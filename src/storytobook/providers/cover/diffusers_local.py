"""Cover art from a local Stable Diffusion model.

Supports a base checkpoint from the Hugging Face hub and, optionally, a LoRA
adapter that is applied on top of it.  The adapter is a *separate* artefact
from the checkpoint, so the base model is always loaded first and the adapter
weights are merged afterwards.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from ...errors import ProviderError, ProviderUnavailableError
from .base import CoverProvider, CoverRequest, CoverResult
from .pillow_fallback import apply_title_overlay
from .theme import build_prompt, detect_genre, negative_prompt

_INSTALL_HINT = "Install it with:  pip install torch diffusers transformers accelerate"


class DiffusersCoverProvider(CoverProvider):
    """Generates artwork with a local diffusion pipeline."""

    name = "diffusers_local"
    label = "Stable Diffusion (local)"
    requirements = "Needs torch + diffusers and a downloaded checkpoint"

    def is_available(self) -> bool:
        if importlib.util.find_spec("torch") is None:
            return False
        if importlib.util.find_spec("diffusers") is None:
            return False
        return bool(getattr(self.settings, "cover_base_model", "").strip())

    # ------------------------------------------------------------------ #
    def _device(self):
        import torch  # noqa: PLC0415 - optional dependency

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _dtype(self, device: str):
        import torch  # noqa: PLC0415 - optional dependency

        if device == "cuda":
            return torch.float16
        return torch.float32

    def _load_pipeline(self, progress=None):
        if importlib.util.find_spec("torch") is None or importlib.util.find_spec("diffusers") is None:
            raise ProviderUnavailableError(
                "The diffusion libraries are not installed.", _INSTALL_HINT
            )

        import torch  # noqa: PLC0415 - optional dependency
        from diffusers import (  # noqa: PLC0415 - optional dependency
            DPMSolverMultistepScheduler,
            StableDiffusionPipeline,
        )

        device = self._device()
        dtype = self._dtype(device)
        base_model = (getattr(self.settings, "cover_base_model", "") or "").strip()

        if progress:
            progress(f"Loading '{base_model}' on {device}...")

        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                base_model,
                torch_dtype=dtype,
                safety_checker=None,
                requires_safety_checker=False,
            )
        except Exception as exc:
            raise ProviderError(
                f"Could not load the diffusion model '{base_model}': {exc}",
                "Check the model name in Settings and that you are online for the first download.",
            ) from exc

        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

        lora_path = (getattr(self.settings, "cover_lora_path", "") or "").strip()
        if getattr(self.settings, "cover_use_lora", False) and lora_path:
            self._apply_lora(pipe, lora_path, progress)

        pipe = pipe.to(device)
        if device == "mps":
            pipe.enable_attention_slicing()
        elif device == "cpu":
            pipe.enable_attention_slicing()
            pipe.enable_vae_slicing()
        else:
            try:
                pipe.enable_xformers_memory_efficient_attention()
            except Exception:
                pass

        if device == "cuda" and torch.cuda.get_device_properties(0).total_memory < 8 * 1024**3:
            pipe.enable_model_cpu_offload()

        return pipe, device

    def _apply_lora(self, pipe, lora_path: str, progress=None) -> None:
        """Merge a LoRA adapter into the pipeline."""
        adapter = Path(lora_path).expanduser()
        if not adapter.exists():
            raise ProviderError(
                f"The LoRA adapter folder '{adapter}' does not exist.",
                "Point the setting at the folder that contains adapter_config.json and the .safetensors weights.",
            )
        if progress:
            progress(f"Applying LoRA adapter from {adapter.name}...")

        weights = adapter
        if adapter.is_dir():
            candidates = sorted(adapter.glob("*.safetensors")) + sorted(adapter.glob("*.bin"))
            if candidates:
                weights = candidates[0]
            elif not (adapter / "adapter_config.json").exists():
                raise ProviderError(
                    f"'{adapter}' does not look like a LoRA adapter folder.",
                    "It should contain adapter_config.json and adapter_model.safetensors.",
                )

        try:
            pipe.load_lora_weights(str(weights))
        except Exception as exc:
            raise ProviderError(f"Could not load the LoRA adapter: {exc}") from exc

        try:
            pipe.fuse_lora()
        except Exception:
            # Fusing is an optimisation; the adapter still works without it.
            pass

    # ------------------------------------------------------------------ #
    def generate(self, request: CoverRequest, progress=None) -> CoverResult:
        pipe, device = self._load_pipeline(progress)

        genre, hits = detect_genre(request.story_text)
        prompt = build_prompt(genre, request.title, request.author, request.extra_prompt)

        seed = request.seed
        if seed is not None and seed >= 0:
            import torch  # noqa: PLC0415 - optional dependency

            generator = torch.Generator(device="cpu").manual_seed(seed)
        else:
            generator = None

        if progress:
            progress(f"Painting the cover ({genre})...")

        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt(),
                num_inference_steps=request.steps,
                guidance_scale=request.guidance_scale,
                height=request.height,
                width=request.width,
                generator=generator,
            )
            image = result.images[0]
        except Exception as exc:
            raise ProviderError(f"Image generation failed: {exc}") from exc

        image = apply_title_overlay(image, request.title, request.author)

        output_path = Path(request.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "PNG", dpi=(300, 300))

        return CoverResult(
            path=output_path,
            provider=self.name,
            prompt=prompt,
            genre=genre,
        )
