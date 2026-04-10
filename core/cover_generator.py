import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image, ImageDraw, ImageFont
import os
from config import MODEL_CONFIG, COVERS_DIR

class CoverGenerator:
    def __init__(self, model_path=None):
        self.model_path = model_path or MODEL_CONFIG["default_model_path"]
        self.pipe = None
        self.device = self._detect_device()

    def _detect_device(self):
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def load_model(self):
        print(f"[CoverGen] Loading model on {self.device}...")
        dtype = torch.float16 if self.device == "cuda" and MODEL_CONFIG["use_float16_cuda"] else torch.float32

        self.pipe = StableDiffusionPipeline.from_pretrained(
            self.model_path,
            torch_dtype=dtype,
            safety_checker=None,
            requires_safety_checker=False
        )

        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(self.pipe.scheduler.config)

        if self.device == "mps":
            self.pipe = self.pipe.to("mps")
            self.pipe.enable_attention_slicing() # Mac-friendly optimization
        elif self.device == "cuda":
            self.pipe = self.pipe.to("cuda")
            try:
                self.pipe.enable_xformers_memory_efficient_attention()
            except Exception:
                pass
        else:
            self.pipe = self.pipe.to("cpu")

        print("[CoverGen] Model ready.")

    def _extract_story_theme(self, text):
        text_lower = text.lower()
        themes = {
            "fantasy": ["magic", "dragon", "kingdom", "wizard", "quest"],
            "scifi": ["space", "future", "robot", "starship", "galaxy"],
            "mystery": ["detective", "crime", "secret", "shadow", "clue"],
            "romance": ["love", "heart", "kiss", "passion", "wedding"],
            "horror": ["dark", "fear", "ghost", "blood", "nightmare"],
            "adventure": ["journey", "treasure", "mountain", "ocean", "explore"]
        }
        detected = [genre for genre, keywords in themes.items() if any(kw in text_lower for kw in keywords)]
        return detected[0] if detected else "dramatic"

    def generate(self, story_text, title, author, output_name="cover"):
        if self.pipe is None:
            self.load_model()

        theme = self._extract_story_theme(story_text)
        prompt = (
            f"Professional book cover, {theme} genre, cinematic lighting, "
            f"highly detailed, bestseller style, atmospheric, 8k resolution"
        )
        negative_prompt = "blurry, low quality, distorted, ugly, bad anatomy, watermark, text"

        print("[CoverGen] Generating image...")
        image = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=MODEL_CONFIG["num_inference_steps"],
            guidance_scale=MODEL_CONFIG["guidance_scale"],
            height=MODEL_CONFIG["image_height"],
            width=MODEL_CONFIG["image_width"]
        ).images[0]

        image = self._add_text_overlay(image, title, author)
        output_path = COVERS_DIR / f"{output_name}.png"
        image.save(output_path, "PNG", dpi=(300, 300))
        print(f"[CoverGen] Saved to {output_path}")
        return str(output_path)

    def _add_text_overlay(self, image, title, author):
        draw = ImageDraw.Draw(image)
        w, h = image.size

        try:
            title_font = ImageFont.truetype("arialbd.ttf", 72)
            author_font = ImageFont.truetype("arial.ttf", 48)
        except IOError:
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
                author_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            except IOError:
                title_font = ImageFont.load_default()
                author_font = ImageFont.load_default()

        # Title
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        t_w = title_bbox[2] - title_bbox[0]
        t_x = (w - t_w) // 2
        t_y = h // 12
        draw.text((t_x+2, t_y+2), title, fill="black", font=title_font)
        draw.text((t_x, t_y), title, fill="white", font=title_font)

        # Author
        auth_bbox = draw.textbbox((0, 0), author, font=author_font)
        a_w = auth_bbox[2] - auth_bbox[0]
        a_x = (w - a_w) // 2
        a_y = h - h // 10
        draw.text((a_x+2, a_y+2), author, fill="black", font=author_font)
        draw.text((a_x, a_y), author, fill="white", font=author_font)

        return image