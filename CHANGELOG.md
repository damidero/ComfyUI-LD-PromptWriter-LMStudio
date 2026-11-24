# Changelog

## 1.2.0 — 2026-11-24

### Nuevo nodo
- **Describir como prompt (LD):** carga o conectá una imagen y el modelo de visión escribe un prompt completo, editable, en estilo Krea2 o Illustrious. Botones **Enviar a idea** y **Enviar a prompt** hacia el Writer, con deshacer de un nivel. Respeta `unload_after` del Config.

### Writer
- Botón **✨ Mejorar idea** junto a Generar, con modos **Mejorar** y **Criticar** y casillas que se guardan con el nodo: **Incluir detalle de las fotos** (prendida por defecto), **Incluir LoRAs** (prendida) e **Incluir foto de referencia** (apagada). Deshacer de un nivel. También respeta `unload_after`.
- **Compose:** la idea ya no pisa los ajustes, las personas ni la cámara. El texto se arma en bloques (ajustes obligatorios, notas de referencia, idea del usuario). En 2 pasadas, la pasada 2 usa prompts de refine que revisan el resultado contra esos ajustes.

### Layout
- Tamaños de nodo fijos; el recálculo del alto de **Describir como prompt** y del Writer usa píxeles de layout (no `getBoundingClientRect`), así el zoom del canvas ya no deja una banda vacía ni recorta los botones.

### Notas y docs
- README en inglés y español al día; workflow de ejemplo con el nodo Describir y el layout actual.

## 1.1.3 — 2026-11-17

### Writer
- **Ropa**: la opción *Automático* pasa a llamarse **LoRA** (ropa de los triggers del LoRA; sin triggers decide el LLM). Los workflows con *Automático* se leen como LoRA. Al prender un chip **Ropa** el selector pasa solo a **Foto**; al apagarlos todos vuelve a LoRA (Desnudo nunca cambia solo). Con **Desnudo** y **Foto** los fragmentos de ropa de los triggers se quitan antes de mandarlos y la regla de ropa tiene prioridad máxima.
- **Chips por imagen**: 5 nuevos (Accesorios, Colores, Expresión, Iluminación, Pelo); todos en orden alfabético. Pelo/Expresión/Accesorios de otra imagen se aplican a la persona elegida. Los widgets nuevos `img{N}_{clave}` van al final (los workflows guardados no se corren).
- **Descripciones de imagen atadas a su foto**: cada descripción guarda una huella de la foto y los chips con que se hizo; si cambian (o se saca la foto) se borra y se rehace en el próximo Generar/Encolar. Las descripciones viejas sin huella se rehacen una vez. Botón **✖** por descripción.
- "N° de personas" pasa a llamarse **Participantes**.
- **Limpiar** también vuelve las listas a su valor inicial: Estilo `(como la referencia)`, Cámara automática, Participantes **Auto (decide el LLM)**, Ropa `LoRA`, usar_imagen `todo`.
- Diseño: listas en grilla 2×2 (Estilo | Cámara, Ropa | Participantes) con 4 px de separación; columna derecha: Generar → nota del positivo → nota de los chips → recuadro **Cambios** con **Modificar**. El alto del nodo se vuelve a medir cuando cambia el contenido (el fondo ya no se corta).
- **Triggers de LoRA descriptivos**: solo las palabras clave cortas se fuerzan textuales; una descripción larga del personaje se integra como rasgos en la escena (antes algunos modelos la copiaban y paraban).
- Si el modelo devuelve un prompt demasiado corto, se le pide una vez el prompt completo.
- **Se quita la Vista en español** (no coincidía con el inglés): ya no se muestra ni se llama al traductor. Lo guardado en workflows viejos se ignora; ningún widget se corre.

### Config
- **Pasadas del LLM** (sección debajo de Actividad del LLM): *1 pasada* o *2 pasadas* (una segunda llamada revisa y corrige el prompt; la actividad muestra Pasada 1/2 y 2/2). Vale para todos los Writer conectados. Widget `pasadas` al final del Config (los workflows viejos quedan en 1 pasada); el widget `pasadas` del Writer queda oculto e ignorado solo por compatibilidad.
- **🎲 Seed aleatoria** y el interruptor **Aleatoria en cada generación** (Generar, Modificar y Encolar ponen una seed nueva; se guarda en las propiedades del nodo, apagado por defecto). Mismo estilo nativo del Config.
- Las entradas (imágenes 1–8, triggers, embeddings negativos) se acomodan en 2–3 filas, las conectadas primero (solo en el modo de nodos clásico).
- `max_tokens` por defecto 2048 (antes 600).

### Notas y docs
- La nota *Recomendaciones de modelos* pasa a ser **Configuración** y hay una segunda nota **Especificaciones** (`properties.ld_note = "specs"`); el pack mantiene texto y título en español/inglés. Sección LLM nueva: Qwen3-VL-8B-Instruct abliterated (GGUF Q4_K_M + mmproj) o 4B, Instruct y no Thinking, evitar modelos MTP/razonamiento, modelo fijo en Config.
- README en inglés y español (README.es.md) al día.

## 1.1.2 — 2026-11-17

- **Limpiar** también apaga las selecciones (chips) de las 8 imágenes.
- El recuadro **Actividad del LLM** pasó del Writer al nodo Config, debajo de **Probar conexión**.
- Nuevo desplegable **Ropa** en el Writer (Automático / Foto / Desnudo), al lado de **N° de personas** (ambos en la columna derecha). Se guarda en el widget `modo_ropa` (al final, así los workflows viejos cargan con Automático).
  - Foto: gana la ropa de la imagen con el interruptor Ropa activado (si ninguna lo tiene, actúa como Automático).
  - Automático: decide el LLM; si hay trigger words de LoRA, prefiere la ropa que implican.
  - Desnudo: sin ropa; ignora la ropa de las imágenes y de los LoRA.
- **Imagen base (i2i)**: aviso visible (y en la descripción/tooltip) de que la IA no ve esa imagen; con denoise bajo se conservan su ropa, pose y colores. Para copiar ropa/pose, usar las imágenes del Writer con sus chips.

## 1.1.0 — 2026-11-16

### Writer y Config
- Vista en español al lado derecho del recuadro positivo (misma altura); el negativo queda a todo el ancho debajo. Se oculta en English y el positivo ocupa todo el ancho.
- El recuadro en español es editable: si está “sucio”, antes de Generar, Modificar o encolar se traduce al inglés. Si se edita el inglés a mano, ese texto gana y no se llama al traductor.
- Cola del workflow: se usa el texto **actual** de los recuadros (positivo / negativo / idea), no un prompt anterior en caché.
- Auto-describir: antes de Generar (y de encolar si el positivo está vacío) se describen las imágenes sin descripción al día, respetando solo los interruptores activos. El modelo no se descarga entre esas descripciones y la composición.
- Filtro de aspectos por imagen: si solo está activo Cámara / POV (u otro subconjunto), la descripción y la composición usan **únicamente** esos aspectos e ignoran el resto (fondo, ropa, identidad, acción, etc.). La composición es solo texto (`From Image N use ONLY: …`); no se reenvían las fotos.
- Estilo, N° de personas y Cámara van apilados debajo de la idea.
- `unload_after` sigue encendido por defecto; **Describir** no descarga el modelo.
- Carga de workflows: ya no se asigna `title_mode` en la instancia del nodo (en ComfyUI actual es de solo lectura). El título se oculta a nivel de tipo, con un fallback seguro. Los hooks `onConfigure` / `onNodeCreated` no interrumpen la carga si fallan.

### Otros nodos
- **Guardar imagen (LD):** prefijo + guardado automático, botón 💾 Guardar y vista previa si el automático está apagado.
- **Imagen base i2i (LD):** miniatura, denoise (por defecto 0.6) y Steps Krea2; sin imagen se comporta como texto a imagen (denoise 1.0).
- **Modelo: Krea2 / Illustrious (LD)** y notas es/en del workflow de ejemplo (sin URLs en las notas).

### Ejemplo y publicación
- `example_workflows/LLM Writer Krea2 and Illustrious.json`: flujo Krea2 + Illustrious con Writer, i2i, Guardar, selector de motor y notas. URL de LM Studio `http://127.0.0.1:1234`. Prefijos de salida `Krea2` e `Illustrious`.
- Plantilla del Action del Comfy Registry en `docs/publish_action.yml` (no publica nada sin el secreto `REGISTRY_ACCESS_TOKEN`). Para activarlo, copiarlo a `.github/workflows/publish_action.yml` con un token que tenga alcance `workflow`.

## 1.0.0 — 2026-11-16

Primera publicación del pack: Config + Writer V2, Tamaño, Modelo Krea2 / Illustrious, Embeddings negativos, Guardar imagen, Imagen base i2i, y el Writer clásico por compatibilidad.
