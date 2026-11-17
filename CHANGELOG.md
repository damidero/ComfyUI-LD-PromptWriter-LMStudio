# Changelog

## 1.1.3 — 2026-11-17

- **Vista en español**: ahora es una traducción aparte del prompt inglés **final** (después de agregar los triggers de LoRA), con tokens suficientes según el largo. Antes el LLM la escribía en la misma respuesta que el inglés: no incluía lo que se agregaba después (triggers faltantes), compartía el límite de tokens y se resumía o cortaba. Lo mismo al usar **Modificar**.
- **Ropa**: la opción *Automático* pasa a llamarse **LoRA** (usa la ropa de los triggers del LoRA; sin triggers decide el LLM). Los workflows con *Automático* se leen como LoRA.
  - Al prender un chip **Ropa** en una imagen, el selector pasa solo a **Foto**; al apagar todos vuelve a **LoRA** (Desnudo nunca se cambia solo). **Limpiar** también lo devuelve a LoRA.
  - **Desnudo** y **Foto** (con imagen con Ropa): los fragmentos de ropa de los triggers del LoRA se quitan antes de mandarlos (ya no se fuerzan textuales ni se vuelven a agregar al encolar) y la regla de ropa tiene prioridad máxima.
- Writer: el título **Vista en español ⓘ** explica (al pasar el mouse) cómo se genera y se edita la vista en español.
- Config: `max_tokens` por defecto 1200 (antes 600). La traducción español→inglés también usa tokens suficientes.

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
