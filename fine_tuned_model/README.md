# LoRA adapter folder

This folder is a placeholder for a LoRA adapter that can be merged on top of a
Stable Diffusion checkpoint.

An adapter is **not** a model. It is a small set of extra weights that nudge an
existing checkpoint towards a particular look. Two artefacts are needed:

| File | Required | Purpose |
|---|---|---|
| `adapter_config.json` | yes | Describes the rank, the target modules and the training setup. |
| `adapter_model.safetensors` | yes | The trained weights themselves. This is the part that changes the image. |

Only `adapter_config.json` is committed here, so the folder is **not** a usable
adapter on its own - there are no weights in it.

## Using an adapter

1. Put a trained adapter (both files) in this folder, or keep it somewhere
   else entirely.
2. In *Settings -> Cover art*, switch the LoRA toggle on and point
   *Adapter folder* at the directory that holds the two files.
3. Set *Diffusion model* to the base checkpoint the adapter was trained for.
   The default is `stable-diffusion-v1-5/stable-diffusion-v1-5`.

The application loads the base checkpoint first and then merges the adapter
with `pipe.load_lora_weights(...)`, fusing it when the installed `diffusers`
version supports that. The model weights are not tracked by git, so keep them
out of the repository.
