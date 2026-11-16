# Changelog

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
