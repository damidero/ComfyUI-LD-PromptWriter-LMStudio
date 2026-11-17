# LM Studio Prompt Writer (LD)

ComfyUI nodes that connect to a local **LM Studio** server and turn an idea (or up to eight reference images) into a ready-to-use image prompt.

Two nodes work together:

1. **LM Studio Config (LD):** URL, model (dropdown), Krea2 / Illustrious mode, temperature, tokens, seed, `unload_after` (on by default) and extra instructions. Includes **🔄 Refresh models** and **Test connection**. The references (`image_1`…`image_8`), `lora_triggers` and, in Illustrious, `neg_embeddings` connect here. Outputs are `config` (a single wire to the Writer), **positive** and **negative**.
2. **LM Studio Prompt Writer (LD):** the idea, the **✍️ Generate prompt** button, **✏️ Modify** and the editable boxes (English positive and, when the language is Spanish, a Spanish view on the right). It has a single visible input: `config`. **Output style**, **Number of people** and **Camera** are stacked under the idea. Each image has toggles: *Action*, *Pose*, *Person*, *Clothing*, *Background*, *Style* and *Camera / POV*. If none is on, everything except the camera is used (the Camera dropdown or the LLM decides that). If you enable only some (for example only Camera / POV), the Writer describes and composes **only** those aspects and ignores the rest (background, clothing, identity, action, etc.). The **output style** combo (for example *Realistic / photo*) ignores the art style of the references and writes the prompt in that style. If the positive box has text, running the workflow uses that text (whatever is in the box at that moment) and the LLM is not called. Old workflows that still connect images or outputs to the Writer keep working.

## How to use

1. Open **LM Studio**, start the local server and, if you are going to use images, load a **vision** model.
2. Connect the `config` output of **Config** to the Writer's only input.
3. Write an idea and/or load up to 8 references (thumbnails in the Writer, or *LoadImage* into `image_1`…`image_8` on **Config**). In each column choose Action, Pose, Person, Clothing, Background, Style and/or Camera.
4. If you use **Lora Loader (LoraManager)**, connect its `trigger_words` output to `lora_triggers` on **Config**. The Writer asks the LLM to include them verbatim (at the start in Krea2, as tags in Illustrious) and adds them on run if they are missing.
5. Press **✍️ Generate prompt**, review the text and then run the workflow. For a small change (for example hair color) type the request in **Changes** and press **✏️ Modify**: the LLM applies only that and leaves the rest as is. **Modify** unloads the model when done if `unload_after` is on (same as Generate).
6. Connect the **positive** and **negative** outputs of **Config** to *CLIP Text Encode* (in Illustrious, **negative** can already include the embeddings if `neg_embeddings` is connected).

If the idea is empty but there are images, the Writer asks the model to describe the references (respecting what to take from each one) and builds the prompt. With both an idea and images, it uses both. With neither, it warns you to write an idea or connect an image.

If the model has no vision and you send an image, it warns you to pick a model marked (vision) in LM Studio.

`(auto: loaded)` uses the model already in memory. If you pick one that is not loaded, LM Studio loads it when generating. `unload_after` is **on by default** and unloads the model after **Generate** or after running the workflow; **Describe does not unload**, so the same instance is reused. In Config, `descarga_idle_min` (0 = off) can unload it after N idle minutes. Requests reuse the loaded model (`ttl: -1`, no expiry).

The old all-in-one **LM Studio Prompt Writer (LD) (old)** node is kept for compatibility with earlier workflows.

## Requirements

- LM Studio with the local server running.
- This pack installs no extra Python packages.

## Troubleshooting

- *LM Studio does not respond at …*: start the local server in LM Studio.
- *No chat model loaded*: load a model and try again.
- If the model "thinks" and never returns the prompt, turn off Reasoning / Thinking in LM Studio.

## Images in the Writer

The 8 references are shown in the Writer in two rows of 4, with a thumbnail under each column's toggles. Click or drag a file to upload, 📂 to pick one from the `input` folder, and ✖ to remove it. The *LoadImage* inputs are on the **Config** node (`image_1`…`image_8`); a connected input wins over the column's file. **Describe**, **Generate** and **Modify** read those images even when they are connected to Config.

**🔄 Describe** asks for a description **limited to that image's active toggles** (if none, everything except the camera). The description stays in the compact box (~60 px, scrollable) and is reused when generating if it is still current (if you changed the toggles, it is described again). **Describe does not unload** the model, so it is reused in the next step.

Before **✍️ Generate** (and before queueing the workflow if the positive box is empty), the Writer **auto-describes** loaded images that have no up-to-date description. The model is not unloaded between those descriptions and the final composition. The composition is text only: the photos are never re-sent to the LLM in that call; it is told *From Image N use ONLY: …* with the active aspects.

If an image has no active toggles, all aspects are used (*all*, without camera). If **output style** is not *(as the reference)*, that style wins over the "style" toggle.

## How the prompt is chosen

There is no separate "manual prompt" path anymore. If the **positive** box has text (typed or generated earlier), running the workflow uses **the current text in the box** (not a cached older version) and the LLM is not called. If it is empty, missing references are auto-described and a prompt is generated. LoRA trigger words are prepended if missing.

## Spanish view

With the language selector on **Español**, a Spanish box of the same height appears to the right of the positive box (always English, which is what is used to generate). The **negative** box sits below at full width. In **English** the Spanish view is hidden and the positive box takes the full width.

The Spanish box is **editable**. If you edit it after the last sync, pressing Generate or Modify, or queueing the workflow, translates it to English and uses that translation. If you edit the English box by hand, English wins and the translator is not called. **🧹 Clear** also empties the Spanish view.

## Size (LD)

The node shows, in this order: (1) the aspect ratio dropdown, (2) the megapixel (quality) selector and (3) below it, centered, the approximate pixel size (for example `≈ 864 × 1248 px`), updated live. Values are rounded to multiples of 16. The default 2:3 at 1.08 MP is 864×1248. More ratios are available (9:21, 1:2, 2:1, 3:5, 5:3, etc.) plus a switch to flip portrait/landscape.

## Krea2 and Illustrious

The **Model: Krea2 / Illustrious (LD)** node switches the LLM mode and mutes the nodes of the branch that is not in use.

For **Illustrious**, the checkpoint (`waiIllustriousSDXL_v170.safetensors`, or the more realistic alternative `illustriousRealism_ilXL10V40.safetensors`) must be in `ComfyUI/models/checkpoints` and selected in the Load Checkpoint node. CLIP and VAE are included in the checkpoint; there is no need to load them separately.

In the Writer, **Number of people** (1 to 8, Auto or Custom) sets how many distinct people the prompt should describe. The **language** selector (Español / English) sits above the model selector and changes the interface and the language of the image descriptions; the final prompt is always English.

The **Camera** dropdown (under the idea, below Style and People) chooses the framing. If an image has the Camera / POV toggle on, that reference wins; otherwise the dropdown is used; on Automatic, the LLM decides.

Under **Generate** there is a read-only **LLM activity** box with a live step-by-step log (connection, model load or reuse, each image description, timings, composition, unload and errors). **🧹 Clear** also empties that log.

Recommended LLM in LM Studio: **qwen_qwen3-vl-8b-instruct** (Qwen3-VL 8B Instruct, with vision, needed to describe images). Start LM Studio's local server (Developer / Local Server tab) and use that URL in the Config node.

Krea2 models used in the example workflow: UNET `Krea2-Turbo-HD-V1-int8_convrot`, CLIP `qwen3vl_4b_fp8_scaled` (krea2 type) and VAE `qwen_image_vae`.

The **Negative embeddings (LD)** node (Illustrious branch, below the Lora Loader) lists the files in `ComfyUI/models/embeddings`. Pick one, an optional weight and press ➕ Add; its output connects to `neg_embeddings` on Config and is appended to the **negative**. The **Model: Krea2 / Illustrious** selector mutes it along with the rest of that branch.

The **Model: Krea2 / Illustrious (LD)** selector uses two mutually exclusive switches (turning one on turns the other off). Above them is the **language** for the interface, descriptions and notes. A single **Lora Loader** serves both branches (the selector passes on the active MODEL/CLIP). Krea2 LoRAs do not work in Illustrious and vice versa: change them when you switch engines.

In the Writer, the **Settings** and **Images** sections can be collapsed (▸/▾) and the node shrinks to fit its content, with no empty space below the last row. **Number of people** goes from 1 to 8, plus **Auto (LLM decides)** and **Custom** (any number). You do not need one image per person: the LLM invents any missing participants.

## Save Image (LD)

Replaces Comfy's *SaveImage* on the Krea2 and Illustrious outputs. Inputs: the image, a filename prefix and **auto save** (on by default). When on, running the workflow saves the image to `output` with that prefix. When off, only a preview is kept in `temp` (nothing goes to `output`). **💾 Save** copies the current preview to `output` with the same prefix, even when auto save is off. The `images` output is kept for nodes that listen to it (for example PlaySound).

## Base Image i2i (LD)

Sits below Config. It has a thumbnail (click or drag to upload, ✖ to remove) and a **denoise** value (0.6 by default).

- No image: uses the empty latent from **Size (LD)** for the active branch and outputs denoise 1.0 (text to image, as before).
- With an image: crops and rescales the photo to the Size dimensions, encodes it with the active branch's VAE (the Krea2 VAE or the Illustrious checkpoint's) and outputs that latent plus the denoise.

The denoise goes to the Illustrious *KSampler*. In Krea2 (*KSamplerAdvanced*, which has no denoise) it is converted to `start_at_step = round(steps × (1 − denoise))`. The **Krea2 steps** field must match the Krea2 sampler's steps (8 in the example workflow). The unused branch's VAE is not evaluated (lazy inputs).

## Example workflow

`example_workflows/LLM Writer Krea2 and Illustrious.json` builds a Krea2 / Illustrious flow with this pack.

### Required nodes

- This pack: [ComfyUI-LD-PromptWriter-LMStudio](https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio)
- [ComfyUI-Lora-Manager](https://github.com/willmiao/ComfyUI-Lora-Manager) (Lora Loader)
- [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts) (PlaySound, optional)
- The rest of the nodes in the example are ComfyUI core: UNETLoader, CLIPLoader, VAELoader, CheckpointLoader, CLIPTextEncode, KSampler, VAEDecode, etc.

Installation: search for **LD PromptWriter** in **ComfyUI Manager**, use *Install via Git URL* with this repo's link, or:

```
cd ComfyUI/custom_nodes
git clone https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio
git clone https://github.com/willmiao/ComfyUI-Lora-Manager
git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts
```

Then restart ComfyUI.

### Models (download)

- Krea2 UNET HD int8 (`Krea2-Turbo-HD-V1-int8_convrot.safetensors`): [wikeeyang/Krea2-Turbo-HD-V1](https://huggingface.co/wikeeyang/Krea2-Turbo-HD-V1)
- Krea2 CLIP (`qwen3vl_4b_fp8_scaled.safetensors`) and VAE (`qwen_image_vae.safetensors`): [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2)
- Illustrious WAI v17 (`waiIllustriousSDXL_v170.safetensors`): [Civitai](https://civitai.com/models/827184/wai-illustrious-sdxl) · [Hugging Face mirror](https://huggingface.co/LyliaEngine/waiIllustriousSDXL_v170)
- Realistic alternative (`illustriousRealism_ilXL10V40.safetensors`): [Civitai — Illustrious Realism](https://civitai.com/models/2354628/illustrious-realism)
- [LM Studio](https://lmstudio.ai) and the vision LLM [Qwen3-VL 8B Instruct](https://lmstudio.ai/models/qwen/qwen3-vl-8b)
