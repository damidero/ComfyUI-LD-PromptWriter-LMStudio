"""LM Studio Prompt Writer (LD): idea -> prompt for Krea2 or Illustrious.

Talks to LM Studio's OpenAI-compatible API (default http://127.0.0.1:1234).
Lists/unloads models the same way H3 Studio does (/api/v0/models and
/api/v1|/api/v0 models/unload). No third-party HTTP libraries: urllib only.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import os
import json
import re
import time
import threading
import urllib.error
import urllib.request

CATEGORY = "LD/Prompt"
NODE_NAME = "LD_LMStudioPromptWriter"
DISPLAY_NAME = "LM Studio Prompt Writer (LD)"
DEFAULT_URL = "http://127.0.0.1:1234"
AUTO_MODEL = "(auto: el cargado)"
VISION_REQUIRED = (
    "El modelo elegido no tiene visión: elegí uno marcado (visión) en LM Studio"
)
MISSING_IDEA_OR_IMAGE = "⚠️ Escribí una idea o elegí una imagen de referencia"
IMAGE_ONLY_KREA2 = (
    "Describe this reference image and write the prompt from it. "
    "Cover subject, appearance, clothing, pose, setting, lighting, camera/lens, and style, "
    "in natural English. Output only the prompt."
)
IMAGE_ONLY_ILLUSTRIOUS = (
    "Describe this reference image and write the prompt from it as comma-separated "
    "Danbooru-style tags in English, in the required order. Output only the tag line."
)
IMAGE_USE_OPTIONS = (
    "todo",
    "acción / pose",
    "persona",
    "fondo / escena",
    "estilo / ropa",
)
IMAGE_USE_DEFAULT = "todo"
IMAGE_USE_HINTS = {
    "camara": (
        "take ONLY the camera and composition: angle (high, low, eye level, top-down, dutch, etc.), "
        "shot type (close-up, medium, cowboy, full body, wide), point of view "
        "(first-person POV, over the shoulder, side view, from behind, selfie), "
        "lens (wide-angle, telephoto, macro) and framing (how the subject is cropped or placed in the frame). "
        "Name the shot geometry only. "
        "Do NOT describe background content, setting, landscape, weather, architecture, objects in the scene, "
        "clothing, subject identity, pose, action or art style."
    ),
    "todo": (
        "take the full scene: subject, appearance, pose, setting and clothing. "
        "Still obey the output-style instructions (the art style of this image may be ignored)."
    ),
    "acción / pose": (
        "take ONLY the action, pose, body position and gesture. Do NOT describe camera angle, shot type, POV or lens. "
        "IGNORE the person's identity (face, hair, body type, skin, ethnicity, age). "
        "IGNORE background and art style."
    ),
    "persona": (
        "take ONLY this person's identity and appearance, described in detail: "
        "gender, apparent age, ethnicity, face shape, eyes (color and shape), eyebrows, nose, mouth, "
        "hair color and hairstyle, body type, skin tone, and any distinctive features "
        "(moles, scars, freckles, tattoos, jewelry). "
        "IGNORE pose, action, composition, background, clothing (unless it is part of identity, like a signature accessory) and art style. "
        "The FINAL prompt MUST use THIS person as the only subject identity. "
        "Do NOT use the face, body, hair or identity from any other image."
    ),
    "fondo / escena": (
        "take ONLY the background, setting, environment, architecture and atmosphere. "
        "IGNORE people, faces, pose and art style."
    ),
    "estilo / ropa": (
        "take ONLY the clothing, outfit, accessories and (unless a different output style was chosen) the visual aesthetic. "
        "IGNORE identity, pose and background."
    ),
}
ESTILO_SALIDA_DEFAULT = "(como la referencia)"
ESTILO_SALIDA_OPTIONS = (
    "(como la referencia)",
    "Realista / foto",
    "Cinematográfico",
    "Anime",
    "Manga B/N",
    "3D / render",
    "Pixar / cartoon 3D",
    "Pintura al óleo",
    "Acuarela",
    "Ilustración digital",
    "Cómic",
    "Fantasía oscura",
)

N_IMAGES = 8
# Widget order matters for saved workflows: LEGACY keys keep their original
# positions; NEW keys (1.1.3) are appended after every other widget.
LEGACY_ASPECT_KEYS = ("accion", "pose", "persona", "ropa", "fondo", "estilo", "camara")
NEW_ASPECT_KEYS = ("accesorios", "colores", "expresion", "iluminacion", "pelo")
ASPECT_KEYS = LEGACY_ASPECT_KEYS + NEW_ASPECT_KEYS
# Implicit "todo" (no toggles) does not include cámara: that has its own dropdown.
TODO_ASPECTS = ("accion", "pose", "persona", "ropa", "fondo", "estilo") + NEW_ASPECT_KEYS
ASPECT_LABELS = {
    "accesorios": "Accesorios",
    "colores": "Colores",
    "expresion": "Expresión",
    "iluminacion": "Iluminación",
    "pelo": "Pelo",
    "accion": "Acción",
    "pose": "Pose",
    "persona": "Persona",
    "fondo": "Fondo / escena",
    "estilo": "Estilo",
    "ropa": "Ropa",
    "camara": "Cámara / POV",
    "todo": "Todo",
}
ASPECT_PROMPTS = {
    "accion": (
        "take ONLY the action: what is happening, the activity, any interaction between subjects, and motion. "
        "Do NOT describe static body pose, limb placement, clothing, identity, background, art style, or camera."
    ),
    "pose": (
        "take ONLY the body pose: body position, arrangement of limbs, hands, posture, and gaze or head direction. "
        "Do NOT describe the activity or what is happening, clothing, identity, background, art style, or camera."
    ),
    "persona": (
        "take ONLY this person's identity and appearance, described in detail: "
        "gender, apparent age, ethnicity, face shape, eyes (color and shape), eyebrows, nose, mouth, "
        "hair color and hairstyle, body type, skin tone, and any distinctive features "
        "(moles, scars, freckles, tattoos). "
        "IGNORE pose, action, composition, background, clothing, and art style. "
        "The FINAL prompt MUST use THIS person as the only subject identity if this is the chosen persona source. "
        "Do NOT use the face, body or identity from any other image "
        "(only hair, facial expression or accessories may come from another image whose aspect is enabled)."
    ),
    "pelo": (
        "take ONLY the hair: hairstyle (cut, length, parting, texture, updo, bangs) and hair color "
        "(including highlights, roots, dye). "
        "Do NOT describe the face, identity, expression, clothing, pose, background, lighting or art style."
    ),
    "expresion": (
        "take ONLY the facial expression and emotion: mouth, eyes, eyebrows, gaze intensity and the mood they convey "
        "(e.g. smiling, serious, surprised, playful, tired). It is independent from identity: "
        "do NOT describe who the person is, face shape, hair, clothing, pose, background or art style."
    ),
    "accesorios": (
        "take ONLY the accessories, separate from clothing: jewelry (earrings, necklaces, rings, bracelets, piercings), "
        "glasses or sunglasses, watches, hair accessories, bags, and objects held in the hands. "
        "Describe each item's type, material and color. "
        "Do NOT describe garments, footwear, identity, pose, background or art style."
    ),
    "colores": (
        "take ONLY the color palette: dominant and accent colors, saturation, contrast between colors, "
        "warm or cool overall tone and color harmony. "
        "Do NOT describe objects, people, clothing items, lighting setup, pose, background content or art medium."
    ),
    "iluminacion": (
        "take ONLY the lighting: time of day, light sources, direction (front, side, back, top, rim), "
        "quality (hard or soft), intensity, shadows and color temperature (warm, cool, neutral, mixed). "
        "Do NOT describe people, clothing, pose, background content, color palette of objects or art medium."
    ),
    "fondo": (
        "take ONLY the background, setting, environment, architecture, weather and atmosphere. "
        "IGNORE people, faces, pose, clothing and art style/medium."
    ),
    "estilo": (
        "take ONLY the artistic style and photographic/pictorial treatment. "
        "Cover: medium (photograph, oil paint, anime, 3D render, watercolor, comic ink, etc.), "
        "rendering or technique, lighting quality and direction, color palette, contrast, "
        "grain or surface texture, and camera/lens look if it is a photo "
        "(if Iluminación or Colores are also requested, leave lighting or palette details to those sections). "
        "Do NOT mention specific clothing items, garments or accessories. "
        "Do NOT describe the person's identity, pose, action, or what objects/places appear in the scene."
    ),
    "ropa": (
        "take ONLY the clothing: each garment, its colors, materials or fabrics, fit (tight, loose, oversized, tailored), "
        "patterns, layers, footwear, belts, hats and gloves. "
        "Jewelry, glasses, watches, bags and held objects belong to Accesorios, not here. "
        "Do NOT describe art style, medium, lighting, color grading or camera. "
        "Do NOT describe the person's face, body, identity, pose, or the background."
    ),
    "camara": (
        "take ONLY the camera: angle (high, low, eye level, top-down, dutch, etc.), "
        "shot type (close-up, medium, cowboy, full body, wide), point of view "
        "(first-person POV, over the shoulder, side view, from behind, selfie), "
        "lens (wide-angle, telephoto, macro) and framing. "
        "Do NOT describe the person's identity, clothing, background content, or art style."
    ),
    "todo": (
        "take the full scene: subject, appearance, pose, setting and clothing. "
        "Still obey the output-style instructions (the art style of this image may be ignored if a different output style was chosen)."
    ),
}
COMBO_TO_ASPECTS = {
    "todo": ["todo"],
    "acción / pose": ["accion", "pose"],
    "accion / pose": ["accion", "pose"],
    "persona": ["persona"],
    "fondo / escena": ["fondo"],
    "estilo / ropa": ["estilo", "ropa"],
    "estilo": ["estilo"],
    "ropa": ["ropa"],
}

_QUALITY_PREFIX = re.compile(
    r"^(?:\s*(?:masterpiece|best quality|amazing quality|very aesthetic|absurdres)\s*,\s*)+",
    re.I,
)
NO_THINK = "/no_think"
_MODEL_LABEL_SUFFIX = re.compile(
    r"\s*\((?:cargado|visi[oó]n|vision)(?:,\s*(?:cargado|visi[oó]n|vision))*\)\s*$",
    re.I,
)
_EXCLUDE_TYPES = {"embedding", "embeddings", "tts", "whisper", "clip", "audio"}

_THINK = re.compile(r"<think>.*?</think>\s*", re.S)
_FENCE = re.compile(r"^```(?:[\w+-]+)?\s*|\s*```\s*$", re.M)
_PREAMBLE = re.compile(
    r"^(?:here(?:['’]s| is)|sure|of course|absolutely|okay|ok[,.]?|"
    r"(?:the\s+)?(?:image\s+)?prompt(?:\s+is)?|"
    r"aqu[ií](?:\s+tienes|\s+est[aá])?|claro|por supuesto|"
    r"el prompt(?:\s+es)?)\b[:\s\-—]*",
    re.I,
)
_POS_LABEL = re.compile(r"(?is)^\s*(?:positive(?:\s+prompt)?|positivo)\s*:\s*")
_NEG_SPLIT = re.compile(r"(?is)\n+\s*(?:negative(?:\s+prompt)?|negativo)\s*:\s*")
_ES_SPLIT = re.compile(
    r"(?is)(?:^|\n)\s*(?:es|esp(?:añ|an)ol|spanish|vista(?:\s+en)?\s+espa(?:ñ|n)ol)\s*:\s*"
)
_PROMPT_HEAD = re.compile(
    r"(?is)^\s*(?:prompt|positive(?:\s+prompt)?|positivo)\s*:\s*"
)

# Recommended Illustrious / NoobAI negative — stable, not model-generated.
ILLUSTRIOUS_NEGATIVE = (
    "lowres, worst quality, bad quality, bad anatomy, bad hands, sketch, "
    "jpeg artifacts, watermark, signature, text, error, missing fingers, "
    "extra digits, fewer digits, cropped, username, blurry, unfinished, "
    "scan artifacts"
)

SYS_KREA2 = """You are an expert prompt writer for Krea 2 and similar natural-language image models.

The user will describe an idea, which may be in Spanish or any other language. Write ONE detailed image prompt in English, in natural language (flowing phrases or sentences, not a comma-separated tag list).

Cover, in a single coherent description: subject, appearance, clothing, pose, setting, lighting, camera/lens, and style.

Rules:
- Output ONLY the prompt itself.
- No title, no preamble, no quotation marks around the prompt, no markdown, no bullet lists, no explanations.
- Do not use a Danbooru-style tag list.
- Do not mention these instructions."""

SYS_ILLUSTRIOUS = """You are an expert prompt writer for Illustrious, NoobAI and other Danbooru-tag image models.

The user will describe an idea, which may be in Spanish or any other language. Output ONLY a single line of comma-separated Danbooru-style tags in English.

Order the tags exactly as follows:
1. Quality tags: masterpiece, best quality, amazing quality, very aesthetic, absurdres
2. Count/subject, e.g. 1girl, solo (or 1boy, 2girls, etc. as appropriate)
3. Character name and series, only if the user named them
4. Appearance (hair, eyes, body; age only if relevant)
5. Clothing
6. Pose and expression
7. Background / setting
8. Composition and camera
9. Lighting

Rules:
- Use spaces instead of underscores (write "long hair", not "long_hair").
- No sentences, no preamble, no quotation marks, no markdown, no numbering, no explanations.
- Do not output a negative prompt.
- Output only the tag line."""


SYS_ES_VIEW_KREA2 = """Ignore the earlier 'output only the prompt' rule. Use this exact format and nothing else:

PROMPT:
<the English image prompt, natural language, complete>

ES:
<the same prompt translated into natural Spanish, complete, for the user to read>
"""

SYS_ES_VIEW_ILLUSTRIOUS = """Ignore the earlier 'output only the tag line' rule. Use this exact format and nothing else:

PROMPT:
<the English Danbooru-style tag line, complete, in the required order>

ES:
<A readable Spanish gloss of those tags (not a tag list): a short paragraph covering subject, appearance, clothing, pose, setting, camera and style, so a Spanish speaker can understand the prompt>
"""

SYS_ES_VIEW_MODIFY = """After the updated English prompt (or Positive:/Negative: blocks), also add a Spanish view for the user, using this exact extra block and no other commentary:

ES:
<Spanish translation or gloss of the UPDATED English prompt/tags>
"""


def _origin(url: str) -> str:
    for prefix in ("/v1/", "/api/"):
        i = url.find(prefix)
        if i != -1:
            return url[:i]
    return url.rstrip("/")


def _norm_url(url: str) -> str:
    u = (url or DEFAULT_URL).strip().rstrip("/")
    if not u:
        u = DEFAULT_URL
    if "://" not in u:
        u = "http://" + u
    return u


def _down_msg(url: str) -> str:
    return f"LM Studio no responde en {url}: abrí LM Studio y activá el servidor local"


def _http_json(method: str, url: str, body=None, timeout: float = 30):
    data = None
    headers = {"Accept": "application/json", "User-Agent": "LD-PromptWriter/1.0"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = ""
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        snippet = (raw or str(e)).strip().replace("\n", " ")[:400]
        raise RuntimeError(f"LM Studio respondió con error {e.code} en {url}: {snippet}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(_down_msg(_origin(url))) from e
    except TimeoutError as e:
        raise RuntimeError(_down_msg(_origin(url))) from e


def _list_lms_models(url: str, timeout: float = 8):
    """LM Studio native catalog: type + state. Falls back to OpenAI /v1/models."""
    try:
        _status, payload = _http_json("GET", url + "/api/v0/models", timeout=timeout)
        data = payload.get("data") or []
        if data:
            return data, "v0"
    except RuntimeError:
        pass
    _status, payload = _http_json("GET", url + "/v1/models", timeout=timeout)
    return payload.get("data") or [], "v1"


def _is_vision(m: dict) -> bool:
    typ = str(m.get("type") or "").lower()
    caps = m.get("capabilities") or m.get("capability") or []
    if isinstance(caps, str):
        caps = [caps]
    return typ in ("vlm", "vision") or any("vision" in str(c).lower() for c in caps)


def _model_label(mid: str, loaded: bool, vision: bool) -> str:
    tags = []
    if loaded:
        tags.append("cargado")
    if vision:
        tags.append("visión")
    return f"{mid} ({', '.join(tags)})" if tags else mid


def strip_model_label(requested: str) -> str:
    return _MODEL_LABEL_SUFFIX.sub("", (requested or "").strip()).strip()


def is_auto_model(requested: str) -> bool:
    s = strip_model_label(requested)
    return s == "" or s == AUTO_MODEL or s.lower() in ("auto", "(auto)")


def catalog_models(url: str, timeout: float = 1.5) -> dict:
    """Downloaded LLM/VLM models. GET only — never loads a model."""
    url = _norm_url(url)
    empty = {
        "ok": False,
        "reachable": False,
        "url": url,
        "auto": AUTO_MODEL,
        "models": [],
        "options": [AUTO_MODEL],
    }
    try:
        data, kind = _list_lms_models(url, timeout=timeout)
    except Exception:
        return empty

    items = []
    if kind == "v0":
        for m in data:
            mid = m.get("id")
            typ = str(m.get("type") or "").lower()
            if not mid or typ in _EXCLUDE_TYPES:
                continue
            if typ and typ not in ("llm", "vlm", "vision"):
                continue
            loaded = m.get("state") == "loaded"
            vision = _is_vision(m)
            items.append({
                "id": mid,
                "loaded": loaded,
                "vision": vision,
                "type": typ or "llm",
                "label": _model_label(mid, loaded, vision),
            })
        items.sort(key=lambda x: (not x["loaded"], x["id"].lower()))
    else:
        for m in data:
            mid = m.get("id")
            typ = str(m.get("type") or "").lower()
            if not mid or typ in _EXCLUDE_TYPES:
                continue
            items.append({
                "id": mid,
                "loaded": False,
                "vision": False,
                "type": typ or "",
                "label": mid,
            })

    return {
        "ok": True,
        "reachable": True,
        "url": url,
        "auto": AUTO_MODEL,
        "models": items,
        "options": [AUTO_MODEL] + [x["id"] for x in items],
    }


def combo_model_choices(timeout: float = 1.5) -> list:
    return catalog_models(DEFAULT_URL, timeout=timeout)["options"]


def pick_model(url: str, requested: str) -> str:
    requested = strip_model_label(requested)
    insts = _v1_instances(url)
    if not is_auto_model(requested):
        # Keep the same key so a already-loaded instance is reused (no JIT reload).
        return requested
    if insts:
        return insts[0][0] or insts[0][1]
    data, kind = _list_lms_models(url)
    if kind == "v0":
        chat = [m for m in data if m.get("type") in ("llm", "vlm") and m.get("id")]
        live = [m for m in chat if m.get("state") == "loaded"]
        chosen = (live or chat)
        if chosen:
            return chosen[0]["id"]
    ids = [m.get("id") for m in data if m.get("id") and str(m.get("type") or "").lower() not in _EXCLUDE_TYPES]
    if ids:
        return ids[0]
    raise RuntimeError(
        "No hay un modelo de chat cargado en LM Studio. "
        "Cargá un modelo y volvé a intentar."
    )


def _loaded_chat_ids(url: str, fallback_id: str = "") -> list[str]:
    try:
        data, kind = _list_lms_models(url)
    except RuntimeError:
        return [fallback_id] if fallback_id else []
    if kind == "v0":
        live = [
            m["id"]
            for m in data
            if m.get("type") in ("llm", "vlm") and m.get("state") == "loaded" and m.get("id")
        ]
        return live or ([fallback_id] if fallback_id else [])
    return [fallback_id] if fallback_id else [m.get("id") for m in data if m.get("id")][:1]


def _v1_instances(url: str) -> list:
    """[(model_key, instance_id)] from LM Studio /api/v1/models (reliable load state)."""
    try:
        _s, payload = _http_json("GET", url + "/api/v1/models", timeout=8)
    except Exception:
        return []
    out = []
    for m in payload.get("models") or []:
        if str(m.get("type") or "").lower() not in ("llm", "vlm"):
            continue
        for inst in m.get("loaded_instances") or []:
            if inst.get("id"):
                out.append((m.get("key") or "", inst["id"]))
    return out


def _lms_cli_unload(model_id: str) -> bool:
    """Last resort: the `lms` CLI that ships with LM Studio."""
    import shutil
    import subprocess
    exe = shutil.which("lms")
    if not exe:
        cand = os.path.join(os.path.expanduser("~"), ".lmstudio", "bin", "lms.exe")
        exe = cand if os.path.isfile(cand) else None
    if not exe:
        return False
    try:
        r = subprocess.run([exe, "unload", model_id], capture_output=True, text=True, timeout=30)
        return r.returncode == 0
    except Exception:
        return False


def unload_models(url: str, model_id: str = "") -> bool:
    """Free VRAM. Tested on LM Studio 0.4: only POST /api/v1/models/unload
    {"instance_id": <loaded instance id>} works; /api/v0/models/unload answers
    200 with an error body, so a bare 200 is not trusted: we re-check the list."""
    url = _norm_url(url)
    mid = strip_model_label(model_id or "")
    insts = _v1_instances(url)
    targets = [iid for key, iid in insts if not mid or is_auto_model(mid) or key == mid or iid == mid or iid.startswith(mid + ":")]
    if not targets and mid and not is_auto_model(mid) and not insts:
        targets = [mid]  # /api/v1 list unavailable: try the key directly
    if not targets:
        print("[LD-PromptWriter] no hay modelo cargado para descargar", flush=True)
        return True
    all_ok = True
    for iid in targets:
        try:
            _http_json("POST", url + "/api/v1/models/unload", {"instance_id": iid}, timeout=30)
        except Exception as e:
            print(f"[LD-PromptWriter] unload v1 falló para {iid}: {e}", flush=True)
        still = any(i == iid for _k, i in _v1_instances(url))
        if still and _lms_cli_unload(iid):
            still = any(i == iid for _k, i in _v1_instances(url))
        if still:
            all_ok = False
            print(f"[LD-PromptWriter] no pude descargar el modelo {iid} (puede quedar en VRAM)", flush=True)
        else:
            print(f"[LD-PromptWriter] modelo descargado de LM Studio: {iid}", flush=True)
    return all_ok


def _no_think(messages: list) -> list:
    """Append /no_think to the last user turn (copy: caller's list is untouched)."""
    out = [dict(m) for m in messages]
    for m in reversed(out):
        if m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, str):
            m["content"] = c.rstrip() + "\n\n" + NO_THINK
        elif isinstance(c, list):
            m["content"] = list(c) + [{"type": "text", "text": NO_THINK}]
        break
    return out


def _chat_body(model: str, messages: list, temperature: float, max_tokens: int, seed: int) -> dict:
    # Reasoning off: /no_think (Qwen) + LM Studio template kwargs, same as H3 Studio.
    body = {
        "model": model,
        "messages": _no_think(messages),
        "temperature": float(temperature),
        "top_p": 0.95,
        "max_tokens": int(max_tokens),
        "seed": int(seed),
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "reasoning_effort": "none",
        "ttl": int(_chat_ttl),
    }
    return body


def strip_think(text: str) -> str:
    text = _THINK.sub("", text or "")
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    if "<think>" in text:
        text = text.split("<think>")[0]
    return text.replace("/no_think", "")


def clean_output(text: str) -> str:
    text = strip_think(text).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:[\w+-]+)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'“”":
        text = text[1:-1].strip()
    lines = text.splitlines()
    while lines:
        first = lines[0].strip()
        if not first:
            lines = lines[1:]
            continue
        m = _PREAMBLE.match(first)
        if not m:
            break
        rest = first[m.end():].strip()
        if rest:
            lines[0] = rest
            break
        lines = lines[1:]
    return "\n".join(lines).strip()


def parse_illustrious(text: str) -> tuple[str, str]:
    text = clean_output(text)
    parts = _NEG_SPLIT.split(text, maxsplit=1)
    if len(parts) == 2:
        pos = _POS_LABEL.sub("", parts[0]).strip()
        neg = parts[1].strip() or ILLUSTRIOUS_NEGATIVE
        return pos, neg
    return _POS_LABEL.sub("", text).strip(), ILLUSTRIOUS_NEGATIVE


def _tensor_to_data_url(image) -> str:
    """ComfyUI IMAGE is [B,H,W,C] float 0-1. Send the first frame as a PNG data URL."""
    try:
        import numpy as np
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(f"No pude convertir la imagen (falta numpy/PIL): {e}") from e

    frame = image[0] if getattr(image, "ndim", 0) == 4 else image
    if hasattr(frame, "cpu"):
        frame = frame.cpu().numpy()
    arr = np.clip(255.0 * frame, 0, 255).astype("uint8")
    img = Image.fromarray(arr)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    # Keep payloads small so a second image is less likely to be dropped.
    max_side = 1024
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / float(max(w, h))
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), getattr(getattr(Image, 'Resampling', Image), 'LANCZOS', Image.BICUBIC))
    if img.mode == "L":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _user_content(idea: str, extra: str, image=None, images=None) -> str | list:
    text = (idea or "").strip()
    extra = (extra or "").strip()
    if extra:
        text = text + "\n\nAdditional instructions:\n" + extra
    if images is None:
        images = [(1, image, None)] if _has_image(image) else []
    image_parts = []
    for item in images:
        idx = item[0]
        tensor = item[1]
        use = item[2] if len(item) > 2 else None
        try:
            data_url = _tensor_to_data_url(tensor)
        except Exception as e:
            print(f"[LD-PromptWriter] no pude adjuntar la imagen {idx}: {e}", flush=True)
            continue
        label = f"IMAGE {idx}"
        if use:
            label += f" ({use})"
        image_parts.append((label, data_url))
    print(f"[LD-PromptWriter] armas el mensaje con {len(image_parts)} imagen(es): " +
          (", ".join(lbl for lbl, _ in image_parts) if image_parts else "ninguna"), flush=True)
    if not image_parts:
        return text
    parts = []
    if text:
        parts.append({"type": "text", "text": text})
    for label, data_url in image_parts:
        parts.append({"type": "text", "text": f"{label}:"})
        parts.append({"type": "image_url", "image_url": {"url": data_url}})
    return parts


def chat_complete(url: str, model: str, messages: list, temperature: float, max_tokens: int, seed: int) -> str:
    body = _chat_body(model, messages, temperature, max_tokens, seed)
    try:
        _status, payload = _http_json(
            "POST", url + "/v1/chat/completions", body, timeout=300
        )
    except RuntimeError as e:
        msg = str(e)
        if "no responde" in msg:
            raise
        # Connection failures already rewritten; keep HTTP errors as-is,
        # but if the host itself is down the helper already used _down_msg.
        raise
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError(
            "El modelo no devolvió un prompt. Si es un modelo con thinking, "
            "desactivá Reasoning/Thinking en LM Studio e intentá de nuevo."
        )
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    # Some thinking models put the visible reply in a sibling field.
    if not str(content).strip():
        for key in ("reasoning_content", "reasoning"):
            if message.get(key):
                break
        else:
            raise RuntimeError(
                "El modelo no devolvió un prompt. Si es un modelo con thinking, "
                "desactivá Reasoning/Thinking en LM Studio e intentá de nuevo."
            )
    return str(content)


def load_ref_image(filename, subfolder="", typ="input"):
    """Load a ComfyUI input/output/temp image as an IMAGE tensor [1,H,W,C] float 0-1."""
    name = (filename or "").strip()
    if not name:
        return None
    if isinstance(name, dict):
        subfolder = name.get("subfolder") or subfolder
        typ = name.get("type") or typ
        name = (name.get("filename") or name.get("image") or "").strip()
        if not name:
            return None
    if subfolder:
        name = f"{str(subfolder).strip().rstrip('/')}/{name.lstrip('/')}"
    typ = str(typ or "input").strip().strip("[]") or "input"
    if name.endswith("[input]") or name.endswith("[output]") or name.endswith("[temp]"):
        annotated = name
    elif typ in ("input", "output", "temp"):
        annotated = f"{name} [{typ}]"
    else:
        annotated = name
    try:
        import folder_paths
        from PIL import Image
        import numpy as np
    except ImportError as e:
        raise RuntimeError(f"No pude leer la imagen de referencia: {e}") from e
    try:
        path = folder_paths.get_annotated_filepath(annotated)
        img = Image.open(path)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")
        arr = np.array(img).astype("float32") / 255.0
        if arr.ndim == 2:
            arr = np.stack([arr, arr, arr], axis=-1)
        try:
            import torch
            return torch.from_numpy(arr)[None, ...]
        except ImportError:
            return arr[None, ...]
    except Exception as e:
        raise RuntimeError(f"No pude leer la imagen de referencia: {e}") from e



def parse_archivo_widget(value):
    """Filename / subfolder / type from the Writer's archivo_imagen_* widget."""
    if value is None:
        return None
    if isinstance(value, dict):
        name = (value.get("filename") or value.get("image") or value.get("name") or "").strip()
        if not name:
            return None
        return {
            "filename": name,
            "subfolder": value.get("subfolder") or "",
            "type": value.get("type") or "input",
        }
    s = str(value).strip()
    if not s:
        return None
    typ = "input"
    m = re.search(r"\s*\[(input|output|temp)\]\s*$", s, re.I)
    if m:
        typ = m.group(1).lower()
        s = s[: m.start()].strip()
    sub = ""
    s = s.replace("\\", "/")
    if "/" in s:
        sub, s = s.rsplit("/", 1)
    return {"filename": s, "subfolder": sub, "type": typ}


def resolve_slot_image(connected, archivo_value):
    """A connected IMAGE input wins; otherwise load the selected input-dir file."""
    if _has_image(connected):
        return connected
    info = parse_archivo_widget(archivo_value)
    if not info:
        return None
    return load_ref_image(info["filename"], info["subfolder"], info["type"])


def archivo_fingerprint(value) -> str:
    info = parse_archivo_widget(value)
    if not info:
        return ""
    try:
        import folder_paths
        name = info["filename"]
        sub = (info.get("subfolder") or "").strip().replace("\\", "/").rstrip("/")
        typ = info.get("type") or "input"
        if sub:
            name = f"{sub}/{name.lstrip('/')}"
        if name.endswith("[input]") or name.endswith("[output]") or name.endswith("[temp]"):
            annotated = name
        else:
            annotated = f"{name} [{typ}]"
        path = folder_paths.get_annotated_filepath(annotated)
        st = os.stat(path)
        return f"{name}:{st.st_mtime_ns}:{st.st_size}"
    except Exception:
        return str(info.get("filename") or "")


def list_input_images():
    """Top-level image files in ComfyUI's input directory."""
    try:
        import folder_paths
        input_dir = folder_paths.get_input_directory()
        if not input_dir or not os.path.isdir(input_dir):
            return []
        raw = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".jfif")
        if hasattr(folder_paths, "filter_files_content_types"):
            try:
                raw = folder_paths.filter_files_content_types(raw, ["image"])
            except Exception:
                raw = [f for f in raw if f.lower().endswith(exts)]
        else:
            raw = [f for f in raw if f.lower().endswith(exts)]
        return [{"filename": f, "subfolder": "", "type": "input"} for f in sorted(raw)]
    except Exception as e:
        print(f"[LD-PromptWriter] no pude listar la carpeta input: {e}", flush=True)
        return []


def _has_image(image) -> bool:
    if image is None:
        return False
    try:
        if hasattr(image, "numel") and int(image.numel()) == 0:
            return False
        shape = getattr(image, "shape", None)
        if shape is not None and any(int(s) == 0 for s in shape):
            return False
    except Exception:
        pass
    return True


def normalize_image_use(value: str) -> str:
    raw = " ".join(str(value or "").strip().lower().split())
    aliases = {
        "todo": "todo",
        "all": "todo",
        "everything": "todo",
        "accion / pose": "acción / pose",
        "acción / pose": "acción / pose",
        "accion/pose": "acción / pose",
        "acción/pose": "acción / pose",
        "pose": "acción / pose",
        "accion": "acción / pose",
        "acción": "acción / pose",
        "persona": "persona",
        "person": "persona",
        "identity": "persona",
        "fondo / escena": "fondo / escena",
        "fondo/escena": "fondo / escena",
        "background": "fondo / escena",
        "escena": "fondo / escena",
        "fondo": "fondo / escena",
        "estilo / ropa": "estilo / ropa",
        "estilo/ropa": "estilo / ropa",
        "style": "estilo / ropa",
        "ropa": "estilo / ropa",
        "estilo": "estilo / ropa",
    }
    if raw in aliases:
        return aliases[raw]
    for key in IMAGE_USE_HINTS:
        if key.lower() == raw:
            return key
    return IMAGE_USE_DEFAULT


def normalize_aspect_list(use) -> list:
    raw = use if isinstance(use, (list, tuple)) else [use]
    out = []
    seen = set()
    for item in raw:
        key = normalize_aspect_key(item)
        if key in ("todo",) or key not in ASPECT_PROMPTS:
            return list(TODO_ASPECTS)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out or list(TODO_ASPECTS)


def aspect_label_list(use) -> str:
    return ", ".join(ASPECT_LABELS.get(k, k) for k in normalize_aspect_list(use))


def other_aspect_labels(use) -> str:
    enabled = set(normalize_aspect_list(use))
    others = [ASPECT_LABELS.get(k, k) for k in ASPECT_KEYS if k not in enabled]
    return ", ".join(others)


def composer_only_rule(index: int, use) -> str:
    labels = aspect_label_list(use)
    others = other_aspect_labels(use)
    extra = f"; ignore everything else (do not use {others})" if others else "; ignore everything else"
    return f"From IMAGE {index} use ONLY: {labels}{extra}."


def image_use_sentence(index: int, use) -> str:
    aspects = normalize_aspect_list(use)
    parts = [composer_only_rule(index, aspects)]
    for key in aspects:
        hint = ASPECT_PROMPTS.get(key, ASPECT_PROMPTS["todo"])
        label = ASPECT_LABELS.get(key, key)
        parts.append(f"{label}: {hint}")
    return " ".join(parts)


def saved_image_description(index: int, kwargs) -> str:
    return str((kwargs or {}).get("desc_imagen_%s" % index) or "").strip()


def aspect_signature(use) -> str:
    return ",".join(sorted(normalize_aspect_list(use)))


def emit_desc_update(index, text, aspects="") -> None:
    """Push an auto-description into the Writer image box (and properties, on the JS side)."""
    payload = {
        "index": int(index),
        "text": str(text or ""),
        "aspects": str(aspects or ""),
    }
    try:
        from server import PromptServer
        inst = getattr(PromptServer, "instance", None)
        if inst is not None:
            inst.send_sync("ld_promptwriter_desc", payload)
    except Exception:
        pass


def normalize_aspect_key(value: str) -> str:
    raw = " ".join(str(value or "").strip().lower().split())
    aliases = {
        "todo": "todo",
        "all": "todo",
        "accion": "accion",
        "acción": "accion",
        "accion / pose": "accion",  # expanded to both in expand_aspect_token
        "acción / pose": "accion",
        "pose": "pose",
        "persona": "persona",
        "person": "persona",
        "fondo": "fondo",
        "fondo / escena": "fondo",
        "escena": "fondo",
        "estilo": "estilo",
        "style": "estilo",
        "ropa": "ropa",
        "clothing": "ropa",
        "accesorios": "accesorios",
        "accessories": "accesorios",
        "colores": "colores",
        "colors": "colores",
        "colours": "colores",
        "color palette": "colores",
        "expresion": "expresion",
        "expresión": "expresion",
        "expression": "expresion",
        "iluminacion": "iluminacion",
        "iluminación": "iluminacion",
        "lighting": "iluminacion",
        "pelo": "pelo",
        "hair": "pelo",
        "camara": "camara",
        "cámara": "camara",
        "cámara / pov": "camara",
        "camera": "camara",
        "estilo / ropa": "estilo",  # handled as two keys elsewhere
    }
    return aliases.get(raw, raw if raw in ASPECT_PROMPTS else "todo")


def aspects_from_combo(combo) -> list:
    raw = " ".join(str(combo or "").strip().lower().split())
    if not raw:
        return ["todo"]
    # exact table
    for k, v in COMBO_TO_ASPECTS.items():
        if k.lower() == raw:
            return list(v)
    key = normalize_aspect_key(raw)
    return [key]


def expand_aspect_token(item) -> list:
    """Map a label or legacy combo to one or more aspect keys."""
    raw = " ".join(str(item or "").strip().lower().split())
    if raw in ("acción / pose", "accion / pose", "accion/pose", "acción/pose"):
        return ["accion", "pose"]
    if raw in ("estilo / ropa", "estilo/ropa"):
        return ["estilo", "ropa"]
    return [normalize_aspect_key(item)]


def resolve_image_aspects(index: int, old_combo=None, **kwargs) -> list:
    """Toggles win if any are on. Else migrate old combo. Else 'todo' (all aspects).

    Backward compat: if the old combined Acción/Pose toggle is on and the new
    `pose` widget was never saved, both Acción and Pose are treated as on.
    """
    prefix = f"img{index}_"
    # Old workflows only had imgN_accion for "acción / pose".
    if (prefix + "pose") not in kwargs and f"image_{index}_pose" not in kwargs:
        if kwargs.get(prefix + "accion") or kwargs.get(f"image_{index}_accion"):
            kwargs = dict(kwargs)
            kwargs[prefix + "pose"] = True
    active = [k for k in ASPECT_KEYS if kwargs.get(prefix + k) or kwargs.get(f"image_{index}_{k}")]
    # also accept aspects list from the HTTP body
    body_list = kwargs.get(f"aspects_{index}") or kwargs.get("aspects", {}).get(str(index)) if isinstance(kwargs.get("aspects"), dict) else kwargs.get(f"aspects_{index}")
    if body_list:
        if isinstance(body_list, str):
            body_list = [x.strip() for x in body_list.split(",") if x.strip()]
        mapped = []
        for item in body_list:
            mapped.extend(expand_aspect_token(item))
        # unique, keep order
        seen = set()
        mapped = [k for k in mapped if not (k in seen or seen.add(k))]
        if mapped:
            return mapped
    if active:
        return active
    if index <= 2 and old_combo:
        return aspects_from_combo(old_combo)
    return ["todo"]


def filter_style_aspect(aspects: list, estilo_salida: str) -> list:
    """If an explicit output style is chosen, it wins over image 'estilo' toggles."""
    estilo = " ".join(str(estilo_salida or "").strip().split()) or ESTILO_SALIDA_DEFAULT
    if estilo == ESTILO_SALIDA_DEFAULT:
        return list(aspects)
    return [a for a in aspects if a != "estilo"]


def collect_ref_images(
    image=None,
    image_1=None,
    image_2=None,
    image_3=None,
    image_4=None,
    usar_imagen_1="todo",
    usar_imagen_2="todo",
    estilo_salida=ESTILO_SALIDA_DEFAULT,
    **kwargs,
):
    """List of (index, tensor, aspects). Legacy `image` is image_1. None toggled = todo."""
    if not _has_image(image_1) and _has_image(image):
        image_1 = image
    named = {1: image_1, 2: image_2, 3: image_3, 4: image_4}
    tensors = {}
    for idx in range(1, N_IMAGES + 1):
        raw = named.get(idx, kwargs.get(f"image_{idx}"))
        tensors[idx] = resolve_slot_image(raw, kwargs.get(f"archivo_imagen_{idx}"))
    combos = {1: usar_imagen_1, 2: usar_imagen_2}
    out = []
    for idx in range(1, N_IMAGES + 1):
        tensor = tensors[idx]
        if not _has_image(tensor):
            continue
        aspects = resolve_image_aspects(idx, combos.get(idx), **kwargs)
        # expand todo
        if aspects == ["todo"] or "todo" in aspects:
            aspects = list(TODO_ASPECTS)
        estilo = " ".join(str(estilo_salida or "").strip().split()) or ESTILO_SALIDA_DEFAULT
        if estilo != ESTILO_SALIDA_DEFAULT:
            aspects = [a for a in aspects if a != "estilo"]
        if not aspects:
            # only estilo was requested and output style wins: skip this image
            print(f"[LD-PromptWriter] IMAGE {idx}: se omite el estilo de la referencia porque gana estilo_salida={estilo!r}", flush=True)
            continue
        out.append((idx, tensor, aspects))
    return out


def normalize_triggers(text) -> list:
    if text is None:
        return []
    if isinstance(text, (list, tuple)):
        parts = [str(p) for p in text]
    else:
        parts = re.split(r",+", str(text))
    seen = set()
    out = []
    for part in parts:
        token = " ".join(part.split()).strip()
        if not token:
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(token)
    return out


_TRIGGER_TAG_MAX_WORDS = 3
_TRIGGER_NOT_TAG_RE = re.compile(r"^(?:no|not|with|and|without)\b", re.IGNORECASE)
# Short fragments made of ordinary visual words are pieces of a description
# ("blonde hair", "lower angle"), not trigger tokens.
_TRIGGER_DESC_WORD_RE = re.compile(
    r"\b(?:hair|haired|eyes?|eyebrows?|brows?|lashes|eyelashes|skin|smile|smiling|lips?|mouth|face|facial|"
    r"nose|cheeks?|teeth|tongue|chin|jaw|ears?|neck|shoulders?|arms?|hands?|legs?|thighs?|feet|body|figure|"
    r"breasts?|chest|waist|hips?|belly|tattoos?|freckles|moles?|scars?|piercings?|makeup|expression|"
    r"blonde?|brunette|redhead|ginger|tan|tanned|pale|curvy|slim|petite|athletic|"
    r"angle|shot|view|close-?up|portrait|framing|focus|lighting|light|lit|background|pose|posing|"
    r"photorealistic|realistic|detailed|quality)\b",
    re.IGNORECASE,
)


def split_trigger_kinds(triggers) -> tuple:
    """Split LoRA trigger fragments into (tags, description).

    Real trigger words are short tokens ("anahi", "ohwx woman") and must be
    pasted verbatim. Many LoRAs (Forge activation text / civitai trainedWords)
    instead carry a whole character DESCRIPTION; forcing that verbatim at the
    start made some models just echo it and stop, so the "prompt" came out as
    a description of the person only. Those long fragments are returned apart
    so the LLM integrates them into the subject instead of copying them.
    """
    tags, desc = [], []
    for t in triggers or []:
        tok = " ".join(str(t).split()).strip()
        if not tok:
            continue
        words = tok.split()
        looks_desc = len(words) > 1 and bool(_TRIGGER_DESC_WORD_RE.search(tok))
        if (len(words) <= _TRIGGER_TAG_MAX_WORDS and "." not in tok.rstrip(".")
                and not _TRIGGER_NOT_TAG_RE.match(tok) and not looks_desc):
            tags.append(tok)
        else:
            desc.append(tok)
    return tags, desc


def triggers_instruction(is_illustrious: bool, triggers: list) -> str:
    if not triggers:
        return ""
    tags, desc = split_trigger_kinds(triggers)
    parts = []
    if tags:
        joined = ", ".join(tags)
        if is_illustrious:
            parts.append(
                "You MUST include these LoRA trigger words verbatim as Danbooru-style tags "
                "(keep their exact spelling) near the start of the tag list, right after the "
                f"quality tags: {joined}"
            )
        else:
            parts.append(
                "You MUST include these LoRA trigger words verbatim at the very start of the prompt, "
                f"in this exact form, then continue with the rest of the description: {joined}"
            )
    if desc:
        text = ", ".join(desc)
        if is_illustrious:
            parts.append(
                "The LoRA also describes the main character's appearance. Convert these traits into "
                "Danbooru-style tags for the main subject (do not copy the sentences), and still write "
                f"the full tag line for the whole scene: {text}"
            )
        else:
            parts.append(
                "The LoRA also describes the main character's appearance (face, hair, skin, body, "
                "marks). Use these traits for the main subject, woven into your own description; do "
                "NOT copy this text as the whole answer and do not stop after it. The prompt must "
                "still describe the full scene: every participant, the action and pose, camera and "
                "framing, setting, lighting and style, following all other instructions. "
                f"Character traits: {text}"
            )
    return "\n".join(parts)


def ensure_triggers(positive: str, triggers: list, is_illustrious: bool) -> str:
    """If the LLM omitted any short trigger word, put the missing ones in verbatim.

    Long descriptive LoRA fragments are not forced (they are traits the LLM
    already merged into the subject description).
    """
    text = str(positive or "")
    tags, _desc = split_trigger_kinds(triggers)
    missing = [t for t in tags if t.lower() not in text.lower()]
    if not missing:
        return text
    prefix = ", ".join(missing)
    if not text.strip():
        return prefix
    if is_illustrious:
        match = _QUALITY_PREFIX.match(text)
        if match:
            return text[: match.end()] + prefix + ", " + text[match.end() :]
        return prefix + ", " + text
    return prefix + ", " + text


_CLOTHING_RE = re.compile(
    r"\b(?:"
    r"(?:crop|tank|tube|halter|bikini|bra|sports\s+bra|strapless|ribbed)\s+tops?|"
    r"t-?shirts?|shirts?|blouses?|dress(?:es)?|skirts?|miniskirts?|jeans|pants|trousers|shorts|leggings|"
    r"bikinis?|swimsuits?|swimwear|lingerie|bras?|brassieres?|panties|underwear|thongs?|briefs|"
    r"stockings|pantyhose|tights|socks|shoes|heels|high\s+heels|boots|sneakers|sandals|"
    r"jackets?|coats?|hoodies?|sweaters?|cardigans?|vests?|corsets?|bodysuits?|leotards?|robes?|"
    r"kimonos?|uniforms?|outfits?|costumes?|clothing|clothes|garments?|apparel|attire|"
    r"wearing|wears|worn|dressed|neckline|cleavage\s+window|sleeves?|sleeveless|collar|"
    r"gloves|hats?|caps?|scarf|scarves|belts?|fabric|denim|lace|satin|silk|latex|leather\s+(?:jacket|pants|skirt)"
    r")\b",
    re.IGNORECASE,
)
_TOP_RE = re.compile(r"\b(?:\w+\s+)?tops?\b", re.IGNORECASE)
_TOP_SAFE_RE = re.compile(r"\b(?:on\s+top|top\s+(?:of|view|down|light|lighting)|from\s+the\s+top)\b", re.IGNORECASE)


def _mentions_clothing(text: str) -> bool:
    t = str(text or "")
    if _CLOTHING_RE.search(t):
        return True
    if _TOP_RE.search(t) and not _TOP_SAFE_RE.search(t):
        return True
    return False


def split_trigger_clothing(triggers: list) -> tuple:
    """Return (kept_triggers, removed_clothing_fragments).

    Trigger text from LoRA Manager can be a whole description ("young woman...
    Tight pink crop top..."). Sentences/fragments that describe clothing are
    removed so they are neither forced verbatim nor re-added by ensure_triggers.
    """
    kept, removed = [], []
    for trig in triggers or []:
        tok = str(trig or "").strip()
        if not tok:
            continue
        sentences = [x.strip() for x in re.split(r"(?<=[.;!?])\s+", tok) if x.strip()]
        keep_s = []
        for sen in sentences:
            if _mentions_clothing(sen):
                removed.append(sen.rstrip(".;"))
            else:
                keep_s.append(sen)
        if keep_s:
            kept.append(" ".join(keep_s).rstrip(" ."))
    return kept, removed


def ropa_image_indices(refs=None, **kwargs) -> list:
    """Images whose clothing should be used (Ropa chip on, or no chip = todo)."""
    out = []
    if refs is not None:
        for idx, _t, aspects in refs:
            asp = aspects if isinstance(aspects, (list, tuple)) else [aspects]
            if "ropa" in asp or "todo" in asp:
                out.append(idx)
        return out
    for idx in range(1, N_IMAGES + 1):
        if not str(kwargs.get(f"archivo_imagen_{idx}") or "").strip() and not _has_image(kwargs.get(f"image_{idx}")):
            continue
        chips = [bool(kwargs.get(f"img{idx}_{k}")) for k in ASPECT_KEYS]
        if kwargs.get(f"img{idx}_ropa") or not any(chips):
            out.append(idx)
    return out


def effective_triggers(triggers: list, modo_ropa, ropa_imgs) -> tuple:
    """(triggers_to_enforce, removed_clothing) according to the Ropa mode."""
    modo = normalize_ropa(modo_ropa)
    if modo == ROPA_DESNUDO or (modo == ROPA_FOTO and ropa_imgs):
        return split_trigger_clothing(triggers)
    return list(triggers or []), []


def _model_is_vision(url: str, model_id: str):
    """True/False if detectable from /api/v0, else None."""
    cat = catalog_models(url, timeout=3.0)
    if not cat.get("reachable"):
        return None
    mid = (model_id or "").strip()
    for m in cat.get("models") or []:
        if m.get("id") == mid:
            return bool(m.get("vision"))
    if not cat.get("models"):
        return None
    # Known catalog but this id was not a VLM/LLM entry with vision.
    # If the catalog came from /api/v0, a missing/non-vlm id is not vision.
    if any("type" in (m or {}) or m.get("vision") for m in cat.get("models") or []):
        # v0 entries have type/vision; id not marked vision => False
        if any(m.get("type") or m.get("vision") is True or m.get("loaded") is not None
               for m in cat["models"]):
            return False
    return None


def _looks_like_no_vision_error(msg: str) -> bool:
    s = (msg or "").lower()
    keys = (
        "does not support image",
        "doesn't support image",
        "images are not supported",
        "image_url",
        "vision is not",
        "not a vision",
        "no vision",
        "not multimodal",
        "multimodal is not",
        "cannot process image",
        "can't process image",
        "image input is not",
        "images not allowed",
        "unsupported content",
        "unexpected image",
        "invalid image",
        "vlm required",
        "only text",
    )
    return any(k in s for k in keys)



def style_instruction(estilo: str, is_illustrious: bool) -> str:
    estilo = " ".join(str(estilo or "").strip().split()) or ESTILO_SALIDA_DEFAULT
    if estilo == ESTILO_SALIDA_DEFAULT or estilo.lower() in ("como la referencia", "referencia", "same"):
        return ""
    # Shared rule: references may be in another medium.
    ignore = (
        "The reference images MAY be in a completely different art style. "
        "You MUST IGNORE their art style (do not copy anime/illustration look unless that is the chosen output style). "
        "Write the prompt in the CHOSEN output style below. "
        "If a reference is anime/stylized and the output style is realistic, convert anime proportions, eyes, hair and features into a real human."
    )
    krea = {
        "Realista / foto": (
            "Output style: a photorealistic photograph of a real human. "
            "Natural skin texture, real anatomy and proportions, real camera and lens (focal length, aperture), "
            "natural or cinematic photographic lighting. "
            "Do NOT use anime, manga, cartoon, illustration, cel-shading or stylized terms."
        ),
        "Cinematográfico": (
            "Output style: a cinematic still from a live-action film. Photoreal people, movie lighting, "
            "anamorphic/cinemascope feel, shallow depth of field, color grading. No anime or cartoon terms."
        ),
        "Anime": (
            "Output style: modern anime still (2D animation). Clean linework, anime proportions and eyes, cel shading, "
            "no photoreal skin pores or real-camera lens talk."
        ),
        "Manga B/N": (
            "Output style: black-and-white manga panel. Screentones, ink lines, manga framing, no color, no photorealism."
        ),
        "3D / render": (
            "Output style: high-end 3D render (Octane/Unreal/Blender look). Crisp CGI materials and lighting, not a photo and not 2D anime."
        ),
        "Pixar / cartoon 3D": (
            "Output style: Pixar-like stylized 3D cartoon. Appealing stylized anatomy, subsurface skin, cinematic 3D lighting, not photoreal and not 2D anime."
        ),
        "Pintura al óleo": (
            "Output style: oil painting. Visible brushwork, canvas texture, painterly color, classical composition. Not a photo, not anime."
        ),
        "Acuarela": (
            "Output style: watercolor painting. Soft pigment blooms, paper texture, translucent washes. Not a photo, not digital-hard edges."
        ),
        "Ilustración digital": (
            "Output style: polished digital illustration. Designed lighting, clean rendering, illustration (not a photograph, not anime unless features demand it)."
        ),
        "Cómic": (
            "Output style: Western comic-book art. Bold inks, halftone or flat colors, dynamic comic panel feel. Not photoreal, not manga."
        ),
        "Fantasía oscura": (
            "Output style: dark fantasy illustration. Moody chiaroscuro, rich shadows, grim atmosphere, painterly or cinematic fantasy look."
        ),
    }
    illu = {
        "Realista / foto": (
            "Output style tags must include: realistic, photorealistic, real life, realistic skin texture, natural lighting. "
            "Do NOT use: anime, manga, chibi, cel shading, stylized. Convert anime-like faces and proportions into realistic ones."
        ),
        "Cinematográfico": (
            "Output style tags: cinematic lighting, film still, photorealistic, depth of field, cinematography. No anime or cartoon tags."
        ),
        "Anime": (
            "Output style tags: anime, anime style, official art, or similar 2D anime tags. Avoid realistic, photorealistic, 3d."
        ),
        "Manga B/N": (
            "Output style tags: manga, monochrome, greyscale, screentone, lineart, comic panel. No color, no photorealistic."
        ),
        "3D / render": (
            "Output style tags: 3d, 3d render, cgi, realistic materials. Not anime, not a photograph."
        ),
        "Pixar / cartoon 3D": (
            "Output style tags: 3d, pixar style, stylized, cartoon, disney style. Not photoreal, not 2d anime."
        ),
        "Pintura al óleo": (
            "Output style tags: oil painting, painting (medium), brushstroke, canvas texture. Not photo, not anime."
        ),
        "Acuarela": (
            "Output style tags: watercolor, watercolor (medium), paper texture. Not photo, not anime."
        ),
        "Ilustración digital": (
            "Output style tags: digital illustration, official art, high quality illustration. Not photorealistic photo."
        ),
        "Cómic": (
            "Output style tags: comic, comic book, western comic, ink, halftone. Not photorealistic, not manga."
        ),
        "Fantasía oscura": (
            "Output style tags: dark fantasy, moody lighting, cinematic shadows, grim atmosphere."
        ),
    }
    table = illu if is_illustrious else krea
    specific = table.get(estilo)
    if not specific:
        specific = f"Write the prompt in this output style: {estilo}."
    return ignore + " " + specific


def _aspect_names(use) -> list:
    if isinstance(use, (list, tuple)):
        return [normalize_aspect_key(a) for a in use]
    return [normalize_aspect_key(use)]


def _roles_rule(refs: list) -> str:
    if len(refs) < 2:
        return ""
    lines = [
        "The images have different roles. Combine them: keep only the requested aspect(s) from each image."
    ]
    uses = {idx: normalize_aspect_list(use) for idx, _t, use in refs}
    persona_idx = [i for i, u in uses.items() if "persona" in u]
    feature_src = {}
    for key, label in (("pelo", "hair (style and color)"), ("expresion", "facial expression"), ("accesorios", "accessories")):
        src = [i for i, u in uses.items() if key in u and i not in persona_idx]
        if src:
            feature_src[key] = (label, src)
    if persona_idx:
        others = [str(i) for i in uses if i not in persona_idx]
        who = " and ".join(f"IMAGE {i}" for i in persona_idx)
        if others:
            banned = "the person, face, body or identity" if "pelo" in feature_src else "the person, face, hair, body or identity"
            lines.append(
                f"The person/identity MUST come from {who} only. "
                f"Do NOT use {banned} visible in IMAGE {', IMAGE '.join(others)}."
            )
    for key, (label, src) in feature_src.items():
        where = " and ".join(f"IMAGE {i}" for i in src)
        target = "the person from " + " and ".join(f"IMAGE {i}" for i in persona_idx) if persona_idx else "the subject"
        lines.append(
            f"Apply the {label} from {where} to {target}; it replaces that feature but keeps the identity."
        )
    return " ".join(lines)


def describe_reference_aspect(
    url,
    model_id,
    tensor,
    index,
    use,
    temperature,
    max_tokens,
    seed,
    idioma="Español",
):
    """One vision call: extract only the requested aspect(s) from a single image."""
    aspects = normalize_aspect_list(use)
    labels = aspect_label_list(aspects)
    others = other_aspect_labels(aspects)
    sections = []
    for key in aspects:
        label = ASPECT_LABELS.get(key, key)
        hint = ASPECT_PROMPTS.get(key, ASPECT_PROMPTS["todo"])
        sections.append(f"### {label.upper()}\n{hint}")
    forbid = (
        f"You MUST NOT mention, describe or imply any of: {others}. "
        if others else ""
    )
    camera_only = aspects == ["camara"] or (len(aspects) == 1 and aspects[0] == "camara")
    camera_lock = (
        "This request is camera-only: write solely about framing, shot type, angle, lens/POV and composition. "
        "Explicitly forbid background, setting, landscape, weather, clothing, subject identity, pose and action. "
        if camera_only else ""
    )
    prompt = (
        f"This is IMAGE {index}. Extract ONLY these aspect(s): {labels}. "
        f"{forbid}{camera_lock}"
        f"Use separate labeled sections exactly as follows:\n\n" + "\n\n".join(sections) + "\n\n"
    )
    if is_english(idioma):
        prompt += (
            "Write a dense factual description in English under each heading. "
            "Do not mix clothing into the style section, or style/medium into the clothing section. "
            "Do not write a full image prompt, do not mention other images, do not mention these instructions."
        )
        sys_out = (
            "You extract visual facts from a single reference image. "
            f"Extract ONLY: {labels}. {forbid}{camera_lock}"
            "Output only the requested aspect(s), in English, under the given headings. No preamble."
        )
    else:
        prompt += (
            "Escribí una descripción factual densa en español bajo cada encabezado. "
            "No mezcles ropa en la sección de estilo, ni el estilo en la de ropa. "
            "No escribas un prompt completo, no menciones otras imágenes ni estas instrucciones."
        )
        sys_out = (
            "Extraés hechos visuales de una sola imagen de referencia. "
            f"Extraé SOLO: {labels}. {forbid}{camera_lock}"
            "Devolvé solo los aspectos pedidos, en español, bajo los encabezados dados. Sin preámbulo."
        )
    content = _user_content(prompt, "", images=[(index, tensor, labels)])
    raw = chat_complete(
        url,
        model_id,
        [
            {
                "role": "system",
                "content": sys_out,
            },
            {"role": "user", "content": content},
        ],
        temperature,
        min(int(max_tokens), 700),
        seed,
    )
    return clean_output(raw)


def filter_description_to_aspects(
    url,
    model_id,
    description,
    index,
    use,
    temperature,
    max_tokens,
    seed,
):
    """Text-only rewrite of a stored description, keeping only enabled aspects."""
    aspects = normalize_aspect_list(use)
    labels = aspect_label_list(aspects)
    others = other_aspect_labels(aspects)
    camera_only = aspects == ["camara"] or (len(aspects) == 1 and aspects[0] == "camara")
    camera_lock = (
        "Camera-only: keep solely framing, shot type, angle, lens/POV and composition. "
        "Drop background, setting, landscape, weather, clothing, subject identity, pose and action. "
        if camera_only else ""
    )
    user = (
        f"IMAGE {index} requested aspect(s): {labels}.\n"
        f"Delete anything about: {others}. {camera_lock}\n\n"
        f"Description:\n{description}"
    )
    raw = chat_complete(
        url,
        model_id,
        [
            {
                "role": "system",
                "content": (
                    "You filter a description of a reference image. "
                    "Rewrite it so it contains ONLY the requested aspect(s). "
                    "If a sentence is not about those aspect(s), drop it. "
                    "Output plain English, no preamble."
                ),
            },
            {"role": "user", "content": user},
        ],
        min(float(temperature or 0.3), 0.3),
        min(int(max_tokens or 400), 400),
        seed,
    )
    return clean_output(raw)


def describe_image_info(
    url,
    model,
    filename,
    subfolder="",
    typ="input",
    temperature=0.3,
    max_tokens=400,
    seed=0,
    idioma="Español",
):
    """Informational full description of one image. Does not unload the model."""
    image = load_ref_image(filename, subfolder, typ)
    if not _has_image(image):
        raise RuntimeError("No pude leer la imagen para describirla.")
    url = _norm_url(url)
    emit_activity(idioma, "connecting")
    model_id = pick_model(url, model)
    model_id = announce_model_use(url, model_id, idioma) or model_id
    vis = _model_is_vision(url, model_id)
    if vis is False:
        raise RuntimeError(VISION_REQUIRED)
    emit_activity(idioma, "describing_one")
    t0 = time.perf_counter()
    if is_english(idioma):
        prompt = (
            "Describe this image in clear English. Cover subject, appearance, clothing, pose, "
            "setting, lighting and style. Be factual and concise. Output only the description."
        )
        sys = "You describe images factually, in English. No preamble."
    else:
        prompt = (
            "Describe esta imagen en español claro. Incluí sujeto, apariencia, ropa, pose, "
            "escenario, iluminación y estilo. Sé factual y conciso. Escribí solo la descripción."
        )
        sys = "Describís imágenes de forma factual, en español. Sin preámbulo."
    content = _user_content(prompt, "", images=[(1, image, "todo")])
    raw = chat_complete(
        url,
        model_id,
        [
            {"role": "system", "content": sys},
            {"role": "user", "content": content},
        ],
        temperature,
        max_tokens,
        seed,
    )
    text = clean_output(raw)
    emit_activity(idioma, "described_one", secs=f"{time.perf_counter() - t0:.1f}")
    emit_activity(idioma, "done")
    return text


def _generate_prompt_impl(
    idea,
    mode,
    url,
    model,
    temperature,
    max_tokens,
    seed=0,
    unload_after=True,
    extra_instructions="",
    image=None,
    image_1=None,
    image_2=None,
    image_3=None,
    image_4=None,
    usar_imagen_1="todo",
    usar_imagen_2="todo",
    lora_triggers="",
    estilo_salida="(como la referencia)",
    **kwargs,
):
    """Call LM Studio and return (positive, negative). Raises RuntimeError in Spanish."""
    idea = (idea or "").strip()
    refs = collect_ref_images(
        image, image_1, image_2, image_3, image_4,
        usar_imagen_1, usar_imagen_2, estilo_salida, **kwargs,
    )
    has_img = bool(refs)
    if not idea and not has_img:
        raise RuntimeError(MISSING_IDEA_OR_IMAGE)

    url = _norm_url(url)
    idioma = kwargs.get("idioma", "Español")
    emit_activity(idioma, "connecting")
    is_illustrious = str(mode).lower().startswith("illustrious")
    system = SYS_ILLUSTRIOUS if is_illustrious else SYS_KREA2
    want_es = want_spanish_view(kwargs.get("idioma", "Español"))
    # The Spanish view is no longer written in the same reply: it is a separate
    # translation of the FINAL English prompt (after triggers are merged).
    guide = " ".join(image_use_sentence(idx, use) for idx, _tensor, use in refs)
    roles = _roles_rule(refs)
    if roles:
        guide = (guide + " " + roles).strip()
    n_pers = parse_personas(kwargs.get("num_personas", "1"), kwargs.get("num_personas_custom", 1))
    pers = personas_instruction(n_pers, refs)
    if pers:
        guide = (guide + " " + pers).strip()
    cam = camera_instruction(kwargs.get("camara", CAMARA_AUTO), refs, **kwargs)
    if cam:
        guide = (guide + " " + cam).strip()
    estilo_inst = style_instruction(estilo_salida, is_illustrious)
    if not idea and has_img:
        idea = IMAGE_ONLY_ILLUSTRIOUS if is_illustrious else IMAGE_ONLY_KREA2
        if len(refs) > 1:
            idea = idea.replace("this reference image", "these reference images").replace("from it", "from them")
        if guide:
            idea = idea + "\n\n" + guide
    elif idea and has_img:
        idea = idea + "\n\n" + (guide or "Use the attached image as a visual reference.")

    all_triggers = normalize_triggers(lora_triggers)
    modo_ropa = kwargs.get("modo_ropa", ROPA_AUTO)
    triggers, removed_clothing = effective_triggers(all_triggers, modo_ropa, ropa_image_indices(refs))
    if removed_clothing:
        print(f"[LD-PromptWriter] ropa={normalize_ropa(modo_ropa)!r}: se quitan de los triggers {len(removed_clothing)} fragmento(s) de ropa", flush=True)
    trig_inst = triggers_instruction(is_illustrious, triggers)
    ropa_inst = ropa_instruction(modo_ropa, refs, bool(all_triggers), removed_clothing)
    if ropa_inst:
        print(f"[LD-PromptWriter] ropa={normalize_ropa(kwargs.get('modo_ropa', ROPA_AUTO))!r}", flush=True)
    extra_bits = [str(extra_instructions or "").strip(), estilo_inst, trig_inst, ropa_inst]
    extra_instructions = "\n\n".join(b for b in extra_bits if b)

    try:
        model_id = pick_model(url, model)
        model_id = announce_model_use(url, model_id, idioma) or model_id
    except RuntimeError as e:
        emit_activity(idioma, "error", msg=str(e), level="err")
        raise
    except Exception as e:
        emit_activity(idioma, "error", msg=str(e), level="err")
        raise RuntimeError(_down_msg(url)) from e

    if has_img:
        vis = _model_is_vision(url, model_id)
        if vis is False:
            raise RuntimeError(VISION_REQUIRED)

    print(
        f"[LD-PromptWriter] generate con {len(refs)} imagen(es): "
        + (", ".join(f"IMAGE {i} ({u if isinstance(u, str) else ', '.join(u)})" for i, _t, u in refs) if refs else "ninguna")
        + f"; estilo={estilo_salida!r}",
        flush=True,
    )

    try:
        if refs:
            # Never send raw images to the final compose call. Aspects are
            # enforced in text: either a restricted on-the-fly describe, or a
            # filtered saved description, plus an explicit per-image rule.
            notes = []
            rules = []
            for idx, tensor, use in refs:
                asp = normalize_aspect_list(use)
                asp_lbl = aspect_label_list(asp)
                rules.append(composer_only_rule(idx, asp))
                saved = saved_image_description(idx, kwargs)
                saved_sig = str(kwargs.get("desc_aspects_%s" % idx) or "").strip()
                cur_sig = aspect_signature(asp)
                fresh = bool(saved) and saved_sig == cur_sig
                if fresh:
                    note = saved
                    print(f"[LD-PromptWriter] IMAGE {idx}: descripción al día ({asp_lbl}), no se redescribe", flush=True)
                else:
                    emit_activity(idioma, "describing", n=idx, aspects=asp_lbl)
                    t0 = time.perf_counter()
                    note = describe_reference_aspect(
                        url, model_id, tensor, idx, asp, temperature, max_tokens, seed, idioma=idioma,
                    )
                    secs = f"{time.perf_counter() - t0:.1f}"
                    emit_activity(idioma, "described", n=idx, secs=secs)
                    emit_desc_update(idx, note, cur_sig)
                    print(f"[LD-PromptWriter] describí IMAGE {idx} ({asp_lbl}): {len(note)} caracteres", flush=True)
                notes.append(
                    f"Notes from IMAGE {idx} — use ONLY: {asp_lbl}; ignore everything else:\n{note}"
                )
            emit_activity(idioma, "composing")
            hard = (
                "Hard rule for every reference image: use ONLY the listed aspect(s) "
                "and ignore everything else, even if the notes accidentally mention other details. "
                + " ".join(rules)
            )
            compose = idea + "\n\n" + hard + "\n\n" + "\n\n".join(notes)
            if roles:
                compose += "\n\n" + roles
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": _user_content(compose, extra_instructions, images=[])},
            ]
        else:
            emit_activity(idioma, "composing")
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": _user_content(idea, extra_instructions, images=refs)},
            ]
        two = normalize_pasadas(kwargs.get("pasadas")) == PASADAS_2
        if two:
            emit_activity(idioma, "pass_n", n=1, total=2)
        raw = chat_complete(url, model_id, messages, temperature, max_tokens, seed)
        print(f"[LD-PromptWriter] pasada 1: respuesta de {len(clean_output(raw).split())} palabras", flush=True)
    except RuntimeError as e:
        if has_img and _looks_like_no_vision_error(str(e)):
            raise RuntimeError(VISION_REQUIRED) from e
        raise
    except Exception as e:
        msg = str(e)
        if has_img and _looks_like_no_vision_error(msg):
            raise RuntimeError(VISION_REQUIRED) from e
        raise RuntimeError(_down_msg(url)) from e

    positive, negative = _parse_final_prompt(raw, is_illustrious)

    # Too-short answer (some models stop after a sentence or only echo the
    # LoRA text): ask once more for the complete prompt.
    _own = len(_scene_text(positive, triggers).split())
    print(f"[LD-PromptWriter] prompt pasada 1: {len(positive.split())} palabras ({_own} propias, sin texto del LoRA)", flush=True)
    if _prompt_too_short(positive, is_illustrious, triggers):
        print(f"[LD-PromptWriter] respuesta corta ({_own} palabras propias): se pide el prompt completo otra vez", flush=True)
        emit_activity(idioma, "retry_short")
        try:
            retry_msgs = list(messages) + [
                {"role": "assistant", "content": positive or "(empty)"},
                {"role": "user", "content": RETRY_SHORT_ILLUSTRIOUS if is_illustrious else RETRY_SHORT_KREA2},
            ]
            raw2 = chat_complete(url, model_id, retry_msgs, temperature, max(int(max_tokens or 0), 1500), seed)
            p2, n2 = _parse_final_prompt(raw2, is_illustrious)
            if len(_scene_text(p2, triggers).split()) > _own:
                positive, negative = p2, (n2 or negative)
            print(f"[LD-PromptWriter] reintento: {len(_scene_text(p2, triggers).split())} palabras propias", flush=True)
        except Exception as e:
            print(f"[LD-PromptWriter] reintento falló: {e}", flush=True)

    if not positive:
        raise RuntimeError(
            "El modelo no devolvió un prompt. Si es un modelo con thinking, "
            "desactivá Reasoning/Thinking en LM Studio e intentá de nuevo."
        )

    if two:
        positive, negative = refine_prompt_pass(
            url, model_id, system, messages, positive, negative, is_illustrious,
            triggers, temperature, max_tokens, seed, idioma,
        )
    emit_activity(idioma, "done")

    positive = ensure_triggers(positive, triggers, is_illustrious)
    vista_es = ""
    if want_es:
        vista_es = spanish_view_of(url, model_id, positive, is_illustrious, seed, idioma, max_tokens)
    emit_vista_es(vista_es)
    return positive, negative, vista_es


PASADAS_1 = "1 pasada"
PASADAS_2 = "2 pasadas"
PASADAS_OPTIONS = (PASADAS_1, PASADAS_2)


def normalize_pasadas(value) -> str:
    return PASADAS_2 if str(value or "").strip().startswith("2") else PASADAS_1


RETRY_SHORT_KREA2 = (
    "Your answer is incomplete (describing only the character, or only copying the LoRA text, is not a prompt). "
    "Write the COMPLETE final image prompt now, following every instruction above: "
    "all participants, their appearance, action and pose, camera and framing, setting, lighting and style. "
    "Output only the prompt."
)
RETRY_SHORT_ILLUSTRIOUS = (
    "Your answer is incomplete. Write the COMPLETE Danbooru-style tag line now, following every instruction above "
    "(quality tags, LoRA triggers, subject count, appearance, action, pose, camera, setting, style), then the "
    "Negative: line. Output only that."
)


def _parse_final_prompt(raw, is_illustrious):
    body, _es = parse_bilingual(raw)
    if is_illustrious:
        return parse_illustrious(body)
    return clean_output(body), ""


def _scene_text(positive, triggers=None) -> str:
    """The prompt without any LoRA text copied into it (to judge real content)."""
    text = str(positive or "")
    for frag in sorted((str(t) for t in (triggers or []) if str(t).strip()), key=len, reverse=True):
        text = re.sub(re.escape(frag.strip()), " ", text, flags=re.IGNORECASE)
    return " ".join(text.replace(" ,", ",").split()).strip(" ,.")


def _prompt_too_short(positive, is_illustrious, triggers=None) -> bool:
    text = _scene_text(positive, triggers)
    if not text:
        return True
    if is_illustrious:
        return len([t for t in text.split(",") if t.strip()]) < 8
    return len(text.split()) < 25


def refine_prompt_pass(url, model_id, system, messages, positive, negative, is_illustrious,
                       triggers, temperature, max_tokens, seed, idioma):
    """Pass 2/2: same instructions + the pass-1 draft; the LLM checks and improves it.

    Returns (positive, negative). On any failure keeps the pass-1 result.
    """
    original_user = ""
    for m in messages:
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, list):
                c = "\n".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
            original_user = str(c or "")
    draft = positive if not is_illustrious else (positive + "\nNegative: " + (negative or ""))
    if is_illustrious:
        task = (
            "Review the DRAFT tag line against ALL the specifications above (reference image notes and their "
            "allowed aspects, clothing rule, number of participants, output style, camera, LoRA trigger words). "
            "Fix contradictions, add any requested aspect that is missing, remove anything that breaks a rule, "
            "keep the required tag order and the LoRA trigger words verbatim. "
            "Output only the final tag line followed by a line starting with 'Negative:'. No explanations."
        )
    else:
        task = (
            "Review the DRAFT prompt against ALL the specifications above (reference image notes and their "
            "allowed aspects, clothing rule, number of participants, output style, camera, LoRA trigger words). "
            "Fix contradictions, add any requested aspect that is missing, remove anything that breaks a rule, "
            "and improve clarity and visual detail while keeping it one natural-language prompt. "
            "Keep the LoRA trigger words verbatim. Output only the final prompt. No explanations, no headings."
        )
    user = (
        "SPECIFICATIONS (same as for the draft):\n" + original_user.strip()
        + "\n\nDRAFT (pass 1):\n" + draft.strip()
        + "\n\n" + task
    )
    emit_activity(idioma, "pass_n", n=2, total=2)
    t0 = time.perf_counter()
    try:
        raw = chat_complete(
            url, model_id,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            min(float(temperature if temperature is not None else 0.5), 0.5),
            max(int(max_tokens or 0), 1500),
            seed,
        )
        p2, n2 = _parse_final_prompt(raw, is_illustrious)
        print(f"[LD-PromptWriter] pasada 2: {len(p2.split())} palabras ({time.perf_counter() - t0:.1f} s)", flush=True)
        if _prompt_too_short(p2, is_illustrious, triggers) or len(p2.split()) < 0.5 * len(positive.split()):
            print("[LD-PromptWriter] pasada 2 descartada (respuesta corta); se usa la pasada 1", flush=True)
            return positive, negative
        return p2, (n2 or negative)
    except Exception as e:
        print(f"[LD-PromptWriter] pasada 2 falló, se usa la pasada 1: {e}", flush=True)
        emit_activity(idioma, "error", msg=f"pasada 2: {e}", level="err")
        return positive, negative


def _image_fingerprint(image) -> str:
    try:
        arr = image
        if hasattr(arr, "detach"):
            arr = arr.detach()
        if hasattr(arr, "cpu"):
            arr = arr.cpu().numpy()
        shape = str(getattr(arr, "shape", ""))
        # First/last slices keep the hash cheap on large batches.
        raw = arr.tobytes() if hasattr(arr, "tobytes") else bytes(str(arr), "utf-8")
        if len(raw) > 65536:
            raw = raw[:32768] + raw[-32768:]
        return hashlib.sha256(shape.encode("utf-8") + raw).hexdigest()[:20]
    except Exception:
        return "image"


class LD_LMStudioPromptWriter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "idea": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "La idea de la imagen. Puede estar en español.",
                    },
                ),
                "mode": (
                    ["Krea2 (natural)", "Illustrious (tags)"],
                    {"tooltip": "Krea2: prosa en inglés. Illustrious: tags estilo Danbooru."},
                ),
                "url": (
                    "STRING",
                    {
                        "default": DEFAULT_URL,
                        "tooltip": "URL del servidor local de LM Studio.",
                    },
                ),
                "model": (
                    combo_model_choices(timeout=1.5),
                    {
                        "default": AUTO_MODEL,
                        "tooltip": "Modelo de LM Studio. '(auto: el cargado)' usa el que ya está en memoria. Si elegís uno que no está cargado, LM Studio lo carga al generar.",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05},
                ),
                "max_tokens": (
                    "INT",
                    {"default": 600, "min": 64, "max": 4096, "step": 1},
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Cambia la seed para pedir otra versión del prompt.",
                    },
                ),
                "unload_after": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Descarga el modelo al terminar Generar o al ejecutar el workflow. Describir nunca descarga.",
                    },
                ),
            },
            "optional": {
                "extra_instructions": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Indicaciones extra para el LLM (estilo, encuadre, etc.).",
                    },
                ),
                "usar_prompt_generado": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Si está activo y el recuadro de la derecha tiene texto, se usa ese prompt sin llamar al LLM.",
                    },
                ),
                "prompt_generado": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Prompt positivo generado. Editable. Se ve en el panel derecho.",
                    },
                ),
                "negativo_generado": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Prompt negativo generado. Editable. Se ve en el panel derecho.",
                    },
                ),
                "image": (
                    "IMAGE",
                    {"tooltip": "Imagen de referencia (hace falta un modelo de visión en LM Studio)."},
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "write"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, model, mode=None, **kwargs):
        """Accept any model id (and legacy empty/auto).

        execution.py skips the COMBO 'value not in list' check for an input
        when that input is a VALIDATE_INPUTS argument. The list changes as
        models are downloaded or the server goes offline, so membership
        must not be required. Invalid mode values are coerced in write().
        """
        if model is not None and not isinstance(model, (str, int)):
            return "modelo inválido: %r" % (model,)
        return True

    @classmethod
    def IS_CHANGED(
        cls,
        idea,
        mode,
        url,
        model,
        temperature,
        max_tokens,
        seed,
        unload_after,
        extra_instructions="",
        image=None,
        usar_prompt_generado=True,
        prompt_generado="",
        negativo_generado="",
        **kwargs,
    ):
        use_box = bool(str(prompt_generado or "").strip())
        parts = [
            str(idea),
            str(mode),
            _norm_url(str(url)),
            "" if is_auto_model(model) else strip_model_label(str(model or "")),
            f"{float(temperature):.4f}",
            str(int(max_tokens)),
            str(int(seed)),
            str(bool(unload_after)),
            str(extra_instructions or ""),
            str(bool(usar_prompt_generado)),
            str(prompt_generado or ""),
            str(negativo_generado or ""),
        ]
        if image is not None and not use_box:
            parts.append(_image_fingerprint(image))
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def write(
        self,
        idea,
        mode,
        url,
        model,
        temperature,
        max_tokens,
        seed,
        unload_after,
        extra_instructions="",
        image=None,
        usar_prompt_generado=True,
        prompt_generado="",
        negativo_generado="",
    ):
        mode = sanitize_combo(mode, MODE_OPTIONS, "Krea2 (natural)")
        cached = str(prompt_generado or "").strip()
        if cached:
            positive = cached
            negative = str(negativo_generado or "")
            ui_lines = [positive]
            if negative.strip():
                ui_lines.extend(["--- negative ---", negative])
            return {
                "ui": {
                    "text": ui_lines,
                    "prompt_generado": [positive],
                    "negativo_generado": [negative],
                },
                "result": (positive, negative),
            }

        positive, negative, vista_es = generate_prompt(
            idea,
            mode,
            url,
            model,
            temperature,
            max_tokens,
            seed,
            unload_after,
            extra_instructions,
            image,
        )
        ui_lines = [positive]
        if negative:
            ui_lines.extend(["--- negative ---", negative])
        return {
            "ui": {
                "text": ui_lines,
                "prompt_generado": [positive],
                "negativo_generado": [negative],
            },
            "result": (positive, negative),
        }



def test_connection(url: str) -> dict:
    """Probe LM Studio with GET only. Never loads or unloads a model."""
    url = _norm_url(url)
    try:
        data, kind = _list_lms_models(url)
    except Exception:
        return {
            "ok": False,
            "reachable": False,
            "url": url,
            "models": [],
            "loaded": [],
            "vision": False,
            "vision_models": [],
            "vision_detectable": False,
            "message": f"❌ LM Studio no responde en {url}",
        }

    models = [m.get("id") for m in data if m.get("id")]
    loaded = []
    vision_models = []
    vision_detectable = kind == "v0"

    if kind == "v0":
        for m in data:
            mid = m.get("id")
            if not mid:
                continue
            typ = str(m.get("type") or "").lower()
            caps = m.get("capabilities") or m.get("capability") or []
            if isinstance(caps, str):
                caps = [caps]
            vis = typ in ("vlm", "vision") or any("vision" in str(c).lower() for c in caps)
            if vis:
                vision_models.append(mid)
            if m.get("state") == "loaded" and typ not in ("embedding", "tts"):
                loaded.append(mid)
    # /v1/models does not report state; do not pretend those ids are loaded.

    if loaded:
        msg = "✅ LM Studio OK — modelo cargado: " + ", ".join(loaded)
    elif kind == "v0":
        msg = "✅ LM Studio OK — ningún modelo cargado"
    elif models:
        msg = "✅ LM Studio OK — servidor activo, modelos: " + ", ".join(models)
    else:
        msg = "✅ LM Studio OK — ningún modelo listado"

    if vision_detectable:
        vis_loaded = [m for m in vision_models if m in loaded]
        if vis_loaded:
            msg += " — visión disponible"
        elif vision_models:
            msg += " — hay modelo de visión, pero no está cargado"
        else:
            msg += " — sin modelo de visión detectado"

    return {
        "ok": True,
        "reachable": True,
        "url": url,
        "models": models,
        "loaded": loaded,
        "vision": bool(vision_models and (not loaded or any(m in loaded for m in vision_models))),
        "vision_models": vision_models,
        "vision_detectable": vision_detectable,
        "message": msg,
    }




CAMARA_AUTO = "(Automático - decide el LLM)"
CAMARA_OPTIONS = (
    CAMARA_AUTO,
    "Primer plano / Close-up",
    "Plano medio / Medium shot",
    "Plano americano / Cowboy shot",
    "Cuerpo entero / Full body",
    "Plano general / Wide shot",
    "Picado / High angle",
    "Contrapicado / Low angle",
    "Vista cenital / Top-down",
    "A nivel de ojos / Eye level",
    "POV primera persona",
    "Por encima del hombro / Over the shoulder",
    "Perfil / Side view",
    "De espaldas / From behind",
    "Ángulo holandés / Dutch angle",
    "Macro",
    "Gran angular / Wide-angle lens",
    "Teleobjetivo / Telephoto",
    "Selfie",
)

ACTIVITY_I18N = {
    "es": {
        "connecting": "Conectando a LM Studio…",
        "loading": "Cargando modelo {model}…",
        "reusing": "Reutilizando modelo {model} (instancia ya cargada)",
        "describing": "Describiendo imagen {n} ({aspects})…",
        "describing_one": "Describiendo la imagen…",
        "described": "Imagen {n} lista ({secs} s)",
        "described_one": "Descripción lista ({secs} s)",
        "translating_es": "Traduciendo la vista en español al inglés…",
        "translated_es": "Vista traducida al inglés ({secs} s)",
        "translating_view": "Traduciendo el prompt final al español…",
        "pass_n": "Pasada {n}/{total}…",
        "retry_short": "Respuesta corta: pidiendo el prompt completo…",
        "translated_view": "Vista en español lista ({secs} s)",
        "composing": "Componiendo prompt final…",
        "done": "Listo",
        "unloading": "Descargando modelo…",
        "unloaded": "Modelo descargado",
        "idle_unloading": "Descargando modelo por inactividad ({minutes} min)…",
        "cached": "Usando el prompt ya generado (sin llamar al LLM)",
        "modifying": "Aplicando cambios al prompt…",
        "modified": "Prompt modificado ({secs} s)",
        "error": "Error: {msg}",
    },
    "en": {
        "connecting": "Connecting to LM Studio…",
        "loading": "Loading model {model}…",
        "reusing": "Reusing model {model} (instance already loaded)",
        "describing": "Describing image {n} ({aspects})…",
        "describing_one": "Describing the image…",
        "described": "Image {n} ready ({secs} s)",
        "described_one": "Description ready ({secs} s)",
        "translating_es": "Translating the Spanish view into English…",
        "translated_es": "Spanish view translated to English ({secs} s)",
        "translating_view": "Translating the final prompt into Spanish…",
        "pass_n": "Pass {n}/{total}…",
        "retry_short": "Short answer: asking for the complete prompt…",
        "translated_view": "Spanish view ready ({secs} s)",
        "composing": "Composing the final prompt…",
        "done": "Done",
        "unloading": "Unloading the model…",
        "unloaded": "Model unloaded",
        "idle_unloading": "Unloading the model after {minutes} min idle…",
        "cached": "Using the prompt already in the box (no LLM call)",
        "modifying": "Applying changes to the prompt…",
        "modified": "Prompt updated ({secs} s)",
        "error": "Error: {msg}",
    },
}


def emit_activity(idioma, key, **params):
    """Push a live status line to the Writer UI via PromptServer.send_sync."""
    lang = "en" if is_english(idioma) else "es"
    tmpl = ACTIVITY_I18N.get(lang, ACTIVITY_I18N["es"]).get(key) or ACTIVITY_I18N["es"].get(key) or key
    try:
        msg = tmpl.format(**{k: v for k, v in params.items() if k != "level"})
    except Exception:
        msg = tmpl
    payload = {"message": msg, "key": key, "level": params.get("level", "info")}
    try:
        from server import PromptServer
        inst = getattr(PromptServer, "instance", None)
        if inst is not None:
            inst.send_sync("ld_promptwriter_activity", payload)
    except Exception:
        pass
    print(f"[LD-PromptWriter] {msg}", flush=True)
    return msg



# LM Studio JIT default TTL is 60 minutes and ttl:0 may unload immediately.
# ttl:-1 keeps the loaded instance (no idle expiry). If the user set an idle
# timer, we also pass that many seconds as a safety-net TTL.
TTL_NO_EXPIRE = -1
_chat_ttl = TTL_NO_EXPIRE
_idle_lock = threading.Lock()
_idle_timer = None


def chat_ttl_seconds(idle_min) -> int:
    try:
        minutes = float(idle_min or 0)
    except (TypeError, ValueError):
        minutes = 0.0
    if minutes > 0:
        return max(60, int(minutes * 60))
    return TTL_NO_EXPIRE


def set_chat_ttl(idle_min) -> int:
    global _chat_ttl
    _chat_ttl = chat_ttl_seconds(idle_min)
    return _chat_ttl


def cancel_idle_unload():
    global _idle_timer
    with _idle_lock:
        if _idle_timer is not None:
            try:
                _idle_timer.cancel()
            except Exception:
                pass
            _idle_timer = None


def schedule_idle_unload(url, model, idioma, idle_min):
    """Start (or reset) the optional idle unload timer. 0 = off."""
    cancel_idle_unload()
    try:
        minutes = float(idle_min or 0)
    except (TypeError, ValueError):
        minutes = 0.0
    if minutes <= 0:
        return
    url = _norm_url(url)
    mid = strip_model_label(model or "")

    def _fire():
        try:
            mins = int(minutes) if minutes == int(minutes) else minutes
            emit_activity(idioma, "idle_unloading", minutes=mins)
            unload_models(url, mid)
            emit_activity(idioma, "unloaded")
        except Exception as e:
            print(f"[LD-PromptWriter] aviso al descargar por inactividad: {e}", flush=True)

    global _idle_timer
    with _idle_lock:
        _idle_timer = threading.Timer(minutes * 60.0, _fire)
        _idle_timer.daemon = True
        _idle_timer.start()
    print(f"[LD-PromptWriter] idle unload en {minutes} min", flush=True)


def announce_model_use(url, model_id, idioma) -> str:
    """Log whether we reuse a loaded instance or will JIT-load. Prefer loaded id."""
    mid = strip_model_label(model_id or "")
    insts = _v1_instances(url)
    for key, iid in insts:
        if (
            not mid
            or is_auto_model(mid)
            or key == mid
            or iid == mid
            or (key and mid.startswith(key))
            or iid.startswith(mid + ":")
        ):
            label = key or mid or iid
            emit_activity(idioma, "reusing", model=label)
            return key or mid
    emit_activity(idioma, "loading", model=mid or model_id)
    return mid or model_id


def camera_instruction(preset, refs, **kwargs) -> str:
    """Priority: image Cámara/POV toggles, then the dropdown, else the LLM decides."""
    cam_imgs = [
        idx
        for idx, _tensor, aspects in (refs or [])
        if "camara" in (aspects if isinstance(aspects, (list, tuple)) else [aspects])
    ]
    if cam_imgs:
        labels = ", ".join(f"IMAGE {i}" for i in cam_imgs)
        return (
            f"Take the camera angle, shot type, point of view, lens and framing from {labels} "
            "(the Cámara / POV aspect). Use that camera for the final scene."
        )
    val = " ".join(str(preset or "").strip().split()) or CAMARA_AUTO
    if val == CAMARA_AUTO or val.lower().startswith("(auto"):
        return "Choose an appropriate camera angle, shot type, POV and lens for the scene."
    return (
        f"Use this camera / framing for the final image: {val}. "
        "Keep it consistent unless the idea explicitly requires a different shot."
    )


PERSONAS_AUTO = "Auto (decide el LLM)"
PERSONAS_CUSTOM = "Personalizado"
PERSONAS_OPTIONS = (PERSONAS_AUTO,) + tuple(str(i) for i in range(1, 9)) + (PERSONAS_CUSTOM,)


def parse_personas(value, custom=1) -> int:
    """0 = Auto (the LLM decides). Otherwise a count 1–99."""
    raw = " ".join(str(value or "1").strip().split())
    if not raw or raw == PERSONAS_AUTO or raw.lower().startswith("auto"):
        return 0
    if raw == PERSONAS_CUSTOM or raw.lower().startswith("personal") or raw.lower().startswith("custom"):
        try:
            n = int(str(custom or "1").strip().split()[0])
        except ValueError:
            n = 1
        return max(1, min(99, n))
    try:
        n = int(raw.split()[0])
    except ValueError:
        n = 1
    return max(1, min(99, n))


def is_english(idioma) -> bool:
    s = str(idioma or "").strip().lower()
    return s.startswith("eng") or s == "en"


def want_spanish_view(idioma) -> bool:
    return not is_english(idioma)


def bilingual_instruction(is_illustrious: bool, modify: bool = False) -> str:
    if modify:
        return SYS_ES_VIEW_MODIFY
    return SYS_ES_VIEW_ILLUSTRIOUS if is_illustrious else SYS_ES_VIEW_KREA2


def parse_bilingual(text: str) -> tuple[str, str]:
    """Split an LLM reply into (main_prompt_text, spanish_view)."""
    text = clean_output(text)
    parts = _ES_SPLIT.split(text, maxsplit=1)
    es = ""
    if len(parts) >= 2:
        body, es = parts[0].strip(), parts[1].strip()
        # If the model put Negative: after ES:, move it back to the English body.
        neg_parts = _NEG_SPLIT.split(es, maxsplit=1)
        if len(neg_parts) == 2:
            es = neg_parts[0].strip()
            body = (body + "\n\nNegative: " + neg_parts[1].strip()).strip()
    else:
        body = text
    body = _PROMPT_HEAD.sub("", body).strip()
    return body, es


def emit_vista_es(text: str) -> None:
    """Push the Spanish preview to the Writer panel (not a widget; no widgets_values shift)."""
    payload = {"text": str(text or "")}
    try:
        from server import PromptServer
        inst = getattr(PromptServer, "instance", None)
        if inst is not None:
            inst.send_sync("ld_promptwriter_vista_es", payload)
    except Exception:
        pass


def _bump_tokens_for_es(max_tokens, want_es: bool) -> int:
    try:
        tok = int(max_tokens or 600)
    except (TypeError, ValueError):
        tok = 600
    if not want_es:
        return max(1, tok)
    return max(tok, min(tok + 400, 2000))


def personas_instruction(n, refs) -> str:
    """Tell the LLM how many people to include, with or without reference images."""
    persona_imgs = []
    for idx, _tensor, aspects in refs or []:
        asp = aspects if isinstance(aspects, (list, tuple)) else [aspects]
        if "persona" in asp or "todo" in asp or asp == ["todo"]:
            persona_imgs.append(idx)
    mapped = ""
    if persona_imgs:
        cap = n if n and n > 0 else len(persona_imgs)
        pairs = ", ".join(f"IMAGE {i} → person {k}" for k, i in enumerate(persona_imgs[:cap], 1))
        mapped = (
            f" If reference images have the Persona aspect enabled, use them as identity sources "
            f"in order: {pairs}."
        )
        if n and len(persona_imgs) < n:
            mapped += f" Invent the remaining {n - len(persona_imgs)} people so the total is {n}."
        elif n and len(persona_imgs) > n:
            mapped += f" Use only the first {n} of those identities."
    if n == 0:
        return (
            "Decide a sensible number of people for the scene (one or more). "
            "Invent each extra participant with their own face, hair, body, clothing and a clear position "
            "when the idea needs them. Do not force a single person if the scene calls for more."
            + mapped
        )
    if n <= 1:
        return mapped.strip()
    if n == 2:
        pos = "left and right"
    elif n == 3:
        pos = "left, center and right"
    else:
        pos = "spread across the frame from left to right, without overlapping awkwardly"
    return (
        f"The scene MUST contain exactly {n} distinct people, even if there are no reference images. "
        f"Describe each one separately with their own face, hair, body, clothing and a clear position ({pos}). "
        f"Do not merge them into one person.{mapped}"
    )


ROPA_AUTO = "LoRA"  # was "Automático" in 1.1.2; normalize_ropa maps old values
ROPA_FOTO = "Foto"
ROPA_DESNUDO = "Desnudo"
ROPA_OPTIONS = (ROPA_AUTO, ROPA_FOTO, ROPA_DESNUDO)


def normalize_ropa(value) -> str:
    raw = " ".join(str(value or "").strip().split()).lower()
    if raw in ("foto", "photo"):
        return ROPA_FOTO
    if raw in ("desnudo", "nude", "nudo"):
        return ROPA_DESNUDO
    # "LoRA", legacy "Automático"/"Auto", empty or unknown.
    return ROPA_AUTO


def ropa_instruction(modo, refs, has_triggers=False, removed=None) -> str:
    """Clothing rule for the LLM: LoRA / Foto / Desnudo."""
    modo = normalize_ropa(modo)
    ropa_imgs = ropa_image_indices(refs or [])
    removed = [r for r in (removed or []) if str(r).strip()]
    omit = ""
    if removed:
        omit = (
            " The following LoRA description fragments were withheld because they describe clothing; "
            "do NOT reproduce their garments, but you may keep any non-clothing physical trait they mention "
            "(body, skin, hair, tattoos): " + " | ".join(removed) + "."
        )
    if modo == ROPA_DESNUDO:
        return (
            "CLOTHING RULE — HIGHEST PRIORITY, overrides the idea, the reference image notes and the LoRA trigger words: "
            "the subject(s) are fully unclothed. Do not mention or describe any garment, underwear, swimwear, footwear, "
            "fabric or outfit worn on the body (jewelry, glasses and held objects are allowed), and do not write phrases such as 'no clothing except', "
            "'as specified' or 'where garments end'. Keep identity and physical appearance traits from the LoRA trigger "
            "words (face, hair, eyes, skin, body, tattoos) and every other aspect (pose, action, background, camera, "
            "lighting, style) as instructed." + omit
        )
    if modo == ROPA_FOTO and ropa_imgs:
        imgs = ", ".join(f"IMAGE {i}" for i in ropa_imgs)
        return (
            f"CLOTHING RULE — HIGHEST PRIORITY: take the clothing exactly from {imgs} "
            "(garments, colors, materials, fit, accessories). This clothing replaces any clothing "
            "mentioned in the idea or in the LoRA trigger words; keep only the non-clothing traits from the triggers. "
            "Do not invent different clothing." + omit
        )
    if has_triggers:
        return (
            "Clothing rule: use the clothing described or implied by the LoRA trigger words. "
            "If they do not imply any clothing, choose clothing that fits the idea and the scene."
        )
    return ""


def _view_tokens(text: str, max_tokens=0) -> int:
    """Enough tokens for a full Spanish rendering (Spanish runs ~1.3x English)."""
    words = len(str(text or "").split())
    need = int(words * 2.6) + 200
    try:
        mt = int(max_tokens or 0)
    except (TypeError, ValueError):
        mt = 0
    return max(800, min(4096, max(need, mt)))


def translate_english_to_spanish(url, model_id, text, is_illustrious, seed=0, max_tokens=0) -> str:
    """Full translation (Krea2) or full gloss (Illustrious) of the FINAL English prompt."""
    text = str(text or "").strip()
    if not text:
        return ""
    if is_illustrious:
        system = (
            "You explain an English Danbooru-style tag line in natural Spanish for the user. "
            "Write a readable Spanish paragraph that covers EVERY tag (including LoRA trigger words, "
            "kept verbatim), in the same order. Do not add, drop or soften anything. "
            "Output only the Spanish text, no preamble."
        )
    else:
        system = (
            "You translate an English image prompt into natural Spanish for the user to read. "
            "Translate ALL of it, sentence by sentence, keeping every detail, the order and the meaning. "
            "Do not summarize, add, drop or soften anything. Keep LoRA trigger words, names and technical "
            "terms that have no Spanish equivalent verbatim. Output only the Spanish translation, no preamble "
            "or quotation marks."
        )
    raw = chat_complete(
        url,
        model_id,
        [{"role": "system", "content": system}, {"role": "user", "content": text}],
        0.2,
        _view_tokens(text, max_tokens),
        int(seed or 0),
    )
    out = clean_output(raw)
    out = _ES_LABEL_HEAD.sub("", out).strip()
    return out


_ES_LABEL_HEAD = re.compile(r"^\s*(?:ES|ESPAÑOL|SPANISH|TRADUCCI[ÓO]N)\s*:\s*", re.IGNORECASE)


def spanish_view_of(url, model_id, positive, is_illustrious, seed, idioma, max_tokens=0) -> str:
    """Spanish view of the final English prompt; never breaks generation."""
    try:
        emit_activity(idioma, "translating_view")
        t0 = time.perf_counter()
        es = translate_english_to_spanish(url, model_id, positive, is_illustrious, seed, max_tokens)
        emit_activity(idioma, "translated_view", secs=f"{time.perf_counter() - t0:.1f}")
        return es
    except Exception as e:
        print(f"[LD-PromptWriter] no pude traducir la vista en español: {e}", flush=True)
        emit_activity(idioma, "error", msg=f"vista en español: {e}", level="err")
        return ""


def refresh_spanish_view(text, mode, url, model, seed=0, max_tokens=0, idioma="Español",
                         unload_after=False, descarga_idle_min=0) -> str:
    """Re-translate the CURRENT English prompt for the read-only Spanish view.

    Used when the English box changed after the last translation (edited by
    hand, triggers merged on execution, etc.). Never touches the English.
    """
    text = str(text or "").strip()
    if not text:
        return ""
    url = _norm_url(url)
    is_illustrious = str(mode).lower().startswith("illustrious")
    cancel_idle_unload()
    set_chat_ttl(descarga_idle_min)
    try:
        model_id = pick_model(url, model)
        model_id = announce_model_use(url, model_id, idioma) or model_id
        emit_activity(idioma, "translating_view")
        t0 = time.perf_counter()
        es = translate_english_to_spanish(url, model_id, text, is_illustrious, seed, max_tokens)
        emit_activity(idioma, "translated_view", secs=f"{time.perf_counter() - t0:.1f}")
        return es
    except Exception as e:
        emit_activity(idioma, "error", msg=f"vista en español: {e}", level="err")
        raise
    finally:
        if unload_after:
            try:
                unload_models(url, model)
            except Exception as e:
                print(f"[LD-PromptWriter] aviso al descargar el modelo: {e}", flush=True)
        else:
            schedule_idle_unload(url, model, idioma, descarga_idle_min)


def translate_spanish_to_english(
    text,
    mode,
    url,
    model,
    temperature=0.3,
    max_tokens=700,
    seed=0,
    idioma="Español",
    extra_instructions="",
    unload_after=False,
    descarga_idle_min=0,
):
    """Translate a Spanish prompt/gloss into the English prompt used for generation."""
    text = str(text or "").strip()
    if not text:
        raise RuntimeError("No hay texto en español para traducir.")
    url = _norm_url(url)
    is_illustrious = str(mode).lower().startswith("illustrious")
    if is_illustrious:
        system = (
            "You translate a Spanish description into an Illustrious / NoobAI Danbooru-style "
            "English tag line. Output only the tag line, no preamble or quotation marks."
        )
    else:
        system = (
            "You translate a Spanish image-prompt description into a natural English image "
            "prompt for Krea 2. Keep the same meaning, details and structure. "
            "Output only the English prompt, no preamble or quotation marks."
        )
    extra = str(extra_instructions or "").strip()
    user = text if not extra else text + "\n\nAdditional instructions:\n" + extra
    cancel_idle_unload()
    set_chat_ttl(descarga_idle_min)
    emit_activity(idioma, "connecting")
    try:
        model_id = pick_model(url, model)
        model_id = announce_model_use(url, model_id, idioma) or model_id
        emit_activity(idioma, "translating_es")
        t0 = time.perf_counter()
        raw = chat_complete(
            url,
            model_id,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            float(temperature or 0.3),
            max(int(max_tokens or 700), _view_tokens(text, 0)),
            int(seed or 0),
        )
        out = clean_output(raw)
        if is_illustrious:
            out, _neg = parse_illustrious(out)
            out = clean_output(out) or clean_output(raw)
        if not out:
            raise RuntimeError("El modelo no devolvió la traducción al inglés.")
        emit_activity(idioma, "translated_es", secs=f"{time.perf_counter() - t0:.1f}")
        emit_activity(idioma, "done")
        return out
    except Exception as e:
        emit_activity(idioma, "error", msg=str(e), level="err")
        raise
    finally:
        if unload_after:
            try:
                emit_activity(idioma, "unloading")
                unload_models(url, model)
                emit_activity(idioma, "unloaded")
            except Exception as e:
                print(f"[LD-PromptWriter] aviso al descargar el modelo: {e}", flush=True)
        else:
            schedule_idle_unload(url, model, idioma, descarga_idle_min)


def generate_prompt(idea, mode, url, model, temperature, max_tokens, seed=0,
                    unload_after=True, extra_instructions="", **kwargs):
    """Generate, then unload the LLM if unload_after (also after an error)."""
    idioma = kwargs.get("idioma", "Español")
    idle_min = kwargs.get("descarga_idle_min", 0)
    cancel_idle_unload()
    set_chat_ttl(idle_min)
    try:
        return _generate_prompt_impl(idea, mode, url, model, temperature, max_tokens,
                                     seed, unload_after, extra_instructions, **kwargs)
    except Exception as e:
        emit_activity(idioma, "error", msg=str(e), level="err")
        raise
    finally:
        if unload_after:
            try:
                emit_activity(idioma, "unloading")
                unload_models(url, model)
                emit_activity(idioma, "unloaded")
            except Exception as e:
                print(f"[LD-PromptWriter] aviso al descargar el modelo: {e}", flush=True)
        else:
            schedule_idle_unload(url, model, idioma, idle_min)



SYS_MODIFY_KREA2 = """You are editing an existing image prompt for Krea 2 (natural English prose).
The user gives you the CURRENT prompt and a CHANGE request.
Rules:
- Apply ONLY the requested change.
- Keep every other word, sentence order, punctuation, names, details and structure VERBATIM.
- Do not improve, rewrite, shorten, expand, re-order or re-style anything that was not asked.
- Do not add a preamble or quotation marks. Output only the full updated prompt.
- If a negative prompt is provided and the change does not affect it, you may optionally append a line
  starting with 'Negative:' repeating it unchanged. If there is no negative, do not invent one.
"""

SYS_MODIFY_ILLUSTRIOUS = """You are editing an existing Danbooru-tag prompt for Illustrious / NoobAI.
The user gives you the CURRENT positive tags, the CURRENT negative tags, and a CHANGE request.
Rules:
- Apply ONLY the requested change (replace, add or remove the relevant tag(s) only).
- Keep every other tag, their order and weighting EXACTLY as they were.
- Do not improve, reshuffle, add quality tags, or change the negative unless the change explicitly says so.
- Output exactly:
Positive: <full updated positive tags>
Negative: <full updated negative tags, unchanged if the edit does not affect them>
No preamble.
"""


def _split_optional_negative(text: str, original_negative: str) -> tuple:
    text = clean_output(text)
    parts = _NEG_SPLIT.split(text, maxsplit=1)
    if len(parts) == 2:
        pos = _POS_LABEL.sub("", parts[0]).strip()
        neg = parts[1].strip()
        return pos, neg or original_negative
    return _POS_LABEL.sub("", text).strip(), original_negative


def modify_prompt(
    prompt,
    negative,
    change,
    mode,
    url,
    model,
    temperature=0.3,
    max_tokens=800,
    seed=0,
    unload_after=True,
    idioma="Español",
    extra_instructions="",
    descarga_idle_min=0,
):
    """Apply a precise edit to an existing prompt. Unloads afterwards if unload_after is on."""
    prompt = str(prompt or "").strip()
    negative = str(negative or "").strip()
    change = str(change or "").strip()
    if not prompt:
        raise RuntimeError(
            "No hay un prompt generado para modificar. Generá uno primero o escribí uno en el recuadro positivo."
            if not is_english(idioma)
            else "There is no generated prompt to edit. Generate one first, or type one in the positive box."
        )
    if not change:
        raise RuntimeError(
            "Escribí qué querés cambiar (por ejemplo el color de pelo)."
            if not is_english(idioma)
            else "Type the change you want (for example the hair color)."
        )
    url = _norm_url(url)
    cancel_idle_unload()
    set_chat_ttl(descarga_idle_min)
    emit_activity(idioma, "connecting")
    try:
        model_id = pick_model(url, model)
        model_id = announce_model_use(url, model_id, idioma) or model_id
        is_illustrious = str(mode).lower().startswith("illustrious")
        want_es = want_spanish_view(idioma)
        system = SYS_MODIFY_ILLUSTRIOUS if is_illustrious else SYS_MODIFY_KREA2
        if is_illustrious:
            user = (
                "CURRENT POSITIVE:\n" + prompt
                + "\n\nCURRENT NEGATIVE:\n" + (negative or "(empty)")
                + "\n\nCHANGE REQUEST:\n" + change
            )
        else:
            user = (
                "CURRENT PROMPT:\n" + prompt
                + "\n\nCURRENT NEGATIVE (optional):\n" + (negative or "(none)")
                + "\n\nCHANGE REQUEST:\n" + change
            )
        extra = str(extra_instructions or "").strip()
        if extra:
            user = user + "\n\nAdditional instructions (do not break the verbatim rule):\n" + extra
        emit_activity(idioma, "modifying")
        t0 = time.perf_counter()
        temp = min(float(temperature if temperature is not None else 0.3), 0.35)
        raw = chat_complete(
            url, model_id,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temp,
            max(int(max_tokens or 800), 800),
            int(seed or 0),
        )
        body, _ignored_es = parse_bilingual(raw)
        vista_es = ""
        if is_illustrious:
            positive, new_neg = parse_illustrious(body)
            if not positive:
                positive = clean_output(body)
            if (not str(new_neg or "").strip()) or (new_neg == ILLUSTRIOUS_NEGATIVE and negative):
                # keep original negative if the model dropped it or substituted the default
                if "negative" not in (raw or "").lower() and "negativo" not in (raw or "").lower():
                    new_neg = negative
            negative = new_neg or negative
        else:
            positive, negative = _split_optional_negative(body, negative)
        if not positive:
            raise RuntimeError(
                "El modelo no devolvió un prompt modificado."
                if not is_english(idioma)
                else "The model did not return an edited prompt."
            )
        secs = f"{time.perf_counter() - t0:.1f}"
        emit_activity(idioma, "modified", secs=secs)
        if want_es:
            vista_es = spanish_view_of(url, model_id, positive, is_illustrious, seed, idioma, max_tokens)
        emit_activity(idioma, "done")
        emit_vista_es(vista_es)
        return positive, negative, vista_es
    except Exception as e:
        emit_activity(idioma, "error", msg=str(e), level="err")
        raise
    finally:
        if unload_after:
            try:
                emit_activity(idioma, "unloading")
                unload_models(url, model)
                emit_activity(idioma, "unloaded")
            except Exception as e:
                print(f"[LD-PromptWriter] aviso al descargar el modelo: {e}", flush=True)
        else:
            schedule_idle_unload(url, model, idioma, descarga_idle_min)


def register_routes() -> None:
    """ComfyUI HTTP route for the 'Probar conexión' button. Safe if PromptServer is absent."""
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception as e:
        print(f"[LD-PromptWriter] no registré la ruta de test: {e}", flush=True)
        return
    inst = getattr(PromptServer, "instance", None)
    if inst is None:
        return
    if getattr(inst, "_ld_promptwriter_routes", False):
        return

    async def ld_promptwriter_test(request):
        raw = request.rel_url.query.get("url", DEFAULT_URL)
        result = test_connection(raw)
        return web.json_response(result)

    async def ld_promptwriter_models(request):
        raw = request.rel_url.query.get("url", DEFAULT_URL)
        result = catalog_models(raw, timeout=3.0)
        return web.json_response(result)

    async def ld_promptwriter_generate(request):
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {"ok": False, "message": "Pedido inválido: no pude leer el JSON."},
                status=400,
            )
        if not isinstance(body, dict):
            body = {}
        def _parse_img_info(info, fallback_filename=None, fallback_sub="", fallback_typ="input"):
            if isinstance(info, dict):
                return (
                    info.get("filename") or info.get("image") or fallback_filename,
                    info.get("subfolder") or fallback_sub or "",
                    info.get("type") or fallback_typ or "input",
                )
            if info:
                return info, fallback_sub, fallback_typ
            return fallback_filename, fallback_sub, fallback_typ

        images = {}
        try:
            for idx in range(1, N_IMAGES + 1):
                key = f"image_{idx}"
                info = body.get(key)
                if idx == 1 and not info:
                    info = body.get("image")
                fn, sub, typ = _parse_img_info(
                    info,
                    body.get("filename") if idx == 1 else None,
                    body.get("subfolder") or "" if idx == 1 else "",
                    body.get("type") or "input" if idx == 1 else "input",
                )
                if fn:
                    images[idx] = load_ref_image(fn, sub, typ)
            extra_kw = {}
            aspects = body.get("aspects") if isinstance(body.get("aspects"), dict) else {}
            extra_kw["aspects"] = aspects
            for idx in range(1, N_IMAGES + 1):
                for k in ASPECT_KEYS:
                    val = body.get(f"img{idx}_{k}")
                    if val is not None:
                        extra_kw[f"img{idx}_{k}"] = val
                desc = body.get(f"desc_imagen_{idx}")
                if desc:
                    extra_kw[f"desc_imagen_{idx}"] = desc
                sig = body.get(f"desc_aspects_{idx}")
                if sig:
                    extra_kw[f"desc_aspects_{idx}"] = sig
            if body.get("num_personas") is not None:
                extra_kw["num_personas"] = body.get("num_personas")
            if body.get("num_personas_custom") is not None:
                extra_kw["num_personas_custom"] = body.get("num_personas_custom")
            if body.get("camara") is not None:
                extra_kw["camara"] = body.get("camara")
            if body.get("modo_ropa") is not None:
                extra_kw["modo_ropa"] = normalize_ropa(body.get("modo_ropa"))
            if body.get("pasadas") is not None:
                extra_kw["pasadas"] = normalize_pasadas(body.get("pasadas"))
            extra_kw["idioma"] = body.get("idioma", "Español")
            if body.get("descarga_idle_min") is not None:
                extra_kw["descarga_idle_min"] = body.get("descarga_idle_min")
            print(
                f"[LD-PromptWriter] /generate con {len(images)} imagen(es): "
                + ", ".join(f"IMAGE {i}" for i in images),
                flush=True,
            )
            for idx, tensor in images.items():
                if idx not in (1, 2, 3, 4):
                    extra_kw[f"image_{idx}"] = tensor
            positive, negative, vista_es = generate_prompt(
                body.get("idea", ""),
                body.get("mode", "Krea2 (natural)"),
                body.get("url", DEFAULT_URL),
                body.get("model", AUTO_MODEL),
                body.get("temperature", 0.7),
                body.get("max_tokens", 600),
                body.get("seed", 0),
                body.get("unload_after", True),
                body.get("extra_instructions", ""),
                image_1=images.get(1),
                image_2=images.get(2),
                image_3=images.get(3),
                image_4=images.get(4),
                usar_imagen_1=body.get("usar_imagen_1", IMAGE_USE_DEFAULT),
                usar_imagen_2=body.get("usar_imagen_2", IMAGE_USE_DEFAULT),
                lora_triggers=body.get("lora_triggers", ""),
                estilo_salida=body.get("estilo_salida", ESTILO_SALIDA_DEFAULT),
                **extra_kw,
            )
            return web.json_response(
                {"ok": True, "positive": positive, "negative": negative, "vista_es": vista_es or ""}
            )
        except Exception as e:
            return web.json_response({"ok": False, "message": str(e)})

    async def ld_promptwriter_describe(request):
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {"ok": False, "message": "Pedido inválido: no pude leer el JSON."},
                status=400,
            )
        if not isinstance(body, dict):
            body = {}
        img = body.get("image") or body.get("image_1") or {}
        if not isinstance(img, dict):
            img = {"filename": img}
        filename = img.get("filename") or img.get("image") or body.get("filename") or ""
        if not filename:
            return web.json_response({"ok": False, "message": "No hay imagen para describir."})
        idioma = body.get("idioma", "Español")
        url = body.get("url", DEFAULT_URL)
        model = body.get("model", AUTO_MODEL)
        idle_min = body.get("descarga_idle_min", 0)
        # Describir never unloads (even if unload_after is on). Keep the same
        # loaded instance for the next Describir / Generar call.
        cancel_idle_unload()
        set_chat_ttl(idle_min)
        try:
            raw_asp = body.get("aspects")
            aspects = None
            if raw_asp:
                if isinstance(raw_asp, str):
                    aspects = [x.strip() for x in raw_asp.split(",") if x.strip()]
                elif isinstance(raw_asp, (list, tuple)):
                    aspects = [str(x).strip() for x in raw_asp if str(x).strip()]
            if aspects:
                image = load_ref_image(
                    filename,
                    img.get("subfolder") or body.get("subfolder") or "",
                    img.get("type") or body.get("type") or "input",
                )
                if not _has_image(image):
                    raise RuntimeError("No pude leer la imagen para describirla.")
                emit_activity(idioma, "connecting")
                model_id = pick_model(url, model)
                model_id = announce_model_use(url, model_id, idioma) or model_id
                vis = _model_is_vision(url, model_id)
                if vis is False:
                    raise RuntimeError(VISION_REQUIRED)
                idx = int(body.get("index") or body.get("n") or 1)
                asp = normalize_aspect_list(aspects)
                asp_lbl = aspect_label_list(asp)
                emit_activity(idioma, "describing", n=idx, aspects=asp_lbl)
                t0 = time.perf_counter()
                text = describe_reference_aspect(
                    url, model_id, image, idx, asp,
                    body.get("temperature", 0.3),
                    body.get("max_tokens", 400),
                    body.get("seed", 0),
                    idioma=idioma,
                )
                emit_activity(idioma, "described", n=idx, secs=f"{time.perf_counter() - t0:.1f}")
                emit_activity(idioma, "done")
                emit_desc_update(idx, text, aspect_signature(asp))
                return web.json_response({"ok": True, "description": text, "aspects": aspect_signature(asp)})
            text = describe_image_info(
                url,
                model,
                filename,
                img.get("subfolder") or body.get("subfolder") or "",
                img.get("type") or body.get("type") or "input",
                body.get("temperature", 0.3),
                body.get("max_tokens", 400),
                body.get("seed", 0),
                idioma,
            )
            return web.json_response({"ok": True, "description": text})
        except Exception as e:
            emit_activity(idioma, "error", msg=str(e), level="err")
            return web.json_response({"ok": False, "message": str(e)})
        finally:
            schedule_idle_unload(url, model, idioma, idle_min)

    async def ld_promptwriter_modify(request):
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {"ok": False, "message": "Pedido inválido: no pude leer el JSON."},
                status=400,
            )
        if not isinstance(body, dict):
            body = {}
        try:
            positive, negative, vista_es = modify_prompt(
                body.get("prompt") or body.get("prompt_generado") or "",
                body.get("negative") or body.get("negativo_generado") or "",
                body.get("change") or body.get("cambios") or "",
                body.get("mode", "Krea2 (natural)"),
                body.get("url", DEFAULT_URL),
                body.get("model", AUTO_MODEL),
                body.get("temperature", 0.3),
                body.get("max_tokens", 800),
                body.get("seed", 0),
                body.get("unload_after", True),
                body.get("idioma", "Español"),
                body.get("extra_instructions", ""),
                body.get("descarga_idle_min", 0),
            )
            return web.json_response({"ok": True, "positive": positive, "negative": negative, "vista_es": vista_es or ""})
        except Exception as e:
            return web.json_response({"ok": False, "message": str(e)})

    async def ld_promptwriter_input_images(request):
        files = list_input_images()
        return web.json_response({"ok": True, "files": files})

    async def ld_promptwriter_translate_es(request):
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {"ok": False, "message": "Pedido inválido: no pude leer el JSON."},
                status=400,
            )
        if not isinstance(body, dict):
            body = {}
        try:
            english = translate_spanish_to_english(
                body.get("text") or body.get("vista_es") or body.get("spanish") or "",
                body.get("mode", "Krea2 (natural)"),
                body.get("url", DEFAULT_URL),
                body.get("model", AUTO_MODEL),
                body.get("temperature", 0.3),
                body.get("max_tokens", 700),
                body.get("seed", 0),
                body.get("idioma", "Español"),
                body.get("extra_instructions", ""),
                False,
                body.get("descarga_idle_min", 0),
            )
            return web.json_response({"ok": True, "positive": english, "english": english})
        except Exception as e:
            return web.json_response({"ok": False, "message": str(e)})

    async def ld_promptwriter_view_es(request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        text = str(body.get("text") or body.get("positive") or "")
        try:
            es = await asyncio.to_thread(
                refresh_spanish_view,
                text,
                body.get("mode", "Krea2 (natural)"),
                body.get("url", DEFAULT_URL),
                body.get("model", AUTO_MODEL),
                body.get("seed", 0),
                body.get("max_tokens", 0),
                body.get("idioma", "Español"),
                bool(body.get("unload_after", False)),
                body.get("descarga_idle_min", 0),
            )
            return web.json_response({"ok": True, "vista_es": es or "", "source": text})
        except Exception as e:
            return web.json_response({"ok": False, "message": str(e), "source": text})

    inst.routes.get("/ld_promptwriter/test")(ld_promptwriter_test)
    inst.routes.get("/ld_promptwriter/models")(ld_promptwriter_models)
    inst.routes.get("/ld_promptwriter/input_images")(ld_promptwriter_input_images)
    inst.routes.post("/ld_promptwriter/generate")(ld_promptwriter_generate)
    inst.routes.post("/ld_promptwriter/describe")(ld_promptwriter_describe)
    inst.routes.post("/ld_promptwriter/modify")(ld_promptwriter_modify)
    inst.routes.post("/ld_promptwriter/translate_es")(ld_promptwriter_translate_es)
    inst.routes.post("/ld_promptwriter/view_es")(ld_promptwriter_view_es)

    async def ld_promptwriter_save(request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        try:
            result = save_displayed_images(
                body.get("images") or [],
                body.get("filename_prefix") or "ComfyUI",
            )
            return web.json_response(result)
        except Exception as exc:
            return web.json_response({"ok": False, "message": str(exc), "saved": []}, status=200)

    inst.routes.post("/ld_promptwriter/save")(ld_promptwriter_save)
    inst._ld_promptwriter_routes = True
    print("[LD-PromptWriter] rutas /ld_promptwriter/test, /models, /generate, /describe, /modify, /save e /input_images registradas", flush=True)


register_routes()



CFG_TYPE = "LD_LMSTUDIO_CFG"


IDIOMA_OPTIONS = ("Español", "English")
MODE_OPTIONS = ("Krea2 (natural)", "Illustrious (tags)")
MODELO_GEN_OPTIONS = ("Krea2", "Illustrious")


def sanitize_combo(value, options, default=None):
    """Coerce a combo widget value to a valid option.

    Hidden/added widgets can shift widgets_values so a combo receives 0 or
    another type. Invalid values fall back to default (or the first option).
    """
    opts = list(options or [])
    if not opts:
        return default
    if default is None:
        default = opts[0]
    if value in opts:
        return value
    if value is None or isinstance(value, bool):
        return default
    text = str(value).strip()
    for opt in opts:
        if text == str(opt) or text.lower() == str(opt).lower():
            return opt
    # Integer index (the classic "idioma got 0" misalignment).
    if isinstance(value, int) and 0 <= value < len(opts):
        return opts[value]
    if text.isdigit():
        idx = int(text)
        if 0 <= idx < len(opts) and text not in [str(o) for o in opts]:
            return opts[idx]
    return default


def pack_config(url, model, mode, temperature, max_tokens, seed, unload_after, extra_instructions="", idioma="Español", descarga_idle_min=0):
    try:
        idle = int(descarga_idle_min or 0)
    except (TypeError, ValueError):
        idle = 0
    mode = sanitize_combo(mode, MODE_OPTIONS, "Krea2 (natural)")
    idioma = sanitize_combo(idioma, IDIOMA_OPTIONS, "Español")
    return {
        "url": url,
        "model": model,
        "mode": mode,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "seed": seed,
        "unload_after": unload_after,
        "extra_instructions": extra_instructions or "",
        "idioma": idioma or "Español",
        "descarga_idle_min": max(0, idle),
    }


def unpack_config(cfg) -> dict:
    if not isinstance(cfg, dict):
        raise RuntimeError("Conectá el nodo LM Studio Config (LD) a la entrada config del Writer.")
    base = pack_config(
        cfg.get("url", DEFAULT_URL),
        cfg.get("model", AUTO_MODEL),
        cfg.get("mode", "Krea2 (natural)"),
        cfg.get("temperature", 0.7),
        cfg.get("max_tokens", 600),
        cfg.get("seed", 0),
        cfg.get("unload_after", True),
        cfg.get("extra_instructions", ""),
        cfg.get("idioma", "Español"),
        cfg.get("descarga_idle_min", 0),
    )
    # Keep bundled images/triggers so the Writer can run from a single config link.
    for key, value in cfg.items():
        if key not in base:
            base[key] = value
    return base


def append_neg_embeddings(negative, embeddings) -> str:
    emb = str(embeddings or "").strip()
    neg = str(negative or "").strip()
    if not emb:
        return neg
    if not neg:
        return emb
    if emb in neg:
        return neg
    if neg.endswith(","):
        return (neg + " " + emb).strip()
    return (neg + ", " + emb).strip()


def config_image_kwargs(cfg) -> dict:
    """Tensors packed into the config bundle by LM Studio Config (LD)."""
    out = {}
    if not isinstance(cfg, dict):
        return out
    bundled = cfg.get("_images") if isinstance(cfg.get("_images"), dict) else {}
    for idx in range(1, N_IMAGES + 1):
        img = bundled.get(idx)
        if img is None:
            img = bundled.get(str(idx))
        if img is None:
            img = cfg.get("image_%s" % idx)
        if _has_image(img):
            out["image_%s" % idx] = img
    return out


def find_linked_writer(prompt, config_id):
    """Locate the Writer whose `config` input comes from this Config node id."""
    if not isinstance(prompt, dict) or config_id is None:
        return None, {}
    cid = str(config_id)
    for nid, node in prompt.items():
        if not isinstance(node, dict):
            continue
        class_type = str(node.get("class_type") or "")
        if class_type not in ("LD_LMStudioPromptWriterV2", "LD_LMStudioPromptWriter"):
            continue
        inputs = node.get("inputs") if isinstance(node.get("inputs"), dict) else {}
        link = inputs.get("config")
        if isinstance(link, (list, tuple)) and len(link) >= 1 and str(link[0]) == cid:
            return str(nid), inputs
    return None, {}


_WRITER_PROMPT_KEYS = (
    "idea",
    "usar_prompt_generado",
    "prompt_generado",
    "negativo_generado",
    "estilo_salida",
    "usar_imagen_1",
    "usar_imagen_2",
    "num_personas",
    "num_personas_custom",
    "camara",
    "modo_ropa",
    "pasadas",
    "lora_triggers",
)


def writer_kwargs_from_inputs(inputs) -> dict:
    out = {}
    if not isinstance(inputs, dict):
        return out
    for key, value in inputs.items():
        if key in _WRITER_PROMPT_KEYS or key.startswith("desc_imagen_") or key.startswith("desc_aspects_") or key.startswith("archivo_imagen_") or key.startswith("img"):
            out[key] = value
    return out


def writer_change_fingerprint(inputs) -> str:
    if not isinstance(inputs, dict):
        return ""
    keys = sorted(writer_kwargs_from_inputs(inputs).keys())
    return "|".join("%s=%s" % (key, inputs.get(key)) for key in keys)


def resolve_config_prompts(cfg, writer_inputs, image_kwargs, lora_triggers, neg_embeddings):
    """Positive/negative for Config outputs: cached Writer widgets, or a live LLM call."""
    cfg = cfg or {}
    writer_inputs = writer_inputs or {}
    is_illustrious = str(cfg.get("mode", "")).lower().startswith("illustrious")
    if str(lora_triggers or "").strip():
        triggers_text = lora_triggers
    else:
        triggers_text = writer_inputs.get("lora_triggers", "") or ""
    triggers, _removed = effective_triggers(
        normalize_triggers(triggers_text),
        writer_inputs.get("modo_ropa", ROPA_AUTO),
        ropa_image_indices(None, **writer_inputs),
    )
    idea = writer_inputs.get("idea", "")
    usar = writer_inputs.get("usar_prompt_generado", True)
    if isinstance(usar, str):
        usar = usar.strip().lower() not in ("false", "0", "no")
    cached = str(writer_inputs.get("prompt_generado") or "").strip()
    negativo = str(writer_inputs.get("negativo_generado") or "")
    idioma = cfg.get("idioma", "Español")

    extra_kw = writer_kwargs_from_inputs(writer_inputs)
    for drop in (
        "idea",
        "lora_triggers",
        "prompt_generado",
        "negativo_generado",
        "usar_prompt_generado",
        "image",
        "config",
    ):
        extra_kw.pop(drop, None)
    for idx in range(1, N_IMAGES + 1):
        extra_kw.pop("image_%s" % idx, None)

    # The positive box always wins when it has text, regardless of the
    # legacy usar_prompt_generado flag. The queued prompt must carry the
    # current textarea value (see JS graphToPrompt / serializeValue hook).
    if cached:
        emit_activity(idioma, "cached")
        positive = ensure_triggers(cached, triggers, is_illustrious)
        return positive, append_neg_embeddings(negativo, neg_embeddings)

    has_images = any(_has_image(v) for v in (image_kwargs or {}).values())
    has_archivo = any(
        str(extra_kw.get("archivo_imagen_%s" % i) or "").strip()
        for i in range(1, N_IMAGES + 1)
    )
    if not str(idea or "").strip() and not has_images and not has_archivo:
        return "", append_neg_embeddings("", neg_embeddings)

    positive, negative, vista_es = generate_prompt(
        idea,
        cfg.get("mode", "Krea2 (natural)"),
        cfg.get("url", DEFAULT_URL),
        cfg.get("model", AUTO_MODEL),
        cfg.get("temperature", 0.7),
        cfg.get("max_tokens", 600),
        cfg.get("seed", 0),
        cfg.get("unload_after", True),
        cfg.get("extra_instructions", ""),
        lora_triggers=triggers_text or "",
        idioma=idioma,
        descarga_idle_min=cfg.get("descarga_idle_min", 0),
        **(image_kwargs or {}),
        **extra_kw,
    )
    return positive, append_neg_embeddings(negative, neg_embeddings)


class LD_LMStudioConfig:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": (
                    "STRING",
                    {
                        "default": DEFAULT_URL,
                        "tooltip": "URL del servidor local de LM Studio.",
                    },
                ),
                "model": (
                    combo_model_choices(timeout=1.5),
                    {
                        "default": AUTO_MODEL,
                        "tooltip": "Modelo de LM Studio. '(auto: el cargado)' usa el que ya está en memoria. Si elegís uno que no está cargado, LM Studio lo carga al generar.",
                    },
                ),
                "mode": (
                    ["Krea2 (natural)", "Illustrious (tags)"],
                    {"tooltip": "Krea2: prosa en inglés. Illustrious: tags estilo Danbooru."},
                ),
                "temperature": (
                    "FLOAT",
                    {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05},
                ),
                "max_tokens": (
                    "INT",
                    {"default": 2048, "min": 64, "max": 8192, "step": 1},
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Cambia la seed para pedir otra versión del prompt.",
                    },
                ),
                "unload_after": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Descarga el modelo al terminar Generar o al ejecutar el workflow. Describir nunca descarga.",
                    },
                ),
                "extra_instructions": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Indicaciones extra para el LLM (estilo, encuadre, etc.).",
                    },
                ),
                "idioma": (
                    ["Español", "English"],
                    {
                        "default": "Español",
                        "tooltip": "Idioma de la interfaz y de las descripciones de imagen. Los prompts finales siguen en inglés.",
                    },
                ),
                "descarga_idle_min": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 240,
                        "step": 1,
                        "tooltip": "Minutos sin actividad para descargar el modelo. 0 = desactivado. Describir nunca descarga al terminar.",
                    },
                ),
            },
            "optional": {
                "image_1": ("IMAGE", {"tooltip": "Referencia 1 para el Writer (opcional)."}),
                "image_2": ("IMAGE", {"tooltip": "Referencia 2 para el Writer (opcional)."}),
                "image_3": ("IMAGE", {"tooltip": "Referencia 3 para el Writer (opcional)."}),
                "image_4": ("IMAGE", {"tooltip": "Referencia 4 para el Writer (opcional)."}),
                "image_5": ("IMAGE", {"tooltip": "Referencia 5 para el Writer (opcional)."}),
                "image_6": ("IMAGE", {"tooltip": "Referencia 6 para el Writer (opcional)."}),
                "image_7": ("IMAGE", {"tooltip": "Referencia 7 para el Writer (opcional)."}),
                "image_8": ("IMAGE", {"tooltip": "Referencia 8 para el Writer (opcional)."}),
                "lora_triggers": (
                    "STRING",
                    {
                        "default": "",
                        "forceInput": True,
                        "tooltip": "Salida trigger_words del Lora Loader. El Writer los incluye en el prompt.",
                    },
                ),
                "neg_embeddings": (
                    "STRING",
                    {
                        "default": "",
                        "forceInput": True,
                        "lazy": True,
                        "tooltip": "Salida de Embeddings negativos (LD). Se agrega al prompt negativo (Illustrious).",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = (CFG_TYPE, "STRING", "STRING")
    RETURN_NAMES = ("config", "positive", "negative")
    FUNCTION = "build"
    CATEGORY = "LD/Prompt"
    DESCRIPTION = (
        "Ajustes de LM Studio. Las imágenes, trigger words y embeddings se conectan acá. "
        "La salida config va al Writer (un solo cable). positive/negative salen de este nodo."
    )

    def check_lazy_status(self, mode="Krea2 (natural)", **kwargs):
        # When Krea2 is selected the Illustrious embeddings node is muted; do not evaluate it.
        if str(mode or "").lower().startswith("illustrious"):
            return ["neg_embeddings"]
        return []

    @classmethod
    def VALIDATE_INPUTS(cls, model=None, idioma=None, mode=None, **kwargs):
        # Named combo args skip execution.py's "value not in list" check.
        # Invalid idioma/mode are coerced in pack_config / build (e.g. 0 → Español).
        if model is not None and not isinstance(model, (str, int)):
            return "modelo inválido: %r" % (model,)
        return True

    @classmethod
    def IS_CHANGED(
        cls,
        url,
        model,
        mode,
        temperature,
        max_tokens,
        seed,
        unload_after,
        extra_instructions="",
        idioma="Español",
        descarga_idle_min=0,
        lora_triggers="",
        neg_embeddings="",
        prompt=None,
        unique_id=None,
        **kwargs,
    ):
        parts = [
            _norm_url(str(url)),
            "" if is_auto_model(model) else strip_model_label(str(model or "")),
            str(mode),
            "%.4f" % float(temperature),
            str(int(max_tokens)),
            str(int(seed)),
            str(bool(unload_after)),
            str(extra_instructions or ""),
            str(idioma or "Español"),
            str(int(descarga_idle_min or 0)),
            str(lora_triggers or ""),
            str(neg_embeddings or ""),
        ]
        for idx in range(1, N_IMAGES + 1):
            img = kwargs.get("image_%s" % idx)
            parts.append("" if img is None else _image_fingerprint(img))
        if kwargs.get("image") is not None:
            parts.append(_image_fingerprint(kwargs.get("image")))
        _nid, inputs = find_linked_writer(prompt, unique_id)
        parts.append(writer_change_fingerprint(inputs))
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def build(
        self,
        url,
        model,
        mode,
        temperature,
        max_tokens,
        seed,
        unload_after,
        extra_instructions="",
        idioma="Español",
        descarga_idle_min=0,
        lora_triggers="",
        neg_embeddings="",
        prompt=None,
        unique_id=None,
        **kwargs,
    ):
        cfg = pack_config(
            url, model, mode, temperature, max_tokens, seed, unload_after,
            extra_instructions, idioma, descarga_idle_min,
        )
        images = {}
        for idx in range(1, N_IMAGES + 1):
            img = kwargs.get("image_%s" % idx)
            if idx == 1 and not _has_image(img):
                img = kwargs.get("image")
            images[idx] = img
        cfg["_images"] = images
        cfg["lora_triggers"] = lora_triggers or ""
        cfg["neg_embeddings"] = neg_embeddings or ""
        _nid, writer_inputs = find_linked_writer(prompt, unique_id)
        image_kwargs = dict(("image_%s" % i, images[i]) for i in images)
        positive, negative = resolve_config_prompts(
            cfg, writer_inputs, image_kwargs, lora_triggers, neg_embeddings
        )
        return (cfg, positive, negative)


class LD_LMStudioPromptWriterV2:
    @classmethod
    def INPUT_TYPES(cls):
        types = {
            "required": {
                "config": (CFG_TYPE, {"tooltip": "Salida del nodo LM Studio Config (LD)."}),
                "idea": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "La idea de la imagen (puede estar en español). Si está vacía, se describe la imagen de referencia.",
                    },
                ),
                "usar_imagen_1": (
                    list(IMAGE_USE_OPTIONS),
                    {
                        "default": IMAGE_USE_DEFAULT,
                        "tooltip": "Qué tomar de la imagen 1: todo, acción/pose, persona, fondo o estilo/ropa.",
                    },
                ),
                "usar_imagen_2": (
                    list(IMAGE_USE_OPTIONS),
                    {
                        "default": IMAGE_USE_DEFAULT,
                        "tooltip": "Qué tomar de la imagen 2: todo, acción/pose, persona, fondo o estilo/ropa.",
                    },
                ),
                "usar_prompt_generado": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Se conserva por compatibilidad. Si el recuadro positivo tiene texto, se usa tal cual y no se llama al LLM; si está vacío, se genera. Los trigger words de LoRA se agregan si faltan.",
                    },
                ),
                "prompt_generado": (
                    "STRING",
                    {"multiline": True, "default": "", "tooltip": "Prompt positivo. Editable."},
                ),
                "negativo_generado": (
                    "STRING",
                    {"multiline": True, "default": "", "tooltip": "Prompt negativo. Editable."},
                ),
                "estilo_salida": (
                    list(ESTILO_SALIDA_OPTIONS),
                    {
                        "default": ESTILO_SALIDA_DEFAULT,
                        "tooltip": "Estilo del prompt final. Las fotos de referencia pueden ser de otro estilo; se ignora su arte y se escribe en este estilo.",
                    },
                ),
            },
            "optional": {
                "img1_accion": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar acción / pose de la imagen 1. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img1_persona": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar persona de la imagen 1. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img1_fondo": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar fondo / escena de la imagen 1. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img1_estilo": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar estilo de la imagen 1. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img1_ropa": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar ropa de la imagen 1. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "desc_imagen_1": (
                    "STRING",
                    {"multiline": True, "default": "", "tooltip": "Descripción informativa de la imagen 1 (no se usa al generar)."},
                ),
                "img2_accion": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar acción / pose de la imagen 2. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img2_persona": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar persona de la imagen 2. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img2_fondo": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar fondo / escena de la imagen 2. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img2_estilo": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar estilo de la imagen 2. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img2_ropa": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar ropa de la imagen 2. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "desc_imagen_2": (
                    "STRING",
                    {"multiline": True, "default": "", "tooltip": "Descripción informativa de la imagen 2 (no se usa al generar)."},
                ),
                "img3_accion": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar acción / pose de la imagen 3. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img3_persona": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar persona de la imagen 3. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img3_fondo": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar fondo / escena de la imagen 3. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img3_estilo": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar estilo de la imagen 3. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img3_ropa": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar ropa de la imagen 3. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "desc_imagen_3": (
                    "STRING",
                    {"multiline": True, "default": "", "tooltip": "Descripción informativa de la imagen 3 (no se usa al generar)."},
                ),
                "img4_accion": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar acción / pose de la imagen 4. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img4_persona": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar persona de la imagen 4. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img4_fondo": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar fondo / escena de la imagen 4. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img4_estilo": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar estilo de la imagen 4. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "img4_ropa": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Tomar ropa de la imagen 4. Si no hay ningún interruptor activo en esa imagen, se usan todos los aspectos (todo).",
                    },
                ),
                "desc_imagen_4": (
                    "STRING",
                    {"multiline": True, "default": "", "tooltip": "Descripción informativa de la imagen 4 (no se usa al generar)."},
                ),
                "archivo_imagen_1": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Archivo de la carpeta input para la imagen 1. Si image_1 está conectada, esa entrada gana.",
                    },
                ),
                "archivo_imagen_2": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Archivo de la carpeta input para la imagen 2. Si image_2 está conectada, esa entrada gana.",
                    },
                ),
                "archivo_imagen_3": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Archivo de la carpeta input para la imagen 3. Si image_3 está conectada, esa entrada gana.",
                    },
                ),
                "archivo_imagen_4": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Archivo de la carpeta input para la imagen 4. Si image_4 está conectada, esa entrada gana.",
                    },
                ),
                "num_personas": (
                    list(PERSONAS_OPTIONS),
                    {
                        "default": "1",
                        "tooltip": "Cuántas personas debe tener la imagen. Auto deja que el LLM decida. Personalizado usa el número de al lado. No hace falta una imagen por persona.",
                    },
                ),
                "camara": (
                    list(CAMARA_OPTIONS),
                    {
                        "default": CAMARA_AUTO,
                        "tooltip": "Cámara / encuadre del prompt. Si una imagen tiene el interruptor Cámara / POV, esa gana.",
                    },
                ),
                "img1_camara": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "Tomar cámara / POV / encuadre de la imagen 1."},
                ),
                "img2_camara": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "Tomar cámara / POV / encuadre de la imagen 2."},
                ),
                "img3_camara": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "Tomar cámara / POV / encuadre de la imagen 3."},
                ),
                "img4_camara": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "Tomar cámara / POV / encuadre de la imagen 4."},
                ),
                "img1_pose": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "Tomar la pose (cuerpo, manos, mirada) de la imagen 1."},
                ),
                "img2_pose": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "Tomar la pose (cuerpo, manos, mirada) de la imagen 2."},
                ),
                "img3_pose": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "Tomar la pose (cuerpo, manos, mirada) de la imagen 3."},
                ),
                "img4_pose": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "Tomar la pose (cuerpo, manos, mirada) de la imagen 4."},
                ),
            },
        }
        opt = types["optional"]
        for idx in range(5, N_IMAGES + 1):
            opt[f"archivo_imagen_{idx}"] = (
                "STRING",
                {
                    "default": "",
                    "tooltip": f"Archivo de la carpeta input para la imagen {idx}. Si image_{idx} está conectada, esa entrada gana.",
                },
            )
            opt[f"desc_imagen_{idx}"] = (
                "STRING",
                {"multiline": True, "default": "", "tooltip": f"Descripción informativa de la imagen {idx} (no se usa al generar)."},
            )
            for key in LEGACY_ASPECT_KEYS:
                label = ASPECT_LABELS.get(key, key)
                opt[f"img{idx}_{key}"] = (
                    "BOOLEAN",
                    {"default": False, "tooltip": f"Tomar {label} de la imagen {idx}."},
                )
        opt["num_personas_custom"] = (
            "INT",
            {
                "default": 1,
                "min": 1,
                "max": 99,
                "step": 1,
                "tooltip": "Número de personas cuando el selector está en Personalizado.",
            },
        )
        opt["ocultar_ajustes"] = (
            "BOOLEAN",
            {"default": False, "tooltip": "Ocultar la sección superior (estilo, idea, cámara)."},
        )
        opt["ocultar_imagenes"] = (
            "BOOLEAN",
            {"default": False, "tooltip": "Ocultar la sección de imágenes de referencia."},
        )
        # Last on purpose: older workflows have fewer widgets_values and keep the default.
        opt["modo_ropa"] = (
            list(ROPA_OPTIONS),
            {
                "default": ROPA_AUTO,
                "tooltip": "Ropa: LoRA (la ropa que indican los triggers del LoRA; sin triggers decide el LLM), Foto (gana la ropa de la imagen con Ropa activado), Desnudo (sin ropa). 'Automático' de 1.1.2 se lee como LoRA.",
            },
        )
        # 1.1.3 chips, appended after everything so saved widgets_values don't shift.
        for idx in range(1, N_IMAGES + 1):
            for key in NEW_ASPECT_KEYS:
                label = ASPECT_LABELS.get(key, key)
                opt[f"img{idx}_{key}"] = (
                    "BOOLEAN",
                    {"default": False, "tooltip": f"Tomar {label} de la imagen {idx}."},
                )
        opt["pasadas"] = (
            list(PASADAS_OPTIONS),
            {
                "default": PASADAS_1,
                "tooltip": "1 pasada: un prompt. 2 pasadas: después del prompt, una segunda llamada lo revisa con todas las especificaciones y lo corrige o mejora (más lento).",
            },
        )
        return types

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "write"
    CATEGORY = "LD/Prompt"
    OUTPUT_NODE = False

    @classmethod
    def VALIDATE_INPUTS(
        cls,
        usar_imagen_1=None,
        usar_imagen_2=None,
        estilo_salida=None,
        num_personas=None,
        camara=None,
        modo_ropa=None,
        pasadas=None,
        **kwargs,
    ):
        return True

    @classmethod
    def IS_CHANGED(
        cls,
        config,
        idea,
        usar_prompt_generado=True,
        prompt_generado="",
        negativo_generado="",
        image=None,
        image_1=None,
        image_2=None,
        image_3=None,
        image_4=None,
        usar_imagen_1="todo",
        usar_imagen_2="todo",
        lora_triggers="",
        estilo_salida="(como la referencia)",
        **kwargs,
    ):
        use_box = bool(str(prompt_generado or "").strip())
        cfg = config if isinstance(config, dict) else {}
        refs = collect_ref_images(
            image, image_1, image_2, image_3, image_4,
            usar_imagen_1, usar_imagen_2, estilo_salida, **kwargs,
        )
        parts = [
            str(cfg),
            str(idea),
            str(bool(usar_prompt_generado)),
            str(prompt_generado or ""),
            str(negativo_generado or ""),
            normalize_image_use(usar_imagen_1),
            normalize_image_use(usar_imagen_2),
            ",".join(normalize_triggers(lora_triggers)),
            str(estilo_salida or ESTILO_SALIDA_DEFAULT),
            str(parse_personas(kwargs.get("num_personas", "1"), kwargs.get("num_personas_custom", 1))),
            str(kwargs.get("camara") or CAMARA_AUTO),
            normalize_ropa(kwargs.get("modo_ropa")),
            normalize_pasadas(kwargs.get("pasadas")),
        ]
        for idx in range(1, N_IMAGES + 1):
            parts.append(archivo_fingerprint(kwargs.get(f"archivo_imagen_{idx}")))
            for key in ASPECT_KEYS:
                parts.append(str(bool(kwargs.get(f"img{idx}_{key}"))))
        if refs and not use_box:
            for _idx, tensor, use in refs:
                parts.append(use)
                parts.append(_image_fingerprint(tensor))
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def write(
        self,
        config,
        idea,
        usar_prompt_generado=True,
        prompt_generado="",
        negativo_generado="",
        image=None,
        image_1=None,
        image_2=None,
        image_3=None,
        image_4=None,
        usar_imagen_1="todo",
        usar_imagen_2="todo",
        lora_triggers="",
        estilo_salida="(como la referencia)",
        **kwargs,
    ):
        cfg = unpack_config(config) if config is not None else {}
        usar_imagen_1 = sanitize_combo(usar_imagen_1, IMAGE_USE_OPTIONS, IMAGE_USE_DEFAULT)
        usar_imagen_2 = sanitize_combo(usar_imagen_2, IMAGE_USE_OPTIONS, IMAGE_USE_DEFAULT)
        estilo_salida = sanitize_combo(estilo_salida, ESTILO_SALIDA_OPTIONS, ESTILO_SALIDA_DEFAULT)
        if "num_personas" in kwargs:
            kwargs["num_personas"] = sanitize_combo(kwargs.get("num_personas"), PERSONAS_OPTIONS, "1")
        if "camara" in kwargs:
            kwargs["camara"] = sanitize_combo(kwargs.get("camara"), CAMARA_OPTIONS, CAMARA_AUTO)
        kwargs["modo_ropa"] = normalize_ropa(kwargs.get("modo_ropa"))
        kwargs["pasadas"] = normalize_pasadas(kwargs.get("pasadas"))
        bundled = config_image_kwargs(cfg)
        if not str(lora_triggers or "").strip():
            lora_triggers = cfg.get("lora_triggers") or ""
        if not _has_image(image_1):
            image_1 = bundled.get("image_1") or image
        if not _has_image(image_2):
            image_2 = bundled.get("image_2")
        if not _has_image(image_3):
            image_3 = bundled.get("image_3")
        if not _has_image(image_4):
            image_4 = bundled.get("image_4")
        for idx in range(5, N_IMAGES + 1):
            key = "image_%s" % idx
            if not _has_image(kwargs.get(key)):
                kwargs[key] = bundled.get(key)
        is_illustrious = str(cfg.get("mode", "")).lower().startswith("illustrious")
        triggers, _removed = effective_triggers(
            normalize_triggers(lora_triggers),
            kwargs.get("modo_ropa", ROPA_AUTO),
            ropa_image_indices(None, image_1=image_1, image_2=image_2, image_3=image_3, image_4=image_4, **kwargs),
        )
        cached = str(prompt_generado or "").strip()
        if cached:
            emit_activity(cfg.get("idioma", "Español"), "cached")
            positive = ensure_triggers(cached, triggers, is_illustrious)
            negative = append_neg_embeddings(negativo_generado, cfg.get("neg_embeddings"))
            ui_lines = [positive]
            if negative.strip():
                ui_lines.extend(["--- negative ---", negative])
            return {
                "ui": {
                    "text": ui_lines,
                    "prompt_generado": [positive],
                    "negativo_generado": [negative],
                },
                "result": (),
            }

        positive, negative, vista_es = generate_prompt(
            idea,
            cfg.get("mode", "Krea2 (natural)"),
            cfg.get("url", DEFAULT_URL),
            cfg.get("model", AUTO_MODEL),
            cfg.get("temperature", 0.7),
            cfg.get("max_tokens", 600),
            cfg.get("seed", 0),
            cfg.get("unload_after", True),
            cfg.get("extra_instructions", ""),
            image=image,
            image_1=image_1,
            image_2=image_2,
            image_3=image_3,
            image_4=image_4,
            usar_imagen_1=usar_imagen_1,
            usar_imagen_2=usar_imagen_2,
            lora_triggers=lora_triggers,
            estilo_salida=estilo_salida,
            idioma=cfg.get("idioma", "Español"),
            descarga_idle_min=cfg.get("descarga_idle_min", 0),
            **kwargs,
        )
        negative = append_neg_embeddings(negative, cfg.get("neg_embeddings"))
        ui_lines = [positive]
        if negative:
            ui_lines.extend(["--- negative ---", negative])
        return {
            "ui": {
                "text": ui_lines,
                "prompt_generado": [positive],
                "negativo_generado": [negative],
                "vista_es": [vista_es or ""],
            },
            "result": (),
        }



PROPORCIONES = ("1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "4:5", "5:4", "21:9", "9:21", "1:2", "2:1", "3:5", "5:3")
MEGAPIXELES = ("0.25 MP", "0.5 MP", "0.75 MP", "1.0 MP", "1.08 MP", "1.25 MP", "1.3 MP", "1.5 MP", "1.75 MP", "2.0 MP", "2.25 MP", "2.5 MP", "3.0 MP", "3.5 MP", "4.0 MP")
_RATIO_WH = {
    "1:1": (1, 1),
    "2:3": (2, 3),
    "3:2": (3, 2),
    "3:4": (3, 4),
    "4:3": (4, 3),
    "9:16": (9, 16),
    "16:9": (16, 9),
    "4:5": (4, 5),
    "5:4": (5, 4),
    "21:9": (21, 9),
    "9:21": (9, 21),
    "1:2": (1, 2),
    "2:1": (2, 1),
    "3:5": (3, 5),
    "5:3": (5, 3),
}
_MP_VALUE = {
    "0.25 MP": 0.25,
    "0.5 MP": 0.5,
    "0.75 MP": 0.75,
    "1.0 MP": 1.0,
    "1.08 MP": 1.08,
    "1.25 MP": 1.25,
    "1.3 MP": 1.3,
    "1.5 MP": 1.5,
    "1.75 MP": 1.75,
    "2.0 MP": 2.0,
    "2.25 MP": 2.25,
    "2.5 MP": 2.5,
    "3.0 MP": 3.0,
    "3.5 MP": 3.5,
    "4.0 MP": 4.0,
}


def parse_mp(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value or "1.08").replace(",", ".")
    for ch in ("MP", "mp", " "):
        s = s.replace(ch, "")
    try:
        return float(s)
    except ValueError:
        return 1.08


def compute_size(proporcion: str, megapixeles, intercambiar: bool = False) -> tuple:
    """Width, height snapped to multiples of 16. Default 2:3 @ 1.08 MP → 864×1248."""
    ratio = str(proporcion or "2:3").strip()
    if ratio not in _RATIO_WH:
        ratio = "2:3"
    rw, rh = _RATIO_WH[ratio]
    if intercambiar:
        rw, rh = rh, rw
    mp = parse_mp(megapixeles)
    # User's current Krea2 latent: exact 864×1248.
    if ratio == "2:3" and not intercambiar and abs(mp - 1.08) < 0.02:
        return 864, 1248
    if ratio == "3:2" and intercambiar and abs(mp - 1.08) < 0.02:
        return 864, 1248
    area = max(0.1, mp) * 1_000_000.0
    height = (area * rh / rw) ** 0.5
    width = height * rw / rh
    w = max(16, int(round(width / 16.0) * 16))
    h = max(16, int(round(height / 16.0) * 16))
    return w, h


class LD_Tamano:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "proporcion": (list(PROPORCIONES), {"default": "2:3", "tooltip": "Relación de aspecto."}),
                "megapixeles": (list(MEGAPIXELES), {"default": "1.08 MP", "tooltip": "Tamaño aproximado en megapíxeles."}),
                "intercambiar": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "Invierte ancho y alto (apaisado ↔ retrato)."},
                ),
                "batch": ("INT", {"default": 1, "min": 1, "max": 64, "tooltip": "Cantidad de latents."}),
                "resultado": (
                    "STRING",
                    {"default": "864 × 1248", "tooltip": "Tamaño resultante (se calcula solo)."},
                ),
            }
        }

    RETURN_TYPES = ("LATENT", "INT", "INT")
    RETURN_NAMES = ("latent", "width", "height")
    FUNCTION = "build"
    CATEGORY = "LD/Prompt"
    DESCRIPTION = "Elige proporción y megapíxeles; genera un latent vacío (múltiplos de 16)."

    @classmethod
    def VALIDATE_INPUTS(cls, proporcion=None, megapixeles=None, **kwargs):
        return True

    @classmethod
    def IS_CHANGED(cls, proporcion, megapixeles, intercambiar=False, batch=1, resultado=""):
        proporcion = sanitize_combo(proporcion, PROPORCIONES, "2:3")
        megapixeles = sanitize_combo(megapixeles, MEGAPIXELES, "1.08 MP")
        w, h = compute_size(proporcion, megapixeles, intercambiar)
        return "%sx%sx%s" % (w, h, int(batch))

    def build(self, proporcion, megapixeles, intercambiar=False, batch=1, resultado=""):
        proporcion = sanitize_combo(proporcion, PROPORCIONES, "2:3")
        megapixeles = sanitize_combo(megapixeles, MEGAPIXELES, "1.08 MP")
        w, h = compute_size(proporcion, megapixeles, intercambiar)
        label = f"{w} × {h}"
        try:
            import torch
            import comfy.model_management as mm
            samples = torch.zeros(
                [int(batch), 4, h // 8, w // 8],
                device=mm.intermediate_device(),
                dtype=mm.intermediate_dtype(),
            )
        except Exception:
            samples = None
        latent = {"samples": samples, "downscale_ratio_spacial": 8}
        return {
            "ui": {"text": [label], "resultado": [label]},
            "result": (latent, w, h),
        }





class LD_ModeloGen:
    """Toggle between the Krea2 and Illustrious generation branches.

    Also switches MODEL/CLIP (lazy) so a single Lora Loader can serve both branches.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "modelo": (
                    ["Krea2", "Illustrious"],
                    {
                        "default": "Krea2",
                        "tooltip": "Motor de generación. En la interfaz son dos interruptores excluyentes.",
                    },
                ),
                "idioma": (
                    ["Español", "English"],
                    {
                        "default": "Español",
                        "tooltip": "Idioma de la interfaz, las descripciones y las notas. Los prompts finales siguen en inglés.",
                    },
                ),
            },
            "optional": {
                "model_krea2": ("MODEL", {"lazy": True, "tooltip": "Modelo de la rama Krea2 (UNET)."}),
                "clip_krea2": ("CLIP", {"lazy": True, "tooltip": "CLIP de la rama Krea2."}),
                "model_illustrious": ("MODEL", {"lazy": True, "tooltip": "Modelo de la rama Illustrious (checkpoint)."}),
                "clip_illustrious": ("CLIP", {"lazy": True, "tooltip": "CLIP de la rama Illustrious (checkpoint)."}),
            },
        }

    RETURN_TYPES = ("STRING", "MODEL", "CLIP")
    RETURN_NAMES = ("modelo", "model", "clip")
    FUNCTION = "pick"
    CATEGORY = "LD/Prompt"
    DESCRIPTION = (
        "Selector Krea2 / Illustrious (interruptores). Silencia la rama que no se usa "
        "y entrega el MODEL/CLIP activo a un único Lora Loader."
    )

    @classmethod
    def VALIDATE_INPUTS(cls, modelo=None, idioma=None, **kwargs):
        return True

    def check_lazy_status(self, modelo="Krea2", idioma="Español", model_krea2=None, clip_krea2=None,
                          model_illustrious=None, clip_illustrious=None):
        modelo = sanitize_combo(modelo, MODELO_GEN_OPTIONS, "Krea2")
        want = "Illustrious" if str(modelo or "").lower().startswith("illust") else "Krea2"
        if want == "Illustrious":
            return ["model_illustrious", "clip_illustrious"]
        return ["model_krea2", "clip_krea2"]

    def pick(self, modelo, idioma="Español", model_krea2=None, clip_krea2=None,
             model_illustrious=None, clip_illustrious=None):
        modelo = sanitize_combo(modelo, MODELO_GEN_OPTIONS, "Krea2")
        idioma = sanitize_combo(idioma, IDIOMA_OPTIONS, "Español")
        is_il = str(modelo or "").lower().startswith("illust")
        model = model_illustrious if is_il else model_krea2
        clip = clip_illustrious if is_il else clip_krea2
        return (str(modelo or "Krea2"), model, clip)




def list_embedding_files() -> list:
    """Filenames in ComfyUI/models/embeddings (and any mapped embeddings folders)."""
    names = []
    try:
        import folder_paths
        names = list(folder_paths.get_filename_list("embeddings") or [])
    except Exception:
        names = []
    if not names:
        roots = []
        try:
            import folder_paths
            roots = list(folder_paths.get_folder_paths("embeddings") or [])
        except Exception:
            pass
        for root in roots:
            if not root or not os.path.isdir(root):
                continue
            try:
                for fn in os.listdir(root):
                    if fn.lower().endswith((".pt", ".safetensors", ".bin", ".pth")):
                        names.append(fn)
            except OSError:
                continue
    seen = set()
    out = []
    for n in names:
        key = str(n).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    out.sort(key=lambda s: s.lower())
    return out


def embedding_token(name, weight=1.0) -> str:
    stem = os.path.splitext(os.path.basename(str(name or "")))[0].strip()
    if not stem or stem.lower() in ("(ninguno)", "ninguno", "(none)", "none"):
        return ""
    try:
        w = float(weight)
    except (TypeError, ValueError):
        w = 1.0
    if abs(w - 1.0) < 0.001:
        return f"embedding:{stem}"
    ws = f"{w:.3f}".rstrip("0").rstrip(".")
    return f"(embedding:{stem}:{ws})"


def parse_embedding_entries(text) -> list:
    raw = str(text or "").replace(";", ",")
    parts = []
    for line in raw.splitlines():
        parts.extend(p.strip() for p in line.split(",") if p.strip())
    out = []
    seen = set()
    for item in parts:
        if item.lower() in ("(ninguno)", "ninguno", "(none)", "none"):
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


class LD_EmbeddingsNegativos:
    """Lista embeddings de models/embeddings y los agrega al negativo de Illustrious."""

    @classmethod
    def INPUT_TYPES(cls):
        files = list_embedding_files() or ["(ninguno)"]
        return {
            "required": {
                "embedding": (
                    files,
                    {
                        "default": files[0],
                        "tooltip": "Embedding de ComfyUI/models/embeddings. Pulsá ➕ Agregar para sumarlo a la lista.",
                    },
                ),
                "peso": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": -5.0,
                        "max": 5.0,
                        "step": 0.05,
                        "tooltip": "Peso opcional. 1.0 se omite en el texto.",
                    },
                ),
                "lista": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Embeddings negativos, uno por línea o separados por coma. Formato: embedding:nombre o (embedding:nombre:peso).",
                    },
                ),
            },
            "optional": {
                "negativo_base": (
                    "STRING",
                    {
                        "forceInput": True,
                        "tooltip": "Prompt negativo (salida negative del Writer). Se concatena y los embeddings van al final.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("negative",)
    FUNCTION = "build"
    CATEGORY = "LD/Prompt"
    DESCRIPTION = (
        "Embeddings para el negativo de Illustrious. Los archivos van en ComfyUI/models/embeddings. "
        "Conectá la salida a neg_embeddings del Config (o negativo_base si usás un workflow viejo)."
    )

    @classmethod
    def VALIDATE_INPUTS(cls, embedding=None, **kwargs):
        # The embeddings folder list changes; never fail the queue on a stale name.
        return True

    @classmethod
    def IS_CHANGED(cls, embedding="(ninguno)", peso=1.0, lista="", negativo_base=""):
        tokens = parse_embedding_entries(lista)
        return hashlib.sha256(
            f"{','.join(tokens)}|{negativo_base or ''}".encode("utf-8")
        ).hexdigest()

    def build(self, embedding="(ninguno)", peso=1.0, lista="", negativo_base=""):
        tokens = parse_embedding_entries(lista)
        added = ", ".join(tokens)
        base = str(negativo_base or "").strip().rstrip(",")
        if base and added:
            out = f"{base}, {added}"
        else:
            out = base or added
        return {
            "ui": {"text": [out or ""]},
            "result": (out,),
        }



def _dir_for_type(typ):
    typ = str(typ or "output").lower()
    try:
        import folder_paths
        if typ == "temp":
            return folder_paths.get_temp_directory()
        if typ == "input":
            return folder_paths.get_input_directory()
        return folder_paths.get_output_directory()
    except Exception:
        return os.getcwd()


def safe_existing_image_path(filename, subfolder="", typ="temp", root=None):
    """Resolve a preview/output image path, rejecting anything outside the folder."""
    typ = str(typ or "temp").lower()
    if typ not in ("output", "temp", "input"):
        typ = "temp"
    base_root = os.path.abspath(root if root is not None else _dir_for_type(typ))
    sub = str(subfolder or "").replace("\\", "/").strip("/")
    parts = [p for p in sub.split("/") if p and p not in (".",)]
    if any(p == ".." for p in parts):
        raise ValueError("subcarpeta inválida")
    name = os.path.basename(str(filename or "").replace("\\", "/"))
    if not name or name in (".", ".."):
        raise ValueError("archivo inválido")
    folder = os.path.abspath(os.path.join(base_root, *parts)) if parts else base_root
    if not (folder == base_root or folder.startswith(base_root + os.sep)):
        raise ValueError("ruta fuera de la carpeta permitida")
    path = os.path.abspath(os.path.join(folder, name))
    if not (path == folder or path.startswith(folder + os.sep)):
        raise ValueError("ruta fuera de la carpeta permitida")
    if not os.path.isfile(path):
        raise FileNotFoundError("no encuentro la imagen: %s" % name)
    return path


def next_output_path(filename_prefix, src_path=None, output_dir=None, width=0, height=0):
    """Build an output path with an incrementing suffix, like ComfyUI SaveImage."""
    prefix = str(filename_prefix or "ComfyUI").strip() or "ComfyUI"
    ext = os.path.splitext(src_path or "")[1] or ".png"
    if not ext.startswith("."):
        ext = "." + ext
    ext_name = ext.lstrip(".")
    try:
        import folder_paths
        out_dir = output_dir or folder_paths.get_output_directory()
        full_output_folder, filename, counter, subfolder, prefix = folder_paths.get_save_image_path(
            prefix, out_dir, int(width or 0), int(height or 0)
        )
        filename = str(filename).replace("%batch_num%", "0")
        file = "%s_%05d_.%s" % (filename, int(counter), ext_name)
        return os.path.join(full_output_folder, file), subfolder, file
    except Exception:
        out_dir = os.path.abspath(output_dir or os.path.join(os.getcwd(), "output"))
        os.makedirs(out_dir, exist_ok=True)
        counter = 1
        while True:
            file = "%s_%05d_.%s" % (prefix, counter, ext_name)
            dest = os.path.join(out_dir, file)
            if not os.path.exists(dest):
                return dest, "", file
            counter += 1


def save_displayed_images(images, filename_prefix="ComfyUI"):
    """Copy already-rendered preview/output files into the output folder."""
    saved = []
    entries = images if isinstance(images, list) else [images]
    if not entries:
        return {"ok": False, "message": "No hay una imagen para guardar.", "saved": []}
    for item in entries:
        if not isinstance(item, dict):
            continue
        src = safe_existing_image_path(
            item.get("filename"),
            item.get("subfolder") or "",
            item.get("type") or "temp",
        )
        dest, subfolder, file = next_output_path(filename_prefix, src_path=src)
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        shutil.copy2(src, dest)
        saved.append({"filename": file, "subfolder": subfolder, "type": "output", "path": dest})
    if not saved:
        return {"ok": False, "message": "No hay una imagen para guardar.", "saved": []}
    names = ", ".join(s["filename"] for s in saved)
    return {"ok": True, "message": "Guardado: %s" % names, "saved": saved}


def _tensor_to_pil(image):
    import numpy as np
    from PIL import Image
    arr = image
    if hasattr(arr, "detach"):
        arr = arr.detach()
    if hasattr(arr, "cpu"):
        arr = arr.cpu().numpy()
    arr = 255.0 * arr
    return Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))


def _png_metadata(prompt, extra_pnginfo):
    try:
        from PIL.PngImagePlugin import PngInfo
    except Exception:
        return None
    try:
        from comfy.cli_args import args
        if getattr(args, "disable_metadata", False):
            return None
    except Exception:
        pass
    meta = PngInfo()
    try:
        if prompt is not None:
            meta.add_text("prompt", json.dumps(prompt))
        if extra_pnginfo is not None:
            for key, value in extra_pnginfo.items():
                meta.add_text(str(key), json.dumps(value) if not isinstance(value, str) else value)
    except Exception:
        return meta
    return meta


class LD_GuardarImagen:
    """Save or preview images. Autosave (default on) writes to output; off is preview-only."""

    def __init__(self):
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Imágenes a mostrar o guardar."}),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "ComfyUI",
                        "tooltip": "Prefijo del archivo en la carpeta output.",
                    },
                ),
                "guardado_automatico": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Si está activo, guarda en output al ejecutar. Si no, solo muestra una vista previa (podés guardar con el botón 💾 Guardar).",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "LD/Prompt"
    DESCRIPTION = (
        "Guarda la imagen en output si 'guardado automático' está activo (por defecto). "
        "Si lo apagás, solo muestra una vista previa. El botón 💾 Guardar la guarda a mano."
    )

    @classmethod
    def IS_CHANGED(cls, images=None, filename_prefix="ComfyUI", guardado_automatico=True, **kwargs):
        parts = [str(filename_prefix or ""), str(bool(guardado_automatico))]
        try:
            parts.append(_image_fingerprint(images))
        except Exception:
            parts.append("img")
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def save_images(self, images, filename_prefix="ComfyUI", guardado_automatico=True, prompt=None, extra_pnginfo=None):
        auto = bool(guardado_automatico)
        try:
            import folder_paths
            if auto:
                out_dir = folder_paths.get_output_directory()
                typ = "output"
                prefix = str(filename_prefix or "ComfyUI")
            else:
                out_dir = folder_paths.get_temp_directory()
                typ = "temp"
                prefix = "%s_temp_%s" % (filename_prefix or "ComfyUI", "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(5)))
        except Exception:
            out_dir = os.path.join(os.getcwd(), "output" if auto else "temp")
            os.makedirs(out_dir, exist_ok=True)
            typ = "output" if auto else "temp"
            prefix = str(filename_prefix or "ComfyUI")

        # Normalize a batch of tensors (B,H,W,C) or a list.
        batch = images
        if batch is None:
            return {"ui": {"images": []}, "result": (images,)}
        try:
            count = int(batch.shape[0]) if hasattr(batch, "shape") else len(batch)
        except Exception:
            count = 1
            batch = [images]

        results = []
        width = height = 0
        try:
            # images[0] is H,W,C in Comfy
            first = batch[0]
            height = int(first.shape[0])
            width = int(first.shape[1])
        except Exception:
            pass
        try:
            import folder_paths
            full_output_folder, filename, counter, subfolder, prefix = folder_paths.get_save_image_path(
                prefix, out_dir, width, height
            )
        except Exception:
            full_output_folder, filename, counter, subfolder, prefix = out_dir, prefix, 1, "", prefix

        metadata = _png_metadata(prompt, extra_pnginfo)
        for batch_number in range(count):
            try:
                img = _tensor_to_pil(batch[batch_number])
            except Exception:
                continue
            filename_with_batch = str(filename).replace("%batch_num%", str(batch_number))
            file = "%s_%05d_.png" % (filename_with_batch, int(counter))
            dest = os.path.join(full_output_folder, file)
            os.makedirs(full_output_folder, exist_ok=True)
            save_kw = {"compress_level": self.compress_level}
            if metadata is not None:
                save_kw["pnginfo"] = metadata
            img.save(dest, **save_kw)
            results.append({"filename": file, "subfolder": subfolder, "type": typ})
            counter = int(counter) + 1

        return {"ui": {"images": results}, "result": (images,)}



def compute_start_at_step(steps, denoise) -> int:
    try:
        steps = int(steps)
    except (TypeError, ValueError):
        steps = 8
    try:
        d = float(denoise)
    except (TypeError, ValueError):
        d = 1.0
    d = max(0.0, min(1.0, d))
    steps = max(1, steps)
    return int(max(0, min(steps, round(steps * (1.0 - d)))))


def latent_pixel_size(latent):
    if not isinstance(latent, dict) or "samples" not in latent:
        raise RuntimeError("Conectá el latent de Tamaño (LD) a Imagen base i2i (LD).")
    samples = latent["samples"]
    # Comfy latent is [B, C, H/8, W/8]
    height = int(samples.shape[-2]) * 8
    width = int(samples.shape[-1]) * 8
    return width, height


def center_crop_resize_image(image, width, height):
    """Cover-crop an IMAGE tensor [B,H,W,C] (or [H,W,C]) to exact width x height."""
    import torch
    import torch.nn.functional as F

    img = image
    if img is None:
        return None
    if not hasattr(img, "shape"):
        raise RuntimeError("imagen inválida para i2i")
    if img.dim() == 3:
        img = img.unsqueeze(0)
    _b, src_h, src_w, _c = img.shape
    target_w = max(8, int(width))
    target_h = max(8, int(height))
    scale = max(target_w / float(src_w), target_h / float(src_h))
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    x = img.permute(0, 3, 1, 2).float()
    x = F.interpolate(x, size=(new_h, new_w), mode="bilinear", align_corners=False)
    top = max(0, (new_h - target_h) // 2)
    left = max(0, (new_w - target_w) // 2)
    x = x[:, :, top : top + target_h, left : left + target_w]
    if x.shape[2] != target_h or x.shape[3] != target_w:
        x = F.interpolate(x, size=(target_h, target_w), mode="bilinear", align_corners=False)
    return x.permute(0, 2, 3, 1).contiguous()


def vae_encode_pixels(vae, image):
    if vae is None:
        raise RuntimeError("Falta el VAE de la rama activa para el i2i.")
    pixels = image
    if pixels.shape[-1] > 3:
        pixels = pixels[:, :, :, :3]
    encoded = vae.encode(pixels)
    if isinstance(encoded, dict) and "samples" in encoded:
        return encoded
    return {"samples": encoded}


class LD_ImagenBaseI2I:
    """t2i (empty latent, denoise 1) or i2i (VAE-encode a base image at Tamaño size)."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "modelo": (
                    "STRING",
                    {
                        "default": "Krea2",
                        "forceInput": True,
                        "tooltip": "Rama activa. Conectá la salida modelo (STRING) del selector Krea2 / Illustrious.",
                    },
                ),
                "denoise": (
                    "FLOAT",
                    {
                        "default": 0.6,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Fuerza del i2i cuando hay imagen. Sin imagen se usa 1.0 (texto a imagen).",
                    },
                ),
                "steps_krea2": (
                    "INT",
                    {
                        "default": 8,
                        "min": 1,
                        "max": 200,
                        "tooltip": "Steps del KSampler de Krea2, para calcular start_at_step = round(steps × (1 − denoise)).",
                    },
                ),
            },
            "optional": {
                "latent_krea2": ("LATENT", {"lazy": True, "tooltip": "Latent vacío de Tamaño (LD) de la rama Krea2."}),
                "latent_illustrious": ("LATENT", {"lazy": True, "tooltip": "Latent vacío de Tamaño (LD) de la rama Illustrious."}),
                "vae_krea2": ("VAE", {"lazy": True, "tooltip": "VAE de Krea2 (solo se usa si hay imagen base)."}),
                "vae_illustrious": ("VAE", {"lazy": True, "tooltip": "VAE del checkpoint Illustrious (solo se usa si hay imagen base)."}),
                "image": ("IMAGE", {"tooltip": "Imagen base opcional. Si está vacía, es texto a imagen. La IA no la ve: con denoise bajo se conserva su ropa, pose y colores aunque el prompt diga otra cosa."}),
                "archivo": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Archivo de la carpeta input (miniatura del nodo).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("LATENT", "FLOAT", "INT")
    RETURN_NAMES = ("latent", "denoise", "start_at_step")
    FUNCTION = "build"
    CATEGORY = "LD/Prompt"

    @classmethod
    def VALIDATE_INPUTS(cls, modelo=None, **kwargs):
        sanitize_combo(modelo, MODELO_GEN_OPTIONS, "Krea2")
        return True
    DESCRIPTION = (
        "Sin imagen: entrega el latent de Tamaño y denoise 1 (texto a imagen). "
        "Con imagen: recorta/reescala al tamaño de Tamaño, la encodifica con el VAE de la rama activa y entrega ese latent y el denoise. "
        "⚠ La IA no ve esta imagen: solo es el punto de partida. Con denoise bajo se conserva su ropa, pose y colores "
        "aunque el prompt diga otra cosa; con denoise alto se parece menos. Para copiar ropa/pose usá las imágenes del Writer con sus chips."
    )

    def check_lazy_status(
        self,
        modelo="Krea2",
        denoise=0.6,
        steps_krea2=8,
        image=None,
        archivo="",
        **kwargs,
    ):
        modelo = sanitize_combo(modelo, MODELO_GEN_OPTIONS, "Krea2")
        is_il = str(modelo).lower().startswith("illust")
        has_img = _has_image(resolve_slot_image(image, archivo))
        need = []
        if is_il:
            need.append("latent_illustrious")
            if has_img:
                need.append("vae_illustrious")
        else:
            need.append("latent_krea2")
            if has_img:
                need.append("vae_krea2")
        return need

    @classmethod
    def IS_CHANGED(cls, modelo="Krea2", denoise=0.6, steps_krea2=8, image=None, archivo="", **kwargs):
        parts = [
            sanitize_combo(modelo, MODELO_GEN_OPTIONS, "Krea2"),
            "%.4f" % float(denoise or 0),
            str(int(steps_krea2 or 8)),
            archivo_fingerprint(archivo),
        ]
        try:
            parts.append("" if image is None else _image_fingerprint(image))
        except Exception:
            parts.append("img")
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def build(
        self,
        modelo="Krea2",
        denoise=0.6,
        steps_krea2=8,
        latent_krea2=None,
        latent_illustrious=None,
        vae_krea2=None,
        vae_illustrious=None,
        image=None,
        archivo="",
    ):
        modelo = sanitize_combo(modelo, MODELO_GEN_OPTIONS, "Krea2")
        is_il = str(modelo).lower().startswith("illust")
        empty = latent_illustrious if is_il else latent_krea2
        if empty is None:
            raise RuntimeError(
                "Conectá el Tamaño (LD) de la rama %s a Imagen base i2i (LD)."
                % ("Illustrious" if is_il else "Krea2")
            )
        pixels = resolve_slot_image(image, archivo)
        if not _has_image(pixels):
            return (empty, 1.0, 0)

        width, height = latent_pixel_size(empty)
        resized = center_crop_resize_image(pixels, width, height)
        vae = vae_illustrious if is_il else vae_krea2
        encoded = vae_encode_pixels(vae, resized)
        # Keep other latent fields (batch, noise_mask) if present, replace samples.
        out = dict(empty)
        out["samples"] = encoded["samples"]
        try:
            d = max(0.0, min(1.0, float(denoise)))
        except (TypeError, ValueError):
            d = 0.6
        start = compute_start_at_step(steps_krea2, d)
        return (out, d, start)


NODE_CLASS_MAPPINGS = {
    "LD_LMStudioConfig": LD_LMStudioConfig,
    "LD_LMStudioPromptWriterV2": LD_LMStudioPromptWriterV2,
    "LD_Tamano": LD_Tamano,
    "LD_ModeloGen": LD_ModeloGen,
    "LD_EmbeddingsNegativos": LD_EmbeddingsNegativos,
    "LD_GuardarImagen": LD_GuardarImagen,
    "LD_ImagenBaseI2I": LD_ImagenBaseI2I,
    NODE_NAME: LD_LMStudioPromptWriter,  # combined node, kept for old workflows
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "LD_LMStudioConfig": "LM Studio Config (LD)",
    "LD_LMStudioPromptWriterV2": "LM Studio Prompt Writer (LD)",
    "LD_Tamano": "Tamaño (LD)",
    "LD_ModeloGen": "Modelo: Krea2 / Illustrious (LD)",
    "LD_EmbeddingsNegativos": "Embeddings negativos (LD)",
    "LD_GuardarImagen": "Guardar imagen (LD)",
    "LD_ImagenBaseI2I": "Imagen base i2i (LD)",
    NODE_NAME: "LM Studio Prompt Writer (LD) (viejo)",
}
