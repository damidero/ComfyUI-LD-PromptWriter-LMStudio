# ComfyUI LD PromptWriter (LM Studio)

**Español** · [English](#english)

Nodos para ComfyUI que usan un modelo local de **LM Studio** para escribir prompts. Convierten una idea (en español o cualquier idioma) en un prompt en inglés natural para **Krea2**, o en tags estilo Danbooru para **Illustrious**. Pueden tomar hasta 4 imágenes de referencia.

## Nodos

- **LM Studio Config (LD)**: URL del servidor, modelo (o "auto: el cargado"), modo (Krea2 / Illustrious), temperatura, tokens, seed, instrucciones extra y `unload_after` (descarga el modelo de la memoria al terminar).
- **LM Studio Prompt Writer (LD)**: el panel principal.
  - Idea + **estilo de salida** (Realista, Cinematográfico, Anime, Manga, 3D, Pixar, Óleo, Acuarela, Cómic, etc.).
  - **4 imágenes de referencia** dentro del nodo: clic o arrastrar para subir, 📂 para elegir de `input`, ✖ para quitar. Las entradas `image_1`…`image_4` son opcionales y, si se conectan, ganan.
  - **Interruptores por imagen**: acción/pose, persona, fondo/escena, estilo, ropa (se pueden combinar). Si no hay ninguno activo, se usa todo. Si el estilo de salida no es "(como la referencia)", gana sobre el interruptor "estilo".
  - **🔄 Describir**: descripción informativa de cada imagen (no se usa al generar).
  - **✍️ Generar prompt** y **🧹 Limpiar**.
  - Si el recuadro positivo tiene texto, al ejecutar se usa tal cual y no se llama al LLM. Si está vacío, se genera.
  - Entrada `lora_triggers`: conectá `trigger_words` del Lora Loader (LoraManager); los triggers se agregan si faltan.
- **Tamaño (LD)**: latent vacío por proporción (1:1, 2:3, 3:2, 3:4, 4:3, 9:16, 16:9, 4:5, 5:4, 21:9, 9:21, 1:2, 2:1, 3:5, 5:3) y megapíxeles (1.0 a 2.0). Redondea a múltiplos de 16 y muestra el tamaño en píxeles.
- **LM Studio Prompt Writer (LD) (viejo)**: nodo combinado anterior, solo para compatibilidad.

## Instalación

```
cd ComfyUI/custom_nodes
git clone https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio
```

Reiniciá ComfyUI. No necesita dependencias extra: usa la librería estándar de Python y lo que ya trae ComfyUI (numpy, Pillow, torch).

## LM Studio

1. Instalá [LM Studio](https://lmstudio.ai) y descargá un modelo. Para usar imágenes tiene que ser un modelo de visión (por ejemplo Qwen3-VL).
2. En la pestaña **Developer**, activá **Start server**. El puerto por defecto es `1234` (`http://127.0.0.1:1234`). Si usás otro puerto, cambiá la URL en el nodo Config.
3. Con **Probar conexión** en el nodo Config se comprueba el servidor.
4. Si el modelo tiene "thinking", conviene desactivarlo (el nodo igual lo pide con `/no_think`).

## Uso

1. Conectá Config → Writer → `CLIP Text Encode` → KSampler.
2. Escribí una idea y/o cargá imágenes, elegí interruptores y estilo, y pulsá **✍️ Generar prompt** (o ejecutá el workflow con el recuadro vacío).
3. Editá el prompt si querés y ejecutá.

## Workflow de ejemplo

`example_workflows/Krea2_con_Writer.json` usa Krea2 (UNETLoader + CLIPLoader tipo `krea2` + VAE `qwen_image_vae`). Además de este pack necesita:

- **Lora Loader (LoraManager)**: [ComfyUI-Lora-Manager](https://github.com/willmiao/ComfyUI-Lora-Manager)
- **PlaySound|pysssss** (aviso de sonido, opcional): [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts)

Los archivos de modelo (`Krea2-Turbo-HD-V1-int8_convrot.safetensors`, `qwen3vl_4b_fp8_scaled.safetensors`, `qwen_image_vae.safetensors`) no están incluidos.

Para ver la vista previa mientras se genera, iniciá ComfyUI con `--preview-method auto`.

---

<a name="english"></a>
# English

ComfyUI nodes that use a local **LM Studio** model to write prompts. They turn an idea (in any language) into a natural English prompt for **Krea2**, or Danbooru-style tags for **Illustrious**, optionally using up to 4 reference images.

## Nodes

- **LM Studio Config (LD)**: server URL, model (or "auto: the loaded one"), mode (Krea2 / Illustrious), temperature, max tokens, seed, extra instructions and `unload_after` (unloads the model from memory when done).
- **LM Studio Prompt Writer (LD)**: the main panel.
  - Idea + **output style** (Realistic, Cinematic, Anime, Manga, 3D, Pixar, Oil, Watercolor, Comic, etc.).
  - **4 reference images** inside the node: click or drag & drop to upload, 📂 to pick from `input`, ✖ to clear. Optional `image_1`…`image_4` inputs win when connected.
  - **Per-image toggles**: action/pose, person, background/scene, style, clothing (combinable). None on means everything is used. A specific output style overrides the image "style" toggle.
  - **🔄 Describe**: informational description of each image (not used for generation).
  - **✍️ Generate prompt** and **🧹 Clear**.
  - If the positive box already has text, execution uses it as-is without calling the LLM; if empty, it generates one.
  - `lora_triggers` input: connect LoraManager's `trigger_words`; missing triggers are added.
- **Tamaño (LD)** (size): empty latent from aspect ratio (1:1 … 21:9, 9:21, 1:2, 2:1, 3:5, 5:3) and megapixels (1.0 to 2.0), snapped to multiples of 16, showing the pixel size.
- **LM Studio Prompt Writer (LD) (viejo)**: legacy combined node, kept for old workflows.

## Install

```
cd ComfyUI/custom_nodes
git clone https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio
```

Restart ComfyUI. No extra dependencies: Python stdlib plus what ComfyUI already ships (numpy, Pillow, torch).

## LM Studio setup

1. Install [LM Studio](https://lmstudio.ai) and download a model. A vision model (e.g. Qwen3-VL) is needed for images.
2. In the **Developer** tab, enable **Start server**. Default port is `1234` (`http://127.0.0.1:1234`); change the URL in the Config node if you use another.
3. Use **Probar conexión** (test connection) in the Config node.
4. Disabling "thinking" for reasoning models is recommended (the node also sends `/no_think`).

## Usage

1. Wire Config → Writer → `CLIP Text Encode` → KSampler.
2. Type an idea and/or load images, pick toggles and style, click **✍️ Generar prompt** (or run the workflow with the box empty).
3. Edit the prompt if you like and run.

## Example workflow

`example_workflows/Krea2_con_Writer.json` uses Krea2 (UNETLoader + CLIPLoader type `krea2` + `qwen_image_vae`). Besides this pack it needs:

- **Lora Loader (LoraManager)**: [ComfyUI-Lora-Manager](https://github.com/willmiao/ComfyUI-Lora-Manager)
- **PlaySound|pysssss** (optional notification sound): [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts)

Model files are not included. For a live sampling preview, start ComfyUI with `--preview-method auto`.

## License

MIT, see [LICENSE](LICENSE).
