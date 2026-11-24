"""Standalone node: describe one image as an editable Krea2 / Illustrious prompt.

Uses the same LM Studio helpers as the Writer. The LLM is called from the
node button (HTTP route), not when the workflow runs, so the user can edit
the text before queueing. Execution just outputs the current text and the
image (passthrough or the uploaded file).

Helpers are imported lazily so this module can be loaded while prompt_writer
is still initializing (register_routes used to run before CFG_TYPE existed).
"""
from __future__ import annotations

import hashlib
import time


# Local copies of prompt_writer constants: do not import them at module level.
CFG_TYPE = "LD_LMSTUDIO_CFG"
CATEGORY = "LD/Prompt"
MODE_OPTIONS = ("Krea2 (natural)", "Illustrious (tags)")


# Original user asks for this node (not the Writer's IMAGE_ONLY_* strings).
ASK_KREA2 = (
    "Look at this image and write one complete image-generation prompt in English, "
    "as natural flowing sentences (not a tag list). Cover every person present, "
    "and for each one their appearance, clothing, pose, action and facial expression; "
    "then the setting, the lighting, the camera angle and framing, and the visual style. "
    "Stay factual and specific. Output only the prompt."
)

ASK_ILLUSTRIOUS = (
    "Look at this image and write one complete Illustrious / Danbooru-style tag line "
    "in English, in the required order. Cover every person present, their appearance, "
    "clothing, pose, action and facial expression, the setting, the lighting, "
    "the camera angle and framing, and the style. Output only the tag line."
)


def _pw():
    from . import prompt_writer as pw
    return pw


def describe_image_as_prompt(
    url,
    model,
    mode="Krea2 (natural)",
    filename="",
    subfolder="",
    typ="input",
    image=None,
    temperature=0.4,
    max_tokens=1200,
    seed=0,
    idioma="Español",
    extra_instructions="",
):
    """Vision call: return a full prompt string for the loaded image."""
    pw = _pw()
    pixels = image if pw._has_image(image) else None
    if pixels is None and filename:
        pixels = pw.load_ref_image(filename, subfolder, typ)
    if not pw._has_image(pixels):
        raise RuntimeError(
            "No hay una imagen para describir. Cargá o conectá una foto primero."
            if not pw.is_english(idioma)
            else "There is no image to describe. Load or connect a photo first."
        )

    url = pw._norm_url(url)
    is_illustrious = str(mode or "").lower().startswith("illustrious")
    system = pw.SYS_ILLUSTRIOUS if is_illustrious else pw.SYS_KREA2
    user_ask = ASK_ILLUSTRIOUS if is_illustrious else ASK_KREA2
    extra = str(extra_instructions or "").strip()

    pw.emit_activity(idioma, "connecting")
    model_id = pw.pick_model(url, model)
    model_id = pw.announce_model_use(url, model_id, idioma) or model_id
    vis = pw._model_is_vision(url, model_id)
    if vis is False:
        raise RuntimeError(pw.VISION_REQUIRED)

    pw.emit_activity(idioma, "describing_one")
    t0 = time.perf_counter()
    content = pw._user_content(user_ask, extra, images=[(1, pixels, "todo")])
    raw = pw.chat_complete(
        url,
        model_id,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        min(float(temperature if temperature is not None else 0.4), 0.5),
        max(int(max_tokens or 0), 1200),
        int(seed or 0),
    )
    text = pw.clean_output(raw)
    if is_illustrious:
        positive, _neg = pw.parse_illustrious(text)
        text = positive or text
    if not text:
        raise RuntimeError(
            "El modelo no devolvió un prompt. Si es un modelo con thinking, "
            "desactivá Reasoning/Thinking en LM Studio e intentá de nuevo."
            if not pw.is_english(idioma)
            else "The model did not return a prompt. If it is a thinking model, "
            "turn Reasoning/Thinking off in LM Studio and try again."
        )
    pw.emit_activity(idioma, "described_one", secs=f"{time.perf_counter() - t0:.1f}")
    pw.emit_activity(idioma, "done")
    return text


def _placeholder_image():
    import torch
    return torch.zeros((1, 1, 1, 3), dtype=torch.float32)


def register_describe_prompt_route(inst, web):
    """POST /ld_promptwriter/describe_prompt — used by the node button."""
    pw = _pw()

    async def ld_promptwriter_describe_prompt(request):
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {"ok": False, "message": "Pedido inválido: no pude leer el JSON."},
                status=400,
            )
        if not isinstance(body, dict):
            body = {}
        img = body.get("image") or {}
        if not isinstance(img, dict):
            img = {"filename": img}
        filename = img.get("filename") or img.get("image") or body.get("filename") or ""
        subfolder = img.get("subfolder") or body.get("subfolder") or ""
        typ = img.get("type") or body.get("type") or "input"
        idioma = body.get("idioma", "Español")
        url = body.get("url", pw.DEFAULT_URL)
        model = body.get("model", pw.AUTO_MODEL)
        mode = body.get("mode", "Krea2 (natural)")
        idle_min = body.get("descarga_idle_min", 0)
        raw_unload = body.get("unload_after", True)
        if isinstance(raw_unload, str):
            unload_after = raw_unload.strip().lower() in ("1", "true", "yes", "on")
        else:
            unload_after = bool(raw_unload)
        pw.cancel_idle_unload()
        pw.set_chat_ttl(idle_min)
        try:
            text = describe_image_as_prompt(
                url,
                model,
                mode=mode,
                filename=filename,
                subfolder=subfolder,
                typ=typ,
                temperature=body.get("temperature", 0.4),
                max_tokens=body.get("max_tokens", 1200),
                seed=body.get("seed", 0),
                idioma=idioma,
                extra_instructions=body.get("extra_instructions", ""),
            )
            return web.json_response({"ok": True, "prompt": text})
        except Exception as e:
            pw.emit_activity(idioma, "error", msg=str(e), level="err")
            return web.json_response({"ok": False, "message": str(e)})
        finally:
            # Same timing as Writer generate/modify: unload immediately only
            # if Config "descargar modelo LLM" (unload_after) is on; otherwise
            # start the optional idle timer.
            if unload_after:
                try:
                    pw.emit_activity(idioma, "unloading")
                    pw.unload_models(url, model)
                    pw.emit_activity(idioma, "unloaded")
                except Exception as e:
                    print(f"[LD-PromptWriter] aviso al descargar el modelo: {e}", flush=True)
            else:
                pw.schedule_idle_unload(url, model, idioma, idle_min)

    inst.routes.post("/ld_promptwriter/describe_prompt")(ld_promptwriter_describe_prompt)


class LD_DescribirComoPrompt:
    """Load or connect one image, describe it as a prompt, edit the text, output it."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "config": (
                    CFG_TYPE,
                    {"tooltip": "Salida del nodo LM Studio Config (LD). El botón usa su URL, modelo, modo e idioma."},
                ),
                "mode": (
                    MODE_OPTIONS,
                    {
                        "default": "Krea2 (natural)",
                        "tooltip": "Formato del prompt: prosa natural (Krea2) o tags Danbooru (Illustrious). Con el Config conectado, el botón usa el modo del Config.",
                    },
                ),
                "prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": False,
                        "tooltip": "Prompt editable. El botón Describir como prompt lo rellena; podés corregirlo antes de ejecutar.",
                    },
                ),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Imagen a describir. También podés subirla en la miniatura del nodo."}),
                "archivo": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Archivo de la carpeta input (miniatura del nodo).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("prompt", "image")
    FUNCTION = "export"
    CATEGORY = CATEGORY
    OUTPUT_NODE = False
    DESCRIPTION = (
        "Describe una imagen con el modelo de visión de LM Studio y deja el texto "
        "en un recuadro editable. La salida prompt es ese texto; image es la misma foto. "
        "El botón llama al LLM; al ejecutar el workflow se usa el texto actual, sin volver a describir."
    )

    @classmethod
    def VALIDATE_INPUTS(cls, mode=None, **kwargs):
        pw = _pw()
        pw.sanitize_combo(mode, MODE_OPTIONS, "Krea2 (natural)")
        return True

    @classmethod
    def IS_CHANGED(cls, mode="Krea2 (natural)", prompt="", image=None, archivo="", config=None, **kwargs):
        pw = _pw()
        parts = [
            pw.sanitize_combo(mode, MODE_OPTIONS, "Krea2 (natural)"),
            str(prompt or ""),
            pw.archivo_fingerprint(archivo),
        ]
        try:
            parts.append("" if image is None else pw._image_fingerprint(image))
        except Exception:
            parts.append("img")
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def export(self, mode="Krea2 (natural)", prompt="", config=None, image=None, archivo=""):
        # Do not call the LLM here: the button already wrote the text, and the
        # user may have edited it. Just pass the current box and the image.
        pw = _pw()
        text = str(prompt or "")
        pixels = pw.resolve_slot_image(image, archivo)
        if not pw._has_image(pixels):
            pixels = _placeholder_image()
        return (text, pixels)
