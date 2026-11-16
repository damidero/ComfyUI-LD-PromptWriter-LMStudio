# LM Studio Prompt Writer (LD)

Nodos de ComfyUI que se conectan al servidor local de **LM Studio** y convierten una idea (o hasta ocho imágenes de referencia) en un prompt listo para generar imágenes.

Hay dos nodos que se usan juntos:

1. **LM Studio Config (LD):** URL, modelo (lista desplegable), modo Krea2 / Illustrious, temperatura, tokens, seed, `unload_after` (por defecto encendido) e instrucciones extra. Incluye **🔄 Actualizar modelos** y **Probar conexión**. Acá se conectan las referencias (`image_1`…`image_8`), `lora_triggers` y, en Illustrious, `neg_embeddings`. Las salidas son `config` (un solo cable al Writer), **positive** y **negative**.
2. **LM Studio Prompt Writer (LD):** la idea, el botón **✍️ Generar prompt**, **✏️ Modificar** y los recuadros editables (positivo en inglés y, si el idioma es Español, la vista en español a la derecha). Visualmente tiene un solo conector: la entrada `config`. Debajo de la idea van apilados **Estilo de salida**, **N° de personas** y **Cámara**. En cada imagen hay interruptores: *Acción*, *Pose*, *Persona*, *Ropa*, *Fondo*, *Estilo* y *Cámara / POV*. Si no hay ninguno activo se usan todos excepto la cámara (esa la decide el desplegable Cámara o el LLM). Si solo activás algunos (por ejemplo solo Cámara / POV), el Writer describe y compone **únicamente** esos aspectos e ignora el resto (fondo, ropa, identidad, acción, etc.). El combo **estilo de salida** (por ejemplo *Realista / foto*) ignora el estilo artístico de las referencias y escribe el prompt en ese estilo. Si el recuadro positivo tiene texto, al correr el workflow se usa ese texto (el que está en el recuadro en ese momento) y no se llama al LLM. Los workflows viejos que todavía conectan imágenes o salidas en el Writer siguen funcionando.

## Cómo usarlo

1. Abrí **LM Studio**, activá el servidor local y, si vas a usar una imagen, cargá un modelo de **visión**.
2. Conectá la salida `config` de **Config** a la única entrada del **Writer**.
3. Escribí una idea y/o cargá hasta 8 referencias (miniaturas en el Writer, o *LoadImage* a `image_1`…`image_8` del **Config**). En cada columna elegí Acción, Pose, Persona, Ropa, Fondo, Estilo y/o Cámara.
4. Si usás **Lora Loader (LoraManager)**, conectá su salida `trigger_words` a `lora_triggers` del **Config**. El Writer le pide al LLM que los incluya tal cual (al inicio en Krea2, como tags en Illustrious) y, si faltan, los agrega al ejecutar.
5. Pulsá **✍️ Generar prompt**, revisá el texto y después ejecutá el workflow. Para un cambio puntual (por ejemplo el color de pelo) escribí el pedido en **Cambios** y pulsá **✏️ Modificar**: el LLM aplica solo eso y deja el resto igual. **Modificar** descarga el modelo al terminar si `unload_after` está activo (igual que Generar).
6. Conectá las salidas **positive** y **negative** del **Config** a *CLIP Text Encode* (en Illustrious, **negative** ya puede incluir los embeddings si `neg_embeddings` está conectado).

Si la idea está vacía pero hay una o dos imágenes, el Writer le pide al modelo que describa esa referencia (respetando qué tomar de cada una) y arme el prompt. Si hay idea e imagen, usa las dos. Si no hay ninguna, avisa: `⚠️ Escribí una idea o conectá una imagen`.

Si el modelo no tiene visión y mandás una imagen, avisa: `El modelo elegido no tiene visión: elegí uno marcado (visión) en LM Studio`.

`(auto: el cargado)` usa el modelo que ya está en memoria. Si elegís uno que no está cargado, LM Studio lo carga al generar. `unload_after` viene **encendido por defecto** y descarga el modelo al terminar **Generar** o al ejecutar el workflow; **Describir no descarga**, para reutilizar la misma instancia. En Config, `descarga_idle_min` (0 = off) puede descargarlo tras N minutos sin actividad. Las peticiones reutilizan el modelo ya cargado (`ttl: -1`, sin caducidad).

El nodo **LM Studio Prompt Writer (LD) (viejo)** (todo en uno) se deja por compatibilidad con workflows anteriores.

## Requisitos

- LM Studio con el servidor local encendido.
- Este pack no instala paquetes extra.

## Si algo falla

- *LM Studio no responde en …*: activá el servidor local en LM Studio.
- *No hay un modelo de chat cargado*: cargá un modelo y reintentá.
- Si el modelo “piensa” y no devuelve el prompt, desactivá Reasoning / Thinking en LM Studio.


## Imágenes en el Writer

Las 8 referencias se ven en el Writer, en dos filas de 4: debajo de los interruptores de cada columna hay una miniatura. Clic o arrastrá un archivo para subirlo, 📂 para elegir uno de la carpeta `input`, y ✖ para quitarlo. Los conectores de *LoadImage* están en el nodo **Config** (`image_1`…`image_8`); esa entrada gana sobre el archivo de la columna. Los botones **Describir**, **Generar** y **Modificar** leen esas imágenes aunque estén conectadas al Config.

El botón **🔄 Describir** pide una descripción **restringida a los interruptores activos** de esa imagen (si no hay ninguno, se usan todos excepto la cámara). Esa descripción queda en el recuadro compacto (~60 px, con scroll) y se reutiliza al generar si sigue vigente (si cambiaste los interruptores, se vuelve a describir). **Describir no descarga** el modelo, para reutilizarlo en el siguiente paso.

Antes de **✍️ Generar** (y antes de encolar el workflow si el recuadro positivo está vacío), el Writer **auto-describe** las imágenes cargadas que no tengan una descripción al día. Entre esas descripciones y la composición final el modelo no se descarga. La composición es solo de texto: nunca se reenvían las fotos al LLM en esa llamada; se indica *From Image N use ONLY: …* con los aspectos activos.

Si no hay interruptores activos en una imagen, se usan todos los aspectos (*todo*, sin cámara). Si **estilo de salida** no es *(como la referencia)*, ese estilo gana sobre el interruptor «estilo».

## Cómo se elige el prompt

Ya no hay un camino de «prompt manual» separado. Si el recuadro **positivo** tiene texto (escrito o generado antes), al ejecutar el workflow se usa **el texto actual del recuadro** (no una versión anterior en caché) y no se llama al LLM. Si está vacío, se auto-describen las referencias que falten y se genera. Los trigger words de LoRA se agregan al inicio si faltaban.

## Vista en español

Con el selector de idioma en **Español**, a la derecha del recuadro positivo (siempre en inglés, que es el que se usa para generar) aparece un recuadro en español de la misma altura. El recuadro **negativo** queda debajo, a todo el ancho. En **English** la vista en español se oculta y el positivo ocupa todo el ancho.

El recuadro en español es **editable**. Si lo modificás después de la última sincronización, al pulsar Generar, Modificar o al encolar el workflow se traduce al inglés y se usa esa traducción. Si editás el recuadro en inglés a mano, el inglés gana y no se llama al traductor. **🧹 Limpiar** también vacía la vista en español.

## Tamaño (LD)

El nodo muestra, en este orden: (1) el desplegable de proporción, (2) el selector de megapíxeles (calidad) y (3) debajo, centrado, el tamaño aproximado en píxeles (por ejemplo `≈ 864 × 1248 px`), que se actualiza en vivo. Se redondea a múltiplos de 16. El valor por defecto 2:3 y 1.08 MP equivale a 864×1248. Hay más proporciones (9:21, 1:2, 2:1, 3:5, 5:3, etc.) y un interruptor para invertir retrato/apaisado.


## Krea2 e Illustrious

Hay un nodo **Modelo: Krea2 / Illustrious (LD)** que cambia el modo del LLM y silencia (mute) los nodos de la rama que no se usa.

Para **Illustrious**, el checkpoint (`waiIllustriousSDXL_v170.safetensors`, o la alternativa más realista `illustriousRealism_ilXL10V40.safetensors`) tiene que estar en `ComfyUI/models/checkpoints` y seleccionarse en el nodo Load Checkpoint. El CLIP y el VAE vienen incluidos en el checkpoint; no hace falta cargarlos aparte.

En el Writer, **N° de personas** (1 a 8, Auto o Personalizado) indica cuántas personas distintas debe describir el prompt. El selector **idioma** (Español / English) vive arriba del selector de modelo y cambia la interfaz y el idioma de las descripciones de imagen; el prompt final sigue en inglés.

El desplegable **Cámara** (debajo de la idea, bajo Estilo y Personas) elige el encuadre. Si una imagen tiene el interruptor Cámara / POV, esa referencia gana; si no, se usa el desplegable; si está en Automático, decide el LLM.

Bajo **Generar** hay un recuadro de solo lectura **Actividad del LLM** con el paso a paso en tiempo real (conexión, carga o reutilización del modelo, descripción de cada imagen, tiempos, composición, descarga y errores). **🧹 Limpiar** también vacía ese registro.

LLM recomendado en LM Studio: **qwen_qwen3-vl-8b-instruct** (Qwen3-VL 8B Instruct, con visión, necesario para describir imágenes). Activá el servidor local de LM Studio (pestaña Developer / Local Server) y usá esa URL en el nodo Config.

Modelos Krea2 usados en el workflow de ejemplo: UNET `Krea2-Turbo-HD-V1-int8_convrot`, CLIP `qwen3vl_4b_fp8_scaled` (tipo krea2) y VAE `qwen_image_vae`.

El nodo **Embeddings negativos (LD)** (rama Illustrious, debajo del Lora Loader) lista los archivos de `ComfyUI/models/embeddings`. Elegí uno, un peso opcional y pulsá ➕ Agregar; su salida se conecta a `neg_embeddings` del Config y se agrega al **negative**. Con el selector **Modelo: Krea2 / Illustrious** se silencia igual que el resto de esa rama.

El selector **Modelo: Krea2 / Illustrious (LD)** usa dos interruptores excluyentes (al activar uno se apaga el otro). Arriba está el **idioma** de la interfaz, las descripciones y las notas. Un único **Lora Loader** sirve a las dos ramas (el selector entrega el MODEL/CLIP activo). Los LoRA de Krea2 no sirven en Illustrious y al revés: hay que cambiarlos al cambiar de motor.

En el Writer, las secciones **Ajustes** e **Imágenes** se pueden plegar (▸/▾) y el nodo se achica al contenido, sin espacio vacío debajo de la última fila. **N° de personas** va de 1 a 8, más **Auto (decide el LLM)** y **Personalizado** (cualquier número). No hace falta una imagen por persona: el LLM inventa a los participantes que falten.


## Guardar imagen (LD)

Reemplaza el *SaveImage* de Comfy en las salidas Krea2 e Illustrious. Entradas: la imagen, un prefijo de archivo y **guardado automático** (encendido por defecto). Si está encendido, al ejecutar el workflow la imagen se guarda en `output` con ese prefijo. Si está apagado, solo se muestra una vista previa en `temp` (no queda en `output`). El botón **💾 Guardar** copia la vista actual a `output` con el mismo prefijo, aunque el automático esté apagado. La salida `images` se mantiene para nodos que la escuchan (por ejemplo PlaySound).

## Imagen base i2i (LD)

Va debajo del Config. Tiene una miniatura (clic o arrastre para subir, ✖ para quitar) y un **denoise** (por defecto 0.6).

- Sin imagen: usa el latent vacío de **Tamaño (LD)** de la rama activa y entrega denoise 1.0 (texto a imagen, igual que antes).
- Con imagen: recorta y reescala la foto al tamaño de Tamaño, la encodifica con el VAE de la rama activa (VAE de Krea2 o el del checkpoint Illustrious) y entrega ese latent más el denoise.

El denoise va al *KSampler* de Illustrious. En Krea2 (*KSamplerAdvanced*, que no tiene denoise) se convierte a `start_at_step = round(steps × (1 − denoise))`. El campo **Steps Krea2** tiene que coincidir con los steps del sampler de Krea2 (8 en el workflow de ejemplo). El VAE de la rama que no se usa no se evalúa (entradas lazy).


## Workflow de ejemplo

`example_workflows/LLM Writer Krea2 and Illustrious.json` arma un flujo Krea2 / Illustrious con este pack.

### Nodos necesarios

- Este pack: [ComfyUI-LD-PromptWriter-LMStudio](https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio)
- [ComfyUI-Lora-Manager](https://github.com/willmiao/ComfyUI-Lora-Manager) (Lora Loader)
- [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts) (PlaySound, opcional)
- El resto de los nodos del ejemplo son de ComfyUI (core): UNETLoader, CLIPLoader, VAELoader, CheckpointLoader, CLIPTextEncode, KSampler, VAEDecode, etc.

Instalación: en **ComfyUI Manager** usá *Install via Git URL* y pegá el enlace del repo, o:

```
cd ComfyUI/custom_nodes
git clone https://github.com/damidero/ComfyUI-LD-PromptWriter-LMStudio
git clone https://github.com/willmiao/ComfyUI-Lora-Manager
git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts
```

Después reiniciá ComfyUI.

### Modelos (descarga)

- Krea2 UNET HD int8 (`Krea2-Turbo-HD-V1-int8_convrot.safetensors`): [wikeeyang/Krea2-Turbo-HD-V1](https://huggingface.co/wikeeyang/Krea2-Turbo-HD-V1)
- Krea2 CLIP (`qwen3vl_4b_fp8_scaled.safetensors`) y VAE (`qwen_image_vae.safetensors`): [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2)
- Illustrious WAI v17 (`waiIllustriousSDXL_v170.safetensors`): [Civitai](https://civitai.com/models/827184/wai-illustrious-sdxl) · [espejo Hugging Face](https://huggingface.co/LyliaEngine/waiIllustriousSDXL_v170)
- Alternativa realista (`illustriousRealism_ilXL10V40.safetensors`): [Civitai — Illustrious Realism](https://civitai.com/models/2354628/illustrious-realism)
- [LM Studio](https://lmstudio.ai) y el LLM con visión [Qwen3-VL 8B Instruct](https://lmstudio.ai/models/qwen/qwen3-vl-8b)

## Aparecer en ComfyUI Manager

El camino actual es publicar el pack en el [Comfy Registry](https://registry.comfy.org), que es lo que alimenta la lista del Manager. Ya no hace falta un pull request a `custom-node-list.json` de ComfyUI-Manager (eso quedó como vía heredada).

Este repo ya incluye el `pyproject.toml` (`PublisherId = "damidero"`, `DisplayName = "LD PromptWriter (LM Studio)"`) y la plantilla del Action en `docs/publish_action.yml` (el estándar de Comfy-Org). Todavía **no está publicado**. Para listarlo hace falta:

1. Crear una cuenta de *publisher* en [registry.comfy.org](https://registry.comfy.org) (el id va después del `@` y no se puede cambiar; si no es `damidero`, hay que actualizar `PublisherId` en `pyproject.toml`).
2. Crear una API key de publicación en ese publisher y guardarla.
3. En el repo de GitHub: Settings → Secrets and variables → Actions, crear el secreto `REGISTRY_ACCESS_TOKEN` con esa key.
4. Publicar: `pip install comfy-cli` y `comfy node publish`, o copiar `docs/publish_action.yml` a `.github/workflows/publish_action.yml` y subir el Action (se dispara al cambiar `pyproject.toml` en `main`, o a mano con *workflow_dispatch*). Hace falta un token de GitHub con alcance `workflow` para poder pushear archivos en `.github/workflows/`. Cada versión de `pyproject.toml` se publica una sola vez; para un arreglo hay que subir el número (por ejemplo `1.1.1`).

Hasta que esté en el Registry, cualquiera puede instalarlo con Manager → *Install via Git URL* y el enlace de este repositorio.
