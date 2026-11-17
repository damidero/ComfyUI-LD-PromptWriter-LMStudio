# Changelog

## 1.1.3 — 2026-11-17

- **Vista en español**: ahora es una traducción aparte del prompt inglés **final** (después de agregar los triggers de LoRA), con tokens suficientes según el largo. Antes el LLM la escribía en la misma respuesta que el inglés: no incluía lo que se agregaba después (triggers faltantes), compartía el límite de tokens y se resumía o cortaba. Lo mismo al usar **Modificar**.
- **Ropa**: la opción *Automático* pasa a llamarse **LoRA** (usa la ropa de los triggers del LoRA; sin triggers decide el LLM). Los workflows con *Automático* se leen como LoRA.
  - Al prender un chip **Ropa** en una imagen, el selector pasa solo a **Foto**; al apagar todos vuelve a **LoRA** (Desnudo nunca se cambia solo). **Limpiar** también lo devuelve a LoRA.
  - **Desnudo** y **Foto** (con imagen con Ropa): los fragmentos de ropa de los triggers del LoRA se quitan antes de mandarlos (ya no se fuerzan textuales ni se vuelven a agregar al encolar) y la regla de ropa tiene prioridad máxima.
- Writer: el título **Vista en español ⓘ** explica (al pasar el mouse) cómo se genera la vista en español.
- Notas: la nota *Recomendaciones de modelos* pasa a llamarse **Configuración** (modelos, LoRAs, nodos necesarios) y hay una segunda nota **Especificaciones** (prompt positivo, chips, vista en español, Ropa, imagen i2i, actividad del LLM). El pack mantiene el texto y el título de ambas en español/inglés; la segunda se reconoce por `properties.ld_note = "specs"`.
- **Limpiar** también vuelve las listas del Writer a sus valores por defecto: Estilo `(como la referencia)`, Cámara `(Automático - decide el LLM)`, N° de personas `1` (personalizado 1), Ropa `LoRA`, usar_imagen_1/2 `todo`.
- **Chips por imagen**: 5 nuevos (Accesorios, Colores, Expresión, Iluminación, Pelo) y todos ordenados alfabéticamente. Sin chips ("todo") los incluye. Pelo/Expresión/Accesorios de otra imagen se aplican a la persona elegida. Accesorios va aparte de Ropa y se mantiene con Desnudo. Los widgets nuevos `img{N}_{clave}` van al final, así los workflows guardados no se corren. Las descripciones "todo" guardadas se vuelven a generar una vez (cambió la firma de aspectos).
- **Pasadas** (nuevo, encima de Ropa/Participantes): *1 pasada* (como antes) o *2 pasadas*: en el mismo Generar, una segunda llamada revisa el prompt con todas las especificaciones y lo corrige o mejora; la actividad muestra Pasada 1/2 y 2/2. Widget `pasadas` al final (los workflows viejos quedan en 1 pasada). Limpiar lo vuelve a 1 pasada.
- Si el modelo devuelve un prompt demasiado corto, se le pide una vez el prompt completo (antes podía quedar solo el texto del LoRA).
- **Triggers de LoRA descriptivos**: si el LoRA trae una descripción entera del personaje (no palabras clave cortas), ya no se obliga al LLM a pegarla textual al principio (algunos modelos la copiaban y paraban, y el "prompt" quedaba solo con la descripción de la persona). Ahora solo las palabras clave cortas se fuerzan textuales; la descripción se le da como rasgos del personaje para integrar en la escena completa. El control de "prompt corto" no cuenta el texto copiado del LoRA, así que el reintento sí se dispara en ese caso. El log muestra las palabras propias del prompt.
- **Vista en español solo lectura**: ya no se puede editar ni se traduce de vuelta al inglés; la generación usa siempre el prompt en inglés. Recuerda de qué inglés salió: si el inglés cambia (editado a mano o al encolar), el español viejo se borra y se vuelve a traducir solo (ruta nueva `/ld_promptwriter/view_es`). Al abrir un workflow con un español que no corresponde, se muestra vacío con aviso.
- "N° de personas" pasa a llamarse **Participantes**.
- **Se quita la Vista en español**: ya no se muestra y no se hace la llamada de traducción (seguía sin coincidir con el inglés). El prompt positivo ocupa todo el ancho. Lo guardado de la vista en workflows viejos se ignora; no hay widgets que se corran.
- **Descripciones de imagen atadas a su foto**: cada descripción guarda de qué foto (huella de la imagen) y con qué chips se hizo. Si la foto se cambia o se saca, o cambian los chips, la descripción se borra y con el próximo Generar/Encolar se vuelve a describir; si es la misma foto y los mismos chips, se reutiliza. Las descripciones guardadas antes (sin huella) se rehacen una vez. Antes una descripción vieja podía seguir usándose con otra foto. Botón **✖** en cada descripción para borrarla a mano.
- Config: las entradas (imágenes 1–8, triggers, embeddings negativos) se acomodan en columnas de 2–3 filas en vez de una por fila; las conectadas van primero (a la izquierda). Si no entran con el nombre completo se muestran cortas (img 1, triggers, emb neg). Solo en el modo de nodos clásico (canvas); en el modo Vue no cambia nada.
- Config: debajo de seed, en una sola línea, el interruptor **Aleatoria en cada generación** (prendido: Generar, Modificar y Encolar ponen una seed nueva cada vez; se guarda en las propiedades del nodo, apagado por defecto) y el botón **🎲 Seed aleatoria**. Solo interfaz, sin widgets nuevos. Se dibujan con el mismo estilo nativo que el resto del Config (como Probar conexión), igual que la fila de Pasadas.
- **Pasadas pasa al nodo Config**: sección "Pasadas del LLM" (con explicación) debajo de Actividad del LLM, mismo estilo. Vale para todos los Writer conectados; viaja por el cable config. Widget nuevo `pasadas` al final del Config (los workflows viejos quedan en 1 pasada). El widget `pasadas` del Writer queda oculto e ignorado solo por compatibilidad. Limpiar ya no toca las pasadas (no toca Config).
- Writer: listas en grilla 2×2 en el ancho que tenía Estilo (Estilo | Cámara, abajo Ropa | Participantes). Columna derecha: Generar → nota del positivo → nota de los interruptores → recuadro **Cambios** con **Modificar** abajo.
- Config: `max_tokens` por defecto 2048 (antes 600; máximo 8192). La traducción español→inglés también usa tokens suficientes.

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
