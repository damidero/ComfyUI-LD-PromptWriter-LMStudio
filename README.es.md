# LM Studio Prompt Writer (LD)

[English](README.md)

Nodos de ComfyUI que se conectan a un servidor local de **LM Studio** y convierten una idea (o hasta ocho imágenes de referencia) en un prompt listo para **Krea2** (lenguaje natural) o **Illustrious** (tags estilo Danbooru).

Estos nodos trabajan juntos:

1. **LM Studio Config (LD):** URL, modelo, modo Krea2 / Illustrious, temperatura, `max_tokens`, seed, `unload_after` (prendido por defecto), instrucciones extra y **Pasadas del LLM**. Botones: **🔄 Actualizar modelos**, **Probar conexión**, **🎲 Seed aleatoria** y el interruptor **Aleatoria en cada generación**. Debajo de Probar conexión está la **Actividad del LLM** (registro en vivo: conexión, carga/reuso del modelo, cada descripción, pasadas, tiempos, descarga, errores). Acá se conectan las referencias (`image_1`…`image_8`), `lora_triggers` y, en Illustrious, `neg_embeddings`; las entradas se acomodan en 2–3 filas, las conectadas primero. Salidas: `config` (un solo cable al Writer), **positive** y **negative**.
2. **LM Studio Prompt Writer (LD):** la idea, **✍️ Generar prompt**, **✨ Mejorar idea**, **✏️ Modificar** con su recuadro **Cambios**, **🧹 Limpiar**, los recuadros positivo (inglés) y negativo editables, y las 8 imágenes de referencia. Su única entrada visible es `config`.
3. **Describir como prompt (LD):** cargá o conectá una imagen y el modelo de visión escribe un prompt completo, editable (Krea2 o Illustrious). **Enviar a idea** / **Enviar a prompt** lo copian al Writer, con deshacer de un nivel. Respeta `unload_after` del Config.

## Cómo se usa

1. Abrí **LM Studio**, iniciá el servidor local (pestaña Developer / Local Server) y cargá un modelo **con visión** y su **mmproj** (ver *LLM recomendado*).
2. Poné la URL en **Config**, elegí el modelo (uno fijo, no *auto*) y Krea2 o Illustrious.
3. Escribí una idea y/o cargá imágenes, y prendé los chips de lo que querés tomar de cada una.
4. Apretá **✍️ Generar prompt**, revisá el texto y encolá el workflow.
5. Para un cambio puntual (p. ej. "pelo rojo"), escribilo en **Cambios** y apretá **✏️ Modificar**: solo cambia eso.
6. **✨ Mejorar idea** (junto a Generar) reescribe la idea para que quede más clara (**Mejorar**) o señala problemas y después la mejora (**Criticar**), sin convertirla en el prompt final. Casillas opcionales (se guardan con el nodo): **Incluir detalle de las fotos**, **Incluir LoRAs**, **Incluir foto de referencia**.

Si el recuadro **positivo** tiene texto, al ejecutar se usa tal cual y no se llama al LLM. Borralo para generar otro. Los trigger words de LoRA se agregan si faltan.

## Controles del Writer

- **Listas** (grilla 2×2 debajo de la idea): **Estilo de salida** | **Cámara**, y **Ropa** | **Participantes**.
  - *Estilo de salida*: p. ej. *Realista / foto*; gana sobre el estilo de las referencias.
  - *Cámara*: encuadre; el chip Cámara de una imagen gana sobre la lista; en Automático decide el LLM.
  - *Ropa*: **LoRA** (la ropa de los triggers del LoRA; sin triggers decide el LLM), **Foto** (gana la ropa de la imagen con el chip Ropa; se elige sola al prender un chip Ropa y vuelve a LoRA al apagarlos) o **Desnudo** (sin ropa; ignora la ropa de imágenes y LoRA; nunca cambia sola).
  - *Participantes*: 1–8, **Auto (decide el LLM)** o Personalizado. No hace falta una imagen por persona.
- **✨ Mejorar idea** (junto a **✍️ Generar prompt**): **Mejorar** reescribe la idea más clara y concreta; **Criticar** señala problemas y después la mejora. No escribe el prompt final (para eso está Generar). Casillas, se guardan con el nodo: **Incluir detalle de las fotos** (prendida por defecto), **Incluir LoRAs** (prendida) e **Incluir foto de referencia** (apagada). Deshacer de un nivel. Respeta `unload_after`.
- **🧹 Limpiar** borra idea, prompts, imágenes del Writer, chips y descripciones, y vuelve las listas a su valor inicial (Estilo como la referencia, Cámara y Participantes en automático, Ropa LoRA). No toca Config, los LoRA ni la imagen i2i.

## Imágenes de referencia y chips

Las 8 referencias se ven en dos filas de 4. Clic o arrastrar para subir, 📂 para elegir de `input`, ✖ para sacarla. Un *LoadImage* conectado a `image_N` en **Config** gana sobre el archivo de la columna.

Cada imagen tiene chips: **Accesorios, Acción, Cámara, Colores, Estilo, Expresión, Fondo, Iluminación, Pelo, Persona, Pose, Ropa**. Cada imagen aporta **solo** lo que tiene prendido; sin ningún chip se usa todo menos Cámara.

- Las imágenes con Persona se asignan en orden a las personas.
- Pelo, Expresión o Accesorios de otra imagen se aplican a la persona elegida sin cambiar su identidad.
- Iluminación: solo la luz. Colores: solo la paleta. Accesorios: joyas, anteojos, objetos en la mano (se mantienen con Desnudo).

Antes de **Generar** (y de encolar si el positivo está vacío) se describen las imágenes sin descripción al día, solo con sus chips activos. Cada descripción queda **atada a su foto y a sus chips**: si cambiás o sacás la foto, o cambiás los chips, se borra y se rehace en el próximo Generar; si no cambió nada se reutiliza. El ✖ al lado de cada descripción la borra a mano. **🔄 Describir** describe una imagen cuando quieras (sin descargar el modelo). La composición es solo texto (las fotos no se reenvían).

Si el modelo no tiene visión (sin mmproj) y mandás una imagen, el Writer avisa.

## Pasadas del LLM (Config)

- **1 pasada**: describe las imágenes que hagan falta y escribe el prompt.
- **2 pasadas**: en el mismo Generar, una segunda llamada revisa el prompt con todas las especificaciones (imágenes, chips, ropa, participantes, estilo, cámara, LoRA) y lo corrige o mejora. Más lento. La actividad muestra Pasada 1/2 y 2/2.
- La idea se combina con los ajustes, las personas y la cámara: ya no los pisa. La pasada 2 usa prompts de refine que revisan el resultado contra esos ajustes.
- Si el modelo responde muy corto, se le pide una vez el prompt completo.

Vale para todos los Writer conectados a ese Config.

## Seed (Config)

**🎲 Seed aleatoria** pone una seed nueva una vez. Con **Aleatoria en cada generación** prendido, Generar, Modificar y Encolar usan una seed nueva cada vez (se guarda en las propiedades del nodo; apagado por defecto).

## LLM recomendado

- **Qwen3-VL-8B-Instruct abliterated**, GGUF **Q4_K_M**, más su archivo **mmproj**: [noctrex/Huihui-Qwen3-VL-8B-Instruct-abliterated-GGUF](https://huggingface.co/noctrex/Huihui-Qwen3-VL-8B-Instruct-abliterated-GGUF). Más rápido: [la versión 4B](https://huggingface.co/noctrex/Huihui-Qwen3-VL-4B-Instruct-abliterated-GGUF).
- Sin el **mmproj** el modelo no ve las imágenes.
- Usá **Instruct**, no Thinking. Evitá modelos de razonamiento / MTP: suelen devolver prompts vacíos o cortados.
- En Config elegí un **modelo fijo** en vez de `(auto: el cargado)`.
- `max_tokens`: **2048** (valor por defecto en Config nuevos).

`unload_after` (prendido por defecto) descarga el modelo después de Generar, Modificar, **Mejorar idea**, **Describir como prompt** y ejecutar el workflow, liberando VRAM. El **🔄 Describir** de cada imagen del Writer no descarga. `descarga_idle_min` (0 = apagado) lo descarga tras N minutos sin uso.

## Krea2 e Illustrious

El nodo **Modelo: Krea2 / Illustrious (LD)** tiene dos interruptores excluyentes; cambia el modo del LLM y silencia la rama que no se usa. Arriba está el **idioma** (Español / English) de la interfaz, las descripciones y las notas; el prompt final siempre es en inglés. Un solo **Lora Loader** sirve para las dos ramas. Los LoRA de Krea2 no sirven en Illustrious y al revés (y los de otras bases, como Flux, Qwen-Image, Z-Image o SDXL, fallan en Krea2 con un error de shape).

Para Illustrious, el checkpoint va en `ComfyUI/models/checkpoints` y se elige en Load Checkpoint. **Embeddings negativos (LD)** lista `ComfyUI/models/embeddings`; su salida va a `neg_embeddings` en Config y se suma al negativo.

## Otros nodos

- **Tamaño (LD):** proporción, megapíxeles y tamaño en píxeles en vivo (múltiplos de 16), con giro vertical/horizontal.
- **Guardar imagen (LD):** prefijo y **guardado automático** (prendido por defecto). Apagado: solo vista previa; **💾 Guardar** la copia a `output`.
- **Imagen base i2i (LD):** miniatura (✖ para sacarla), **denoise** (0.6 por defecto) y pasos de Krea2. Sin imagen: texto a imagen (denoise 1). Con imagen: se recorta al Tamaño y se codifica con el VAE de la rama activa. El LLM **no** ve esta imagen; con denoise bajo se conservan su ropa, pose y colores. Subí el denoise a 0.75–0.9 para que gane el prompt, o cargá la misma foto en una imagen del Writer con los chips Ropa / Pose. En Krea2 el denoise se convierte en `start_at_step = round(steps × (1 − denoise))`.

El nodo viejo **LM Studio Prompt Writer (LD) (old)** se mantiene para workflows anteriores.

## Workflow de ejemplo

`example_workflows/LLM Writer Krea2 and Illustrious.json`. Trae dos notas que mantiene el pack, **Configuración** y **Especificaciones**, en el idioma del workflow.

### Nodos necesarios

- Este pack: [ComfyUI-LD-PromptWriter-LMStudio](https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio)
- [ComfyUI-Lora-Manager](https://github.com/willmiao/ComfyUI-Lora-Manager) (Lora Loader; su `trigger_words` va a `lora_triggers` en Config)
- [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts) (PlaySound, opcional)

Instalación: buscá **LD PromptWriter** en ComfyUI Manager, o:

```
cd ComfyUI/custom_nodes
git clone https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio
git clone https://github.com/willmiao/ComfyUI-Lora-Manager
git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts
```

Después reiniciá ComfyUI.

### Modelos

- UNET Krea2 (`Krea2-Turbo-HD-V1-int8_convrot.safetensors`): [wikeeyang/Krea2-Turbo-HD-V1](https://huggingface.co/wikeeyang/Krea2-Turbo-HD-V1)
- CLIP Krea2 (`qwen3vl_4b_fp8_scaled.safetensors`, tipo krea2) y VAE (`qwen_image_vae.safetensors`): [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2)
- Illustrious WAI v17 (`waiIllustriousSDXL_v170.safetensors`): [Civitai](https://civitai.com/models/827184/wai-illustrious-sdxl) — o [Illustrious Realism](https://civitai.com/models/2354628/illustrious-realism)
- [LM Studio](https://lmstudio.ai) + el LLM de arriba.

## Problemas comunes

- *LM Studio no responde*: iniciá el servidor local y revisá la URL en Config.
- *No hay modelo cargado*: cargá uno (o elegí uno fijo en Config).
- Prompts vacíos o muy cortos: usá un modelo Instruct (sin thinking), apagá Reasoning en LM Studio, subí `max_tokens` a 2048 o probá 2 pasadas.
- Ignora las imágenes: el modelo necesita su mmproj (visión).
