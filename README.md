# LM Studio Prompt Writer (LD)

[Español](README.es.md)

ComfyUI nodes that connect to a local **LM Studio** server and turn an idea (or up to eight reference images) into a ready-to-use image prompt for **Krea2** (natural language) or **Illustrious** (Danbooru-style tags).

Two nodes work together:

1. **LM Studio Config (LD):** URL, model, Krea2 / Illustrious mode, temperature, `max_tokens`, seed, `unload_after` (on by default), extra instructions and **LLM passes**. Buttons: **🔄 Refresh models**, **Test connection**, **🎲 Random seed** and a **Random on every run** switch. Below Test connection there is the **LLM activity** log (live step-by-step: connection, model load/reuse, each image description, passes, timings, unload, errors). The references (`image_1`…`image_8`), `lora_triggers` and, in Illustrious, `neg_embeddings` connect here; the inputs are laid out in 2–3 rows, connected ones first. Outputs: `config` (a single wire to the Writer), **positive** and **negative**.
2. **LM Studio Prompt Writer (LD):** the idea, **✍️ Generate prompt**, **✏️ Modify** with its **Changes** box, **🧹 Clear**, the editable positive (English) and negative boxes, and the 8 reference images. Its only visible input is `config`.

## How to use

1. Open **LM Studio**, start the local server (Developer / Local Server tab) and load a **vision** model with its **mmproj** (see *Recommended LLM*).
2. Set the server URL in **Config**, pick the model (a fixed model, not *auto*) and Krea2 or Illustrious.
3. Write an idea and/or load reference images, and turn on the chips for what to take from each one.
4. Press **✍️ Generate prompt**, check the text and queue the workflow.
5. For a small change (e.g. "make the hair red"), type it in **Changes** and press **✏️ Modify**: only that is changed.

If the **positive** box has text, running the workflow uses the current text as is and the LLM is not called. Clear it to generate a new one. LoRA trigger words are added if missing.

## Writer controls

- **Dropdowns** (2×2 grid under the idea): **Output style** | **Camera**, and **Clothing** | **Participants**.
  - *Output style*: e.g. *Realistic / photo*; overrides the art style of the references.
  - *Camera*: framing; the Camera chip of an image wins over it; on Automatic the LLM decides.
  - *Clothing*: **LoRA** (clothing from the LoRA triggers; without triggers the LLM decides), **Photo** (clothing from the image with the Clothing chip wins; picked automatically when you turn a Clothing chip on and back to LoRA when they are all off) or **Nude** (no clothing; ignores clothing from images and LoRAs; never changed automatically).
  - *Participants*: 1–8, **Auto (LLM decides)** or Custom. You don't need one image per person.
- **🧹 Clear** empties the idea, prompts, Writer images, chips and descriptions, and resets the dropdowns (Style as the reference, Camera and Participants automatic, Clothing LoRA). It does not touch Config, the LoRAs or the i2i image.

## Reference images and chips

The 8 references are shown in two rows of 4. Click or drag a file to upload, 📂 to pick one from `input`, ✖ to remove it. A *LoadImage* connected to `image_N` on **Config** wins over the column's file.

Each image has chips (alphabetical in Spanish): **Accessories, Action, Camera, Colors, Style, Expression, Background, Lighting, Hair, Person, Pose, Clothing**. Each image contributes **only** the aspects whose chip is on; with no chip on, everything except Camera is used.

- Images with Person are assigned to the people in order.
- Hair, Expression or Accessories from another image are applied to the chosen person without changing their identity.
- Lighting: only the light. Colors: only the palette. Accessories: jewelry, glasses, held objects (kept with Nude).

Before **Generate** (and before queueing if the positive box is empty) the Writer describes the images that have no up-to-date description, limited to their active chips. Each description is **tied to its photo and chips**: if you change or remove the photo, or change the chips, it is cleared and redone on the next Generate; if nothing changed it is reused. The ✖ next to each description clears it by hand. **🔄 Describe** describes a single image on demand (without unloading the model). The composition call is text only (the photos are not re-sent).

If the model has no vision (no mmproj) and you send an image, the Writer warns you.

## LLM passes (Config)

- **1 pass**: describes the images that need it and writes the prompt.
- **2 passes**: in the same Generate, a second call reviews the prompt against all the settings (images, chips, clothing, participants, style, camera, LoRA) and fixes or improves it. Slower. The activity shows Pass 1/2 and 2/2.
- If the model answers too briefly, it is automatically asked once for the complete prompt.

The setting applies to every Writer connected to that Config.

## Seed (Config)

**🎲 Random seed** sets a new seed once. With **Random on every run** on, Generate, Modify and Queue use a new seed every time (saved in the node properties, off by default).

## Recommended LLM

- **Qwen3-VL-8B-Instruct abliterated**, GGUF **Q4_K_M**, plus its **mmproj** file: [noctrex/Huihui-Qwen3-VL-8B-Instruct-abliterated-GGUF](https://huggingface.co/noctrex/Huihui-Qwen3-VL-8B-Instruct-abliterated-GGUF). Faster alternative: [the 4B version](https://huggingface.co/noctrex/Huihui-Qwen3-VL-4B-Instruct-abliterated-GGUF).
- Without the **mmproj** the model cannot see images.
- Use **Instruct**, not Thinking. Avoid reasoning / MTP models: they often return empty or cut-off prompts.
- Pick a **fixed model** in Config instead of `(auto: el cargado)`.
- `max_tokens`: **2048** (default for new Config nodes).

`unload_after` (on by default) unloads the model after Generate / Modify / running the workflow, freeing VRAM for the image model; Describe does not unload. `descarga_idle_min` (0 = off) unloads after N idle minutes.

## Krea2 and Illustrious

The **Model: Krea2 / Illustrious (LD)** node has two mutually exclusive switches; it changes the LLM mode and mutes the branch not in use. Above them is the **language** (Español / English) for the interface, image descriptions and notes; the final prompt is always English. A single **Lora Loader** serves both branches. Krea2 LoRAs do not work in Illustrious and vice versa (and LoRAs for other bases, e.g. Flux, Qwen-Image, Z-Image, SDXL, fail on Krea2 with a shape error).

For Illustrious, put the checkpoint in `ComfyUI/models/checkpoints` and select it in Load Checkpoint. **Negative embeddings (LD)** lists `ComfyUI/models/embeddings`; its output goes to `neg_embeddings` on Config and is appended to the negative.

## Other nodes

- **Size (LD):** aspect ratio, megapixels and a live pixel preview (multiples of 16), with a portrait/landscape flip.
- **Save Image (LD):** filename prefix and **auto save** (on by default). Off: preview only; **💾 Save** copies the preview to `output`.
- **Base Image i2i (LD):** thumbnail (✖ to remove), **denoise** (0.6 by default) and Krea2 steps. No image: text to image (denoise 1). With an image: cropped to the Size, encoded with the active branch's VAE. The LLM does **not** see this image; at low denoise its clothing, pose and colors stay. Raise denoise to 0.75–0.9 so the prompt wins, or load the same photo in a Writer image with the Clothing / Pose chips. In Krea2 the denoise becomes `start_at_step = round(steps × (1 − denoise))`.

The old all-in-one **LM Studio Prompt Writer (LD) (old)** node is kept for older workflows.

## Example workflow

`example_workflows/LLM Writer Krea2 and Illustrious.json`. It includes two pack-managed notes, **Setup** and **How it works**, whose text follows the workflow language.

### Required nodes

- This pack: [ComfyUI-LD-PromptWriter-LMStudio](https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio)
- [ComfyUI-Lora-Manager](https://github.com/willmiao/ComfyUI-Lora-Manager) (Lora Loader; connect its `trigger_words` to `lora_triggers` on Config)
- [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts) (PlaySound, optional)

Install: search **LD PromptWriter** in ComfyUI Manager, or:

```
cd ComfyUI/custom_nodes
git clone https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio
git clone https://github.com/willmiao/ComfyUI-Lora-Manager
git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts
```

Then restart ComfyUI.

### Models

- Krea2 UNET (`Krea2-Turbo-HD-V1-int8_convrot.safetensors`): [wikeeyang/Krea2-Turbo-HD-V1](https://huggingface.co/wikeeyang/Krea2-Turbo-HD-V1)
- Krea2 CLIP (`qwen3vl_4b_fp8_scaled.safetensors`, type krea2) and VAE (`qwen_image_vae.safetensors`): [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2)
- Illustrious WAI v17 (`waiIllustriousSDXL_v170.safetensors`): [Civitai](https://civitai.com/models/827184/wai-illustrious-sdxl) — or [Illustrious Realism](https://civitai.com/models/2354628/illustrious-realism)
- [LM Studio](https://lmstudio.ai) + the LLM above.

## Troubleshooting

- *LM Studio does not respond*: start the local server and check the URL in Config.
- *No chat model loaded*: load a model (or pick a fixed one in Config).
- Empty or very short prompts: use an Instruct (non-thinking) model, turn off Reasoning in LM Studio, raise `max_tokens` to 2048, or try 2 passes.
- Images ignored: the model needs its mmproj (vision).
