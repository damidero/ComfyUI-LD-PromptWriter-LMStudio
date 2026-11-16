"""LM Studio Prompt Writer (LD): idea -> prompt for Krea2 or Illustrious.

Talks to LM Studio's OpenAI-compatible API (default http://127.0.0.1:1234).
Lists/unloads models the same way H3 Studio does (/api/v0/models and
/api/v1|/api/v0 models/unload). No third-party HTTP libraries: urllib only.
"""
from __future__ import annotations

import base64
import hashlib
import io
import os
import json
import re
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
    "todo": (
        "take the full scene: subject, appearance, pose, setting and clothing. "
        "Still obey the output-style instructions (the art style of this image may be ignored)."
    ),
    "acción / pose": (
        "take ONLY the action, pose, body position, gesture, and composition/camera framing. "
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

ASPECT_KEYS = ("accion", "persona", "fondo", "estilo", "ropa")
ASPECT_LABELS = {
    "accion": "acción / pose",
    "persona": "persona",
    "fondo": "fondo / escena",
    "estilo": "estilo",
    "ropa": "ropa",
    "todo": "todo",
}
ASPECT_PROMPTS = {
    "accion": (
        "take ONLY the action, pose, body position, gesture, and composition/camera framing. "
        "IGNORE the person's identity (face, hair, body type, skin, ethnicity, age). "
        "IGNORE clothing as fashion, background scenery, and art style/medium."
    ),
    "persona": (
        "take ONLY this person's identity and appearance, described in detail: "
        "gender, apparent age, ethnicity, face shape, eyes (color and shape), eyebrows, nose, mouth, "
        "hair color and hairstyle, body type, skin tone, and any distinctive features "
        "(moles, scars, freckles, tattoos). "
        "IGNORE pose, action, composition, background, clothing, and art style. "
        "The FINAL prompt MUST use THIS person as the only subject identity if this is the chosen persona source. "
        "Do NOT use the face, body, hair or identity from any other image."
    ),
    "fondo": (
        "take ONLY the background, setting, environment, architecture, weather and atmosphere. "
        "IGNORE people, faces, pose, clothing and art style/medium."
    ),
    "estilo": (
        "take ONLY the artistic style and photographic/pictorial treatment. "
        "Cover: medium (photograph, oil paint, anime, 3D render, watercolor, comic ink, etc.), "
        "rendering or technique, lighting quality and direction, color palette, contrast, "
        "grain or surface texture, and camera/lens look if it is a photo. "
        "Do NOT mention specific clothing items, garments or accessories. "
        "Do NOT describe the person's identity, pose, action, or what objects/places appear in the scene."
    ),
    "ropa": (
        "take ONLY the clothing and wearable accessories. "
        "Cover each garment, its colors, materials or fabrics, fit (tight, loose, oversized, tailored), "
        "patterns, layers, shoes, bags, jewelry and other accessories. "
        "Do NOT describe art style, medium, lighting, color grading or camera. "
        "Do NOT describe the person's face, body, identity, pose, or the background."
    ),
    "todo": (
        "take the full scene: subject, appearance, pose, setting and clothing. "
        "Still obey the output-style instructions (the art style of this image may be ignored if a different output style was chosen)."
    ),
}
COMBO_TO_ASPECTS = {
    "todo": ["todo"],
    "acción / pose": ["accion"],
    "accion / pose": ["accion"],
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
    # A specific id is passed through so LM Studio can JIT-load it if needed.
    if not is_auto_model(requested):
        return requested
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
    return {
        "model": model,
        "messages": _no_think(messages),
        "temperature": float(temperature),
        "top_p": 0.95,
        "max_tokens": int(max_tokens),
        "seed": int(seed),
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "reasoning_effort": "none",
    }


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


def image_use_sentence(index: int, use: str) -> str:
    aspects = use if isinstance(use, (list, tuple)) else [use]
    parts = []
    for a in aspects:
        key = normalize_aspect_key(a)
        hint = ASPECT_PROMPTS.get(key, ASPECT_PROMPTS["todo"])
        label = ASPECT_LABELS.get(key, key)
        parts.append(f"From IMAGE {index} ({label}): {hint}")
    return " ".join(parts)


def normalize_aspect_key(value: str) -> str:
    raw = " ".join(str(value or "").strip().lower().split())
    aliases = {
        "todo": "todo",
        "all": "todo",
        "accion": "accion",
        "acción": "accion",
        "accion / pose": "accion",
        "acción / pose": "accion",
        "pose": "accion",
        "persona": "persona",
        "person": "persona",
        "fondo": "fondo",
        "fondo / escena": "fondo",
        "escena": "fondo",
        "estilo": "estilo",
        "style": "estilo",
        "ropa": "ropa",
        "clothing": "ropa",
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


def resolve_image_aspects(index: int, old_combo=None, **kwargs) -> list:
    """Toggles win if any are on. Else migrate old combo. Else 'todo' (all aspects)."""
    prefix = f"img{index}_"
    active = [k for k in ASPECT_KEYS if kwargs.get(prefix + k) or kwargs.get(f"image_{index}_{k}")]
    # also accept aspects list from the HTTP body
    body_list = kwargs.get(f"aspects_{index}") or kwargs.get("aspects", {}).get(str(index)) if isinstance(kwargs.get("aspects"), dict) else kwargs.get(f"aspects_{index}")
    if body_list:
        if isinstance(body_list, str):
            body_list = [x.strip() for x in body_list.split(",") if x.strip()]
        mapped = []
        for item in body_list:
            if item == "estilo / ropa" or str(item).lower() == "estilo / ropa":
                mapped.extend(["estilo", "ropa"])
            else:
                mapped.append(normalize_aspect_key(item))
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
    tensors = {
        1: resolve_slot_image(image_1, kwargs.get("archivo_imagen_1")),
        2: resolve_slot_image(image_2, kwargs.get("archivo_imagen_2")),
        3: resolve_slot_image(image_3, kwargs.get("archivo_imagen_3")),
        4: resolve_slot_image(image_4, kwargs.get("archivo_imagen_4")),
    }
    combos = {1: usar_imagen_1, 2: usar_imagen_2, 3: None, 4: None}
    out = []
    for idx in (1, 2, 3, 4):
        tensor = tensors[idx]
        if not _has_image(tensor):
            continue
        aspects = resolve_image_aspects(idx, combos[idx], **kwargs)
        # expand todo
        if aspects == ["todo"] or "todo" in aspects:
            aspects = list(ASPECT_KEYS)
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


def triggers_instruction(is_illustrious: bool, triggers: list) -> str:
    if not triggers:
        return ""
    joined = ", ".join(triggers)
    if is_illustrious:
        return (
            "You MUST include these LoRA trigger words verbatim as Danbooru-style tags "
            "(keep their exact spelling) near the start of the tag list, right after the "
            f"quality tags: {joined}"
        )
    return (
        "You MUST include these LoRA trigger words verbatim at the very start of the prompt, "
        f"in this exact form, then continue with the rest of the description: {joined}"
    )


def ensure_triggers(positive: str, triggers: list, is_illustrious: bool) -> str:
    """If the LLM omitted any trigger, put the missing ones in verbatim."""
    text = str(positive or "")
    missing = [t for t in triggers if t.lower() not in text.lower()]
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
    uses = {idx: _aspect_names(use) for idx, _t, use in refs}
    persona_idx = [i for i, u in uses.items() if "persona" in u]
    if persona_idx:
        others = [str(i) for i in uses if i not in persona_idx]
        who = " and ".join(f"IMAGE {i}" for i in persona_idx)
        if others:
            lines.append(
                f"The person/identity MUST come from {who} only. "
                f"Do NOT use the person, face, hair, body or identity visible in IMAGE {', IMAGE '.join(others)}."
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
):
    """One vision call: extract only the requested aspect(s) from a single image."""
    aspects = use if isinstance(use, (list, tuple)) else [use]
    sections = []
    for a in aspects:
        key = normalize_aspect_key(a)
        label = ASPECT_LABELS.get(key, key)
        hint = ASPECT_PROMPTS.get(key, ASPECT_PROMPTS["todo"])
        sections.append(f"### {label.upper()}\n{hint}")
    prompt = (
        f"This is IMAGE {index}. Extract ONLY the requested aspect(s), in separate labeled sections "
        f"exactly as follows:\n\n" + "\n\n".join(sections) + "\n\n"
        "Write a dense factual description in English under each heading. "
        "Do not mix clothing into the style section, or style/medium into the clothing section. "
        "Do not write a full image prompt, do not mention other images, do not mention these instructions."
    )
    content = _user_content(prompt, "", images=[(index, tensor, ",".join(str(a) for a in aspects))])
    raw = chat_complete(
        url,
        model_id,
        [
            {
                "role": "system",
                "content": (
                    "You extract visual facts from a single reference image. "
                    "Output only the requested aspect(s), in English, under the given headings. No preamble."
                ),
            },
            {"role": "user", "content": content},
        ],
        temperature,
        min(int(max_tokens), 700),
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
):
    """Informational full description of one image. Does not unload the model."""
    image = load_ref_image(filename, subfolder, typ)
    if not _has_image(image):
        raise RuntimeError("No pude leer la imagen para describirla.")
    url = _norm_url(url)
    model_id = pick_model(url, model)
    vis = _model_is_vision(url, model_id)
    if vis is False:
        raise RuntimeError(VISION_REQUIRED)
    prompt = (
        "Describe this image in clear English. Cover subject, appearance, clothing, pose, "
        "setting, lighting and style. Be factual and concise. Output only the description."
    )
    content = _user_content(prompt, "", images=[(1, image, "todo")])
    raw = chat_complete(
        url,
        model_id,
        [
            {"role": "system", "content": "You describe images factually, in English. No preamble."},
            {"role": "user", "content": content},
        ],
        temperature,
        max_tokens,
        seed,
    )
    return clean_output(raw)


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
    is_illustrious = str(mode).lower().startswith("illustrious")
    system = SYS_ILLUSTRIOUS if is_illustrious else SYS_KREA2
    guide = " ".join(image_use_sentence(idx, use) for idx, _tensor, use in refs)
    roles = _roles_rule(refs)
    if roles:
        guide = (guide + " " + roles).strip()
    estilo_inst = style_instruction(estilo_salida, is_illustrious)
    if not idea and has_img:
        idea = IMAGE_ONLY_ILLUSTRIOUS if is_illustrious else IMAGE_ONLY_KREA2
        if len(refs) > 1:
            idea = idea.replace("this reference image", "these reference images").replace("from it", "from them")
        if guide:
            idea = idea + "\n\n" + guide
    elif idea and has_img:
        idea = idea + "\n\n" + (guide or "Use the attached image as a visual reference.")

    triggers = normalize_triggers(lora_triggers)
    trig_inst = triggers_instruction(is_illustrious, triggers)
    extra_bits = [str(extra_instructions or "").strip(), estilo_inst, trig_inst]
    extra_instructions = "\n\n".join(b for b in extra_bits if b)

    try:
        model_id = pick_model(url, model)
    except RuntimeError:
        raise
    except Exception as e:
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
            # Some LM Studio builds only honor the first image in a multi-image request.
            # Describe each image alone, then compose the prompt in a text-only call.
            notes = []
            for idx, tensor, use in refs:
                note = describe_reference_aspect(
                    url, model_id, tensor, idx, use, temperature, max_tokens, seed
                )
                print(f"[LD-PromptWriter] describí IMAGE {idx} ({use if isinstance(use, str) else ', '.join(use)}): {len(note)} caracteres", flush=True)
                notes.append(f"Notes from IMAGE {idx} ({use if isinstance(use, str) else ', '.join(ASPECT_LABELS.get(a, a) for a in use)}):\n{note}")
            compose = idea + "\n\n" + "\n\n".join(notes)
            if roles:
                compose += "\n\n" + roles
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": _user_content(compose, extra_instructions, images=[])},
            ]
        else:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": _user_content(idea, extra_instructions, images=refs)},
            ]
        raw = chat_complete(url, model_id, messages, temperature, max_tokens, seed)
    except RuntimeError as e:
        if has_img and _looks_like_no_vision_error(str(e)):
            raise RuntimeError(VISION_REQUIRED) from e
        raise
    except Exception as e:
        msg = str(e)
        if has_img and _looks_like_no_vision_error(msg):
            raise RuntimeError(VISION_REQUIRED) from e
        raise RuntimeError(_down_msg(url)) from e

    if is_illustrious:
        positive, negative = parse_illustrious(raw)
    else:
        positive, negative = clean_output(raw), ""

    if not positive:
        raise RuntimeError(
            "El modelo no devolvió un prompt. Si es un modelo con thinking, "
            "desactivá Reasoning/Thinking en LM Studio e intentá de nuevo."
        )

    positive = ensure_triggers(positive, triggers, is_illustrious)
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
                        "tooltip": "Descarga el modelo de LM Studio al terminar, para liberar VRAM.",
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
    def VALIDATE_INPUTS(cls, model):
        """Accept any model id (and legacy empty/auto).

        execution.py skips the COMBO 'value not in list' check for an input
        when that input is a VALIDATE_INPUTS argument. The list changes as
        models are downloaded or the server goes offline, so membership
        must not be required.
        """
        if model is None or isinstance(model, (str, int)):
            return True
        return f"modelo inválido: {model!r}"

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

        positive, negative = generate_prompt(
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



def generate_prompt(idea, mode, url, model, temperature, max_tokens, seed=0,
                    unload_after=True, extra_instructions="", **kwargs):
    """Generate, then unload the LLM if unload_after (also after an error)."""
    try:
        return _generate_prompt_impl(idea, mode, url, model, temperature, max_tokens,
                                     seed, unload_after, extra_instructions, **kwargs)
    finally:
        if unload_after:
            try:
                unload_models(url, model)
            except Exception as e:
                print(f"[LD-PromptWriter] aviso al descargar el modelo: {e}", flush=True)


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
            for idx, key in ((1, "image_1"), (2, "image_2"), (3, "image_3"), (4, "image_4")):
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
            for idx in (1, 2, 3, 4):
                for k in ASPECT_KEYS:
                    val = body.get(f"img{idx}_{k}")
                    if val is not None:
                        extra_kw[f"img{idx}_{k}"] = val
            print(
                f"[LD-PromptWriter] /generate con {len(images)} imagen(es): "
                + ", ".join(f"IMAGE {i}" for i in images),
                flush=True,
            )
            positive, negative = generate_prompt(
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
                {"ok": True, "positive": positive, "negative": negative}
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
        try:
            text = describe_image_info(
                body.get("url", DEFAULT_URL),
                body.get("model", AUTO_MODEL),
                filename,
                img.get("subfolder") or body.get("subfolder") or "",
                img.get("type") or body.get("type") or "input",
                body.get("temperature", 0.3),
                body.get("max_tokens", 400),
                body.get("seed", 0),
            )
            return web.json_response({"ok": True, "description": text})
        except Exception as e:
            return web.json_response({"ok": False, "message": str(e)})
        finally:
            if body.get("unload_after"):
                try:
                    unload_models(body.get("url", DEFAULT_URL), body.get("model", AUTO_MODEL))
                except Exception as e:
                    print(f"[LD-PromptWriter] aviso al descargar el modelo: {e}", flush=True)

    async def ld_promptwriter_input_images(request):
        files = list_input_images()
        return web.json_response({"ok": True, "files": files})

    inst.routes.get("/ld_promptwriter/test")(ld_promptwriter_test)
    inst.routes.get("/ld_promptwriter/models")(ld_promptwriter_models)
    inst.routes.get("/ld_promptwriter/input_images")(ld_promptwriter_input_images)
    inst.routes.post("/ld_promptwriter/generate")(ld_promptwriter_generate)
    inst.routes.post("/ld_promptwriter/describe")(ld_promptwriter_describe)
    inst._ld_promptwriter_routes = True
    print("[LD-PromptWriter] rutas /ld_promptwriter/test, /models, /generate, /describe e /input_images registradas", flush=True)


register_routes()



CFG_TYPE = "LD_LMSTUDIO_CFG"


def pack_config(url, model, mode, temperature, max_tokens, seed, unload_after, extra_instructions=""):
    return {
        "url": url,
        "model": model,
        "mode": mode,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "seed": seed,
        "unload_after": unload_after,
        "extra_instructions": extra_instructions or "",
    }


def unpack_config(cfg) -> dict:
    if not isinstance(cfg, dict):
        raise RuntimeError("Conectá el nodo LM Studio Config (LD) a la entrada config del Writer.")
    return pack_config(
        cfg.get("url", DEFAULT_URL),
        cfg.get("model", AUTO_MODEL),
        cfg.get("mode", "Krea2 (natural)"),
        cfg.get("temperature", 0.7),
        cfg.get("max_tokens", 600),
        cfg.get("seed", 0),
        cfg.get("unload_after", True),
        cfg.get("extra_instructions", ""),
    )


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
                        "tooltip": "Descarga el modelo de LM Studio al terminar, para liberar VRAM.",
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
            }
        }

    RETURN_TYPES = (CFG_TYPE,)
    RETURN_NAMES = ("config",)
    FUNCTION = "build"
    CATEGORY = "LD/Prompt"

    @classmethod
    def VALIDATE_INPUTS(cls, model):
        if model is None or isinstance(model, (str, int)):
            return True
        return f"modelo inválido: {model!r}"

    @classmethod
    def IS_CHANGED(cls, url, model, mode, temperature, max_tokens, seed, unload_after, extra_instructions=""):
        parts = [
            _norm_url(str(url)),
            "" if is_auto_model(model) else strip_model_label(str(model or "")),
            str(mode),
            f"{float(temperature):.4f}",
            str(int(max_tokens)),
            str(int(seed)),
            str(bool(unload_after)),
            str(extra_instructions or ""),
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def build(self, url, model, mode, temperature, max_tokens, seed, unload_after, extra_instructions=""):
        return (pack_config(url, model, mode, temperature, max_tokens, seed, unload_after, extra_instructions),)


class LD_LMStudioPromptWriterV2:
    @classmethod
    def INPUT_TYPES(cls):
        return {
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
                "image_1": (
                    "IMAGE",
                    {"tooltip": "Imagen de referencia 1 (hace falta un modelo de visión en LM Studio)."},
                ),
                "image_2": (
                    "IMAGE",
                    {"tooltip": "Imagen de referencia 2 (hace falta un modelo de visión en LM Studio)."},
                ),
                "image_3": (
                    "IMAGE",
                    {"tooltip": "Imagen de referencia 3 (hace falta un modelo de visión en LM Studio)."},
                ),
                "image_4": (
                    "IMAGE",
                    {"tooltip": "Imagen de referencia 4 (hace falta un modelo de visión en LM Studio)."},
                ),
                "lora_triggers": (
                    "STRING",
                    {
                        "forceInput": True,
                        "default": "",
                        "tooltip": "Trigger words de los LoRA. Conectá la salida trigger_words del Lora Loader (LoraManager).",
                    },
                ),
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
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "write"
    CATEGORY = "LD/Prompt"
    OUTPUT_NODE = False

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
        ]
        for idx in (1, 2, 3, 4):
            parts.append(archivo_fingerprint(kwargs.get(f"archivo_imagen_{idx}")))
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
        is_illustrious = str(cfg.get("mode", "")).lower().startswith("illustrious")
        triggers = normalize_triggers(lora_triggers)
        cached = str(prompt_generado or "").strip()
        if cached:
            positive = ensure_triggers(cached, triggers, is_illustrious)
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

        positive, negative = generate_prompt(
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
            **kwargs,
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



PROPORCIONES = ("1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "4:5", "5:4", "21:9", "9:21", "1:2", "2:1", "3:5", "5:3")
MEGAPIXELES = ("1.0 MP", "1.08 MP", "1.3 MP", "1.5 MP", "2.0 MP")
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
    "1.0 MP": 1.0,
    "1.08 MP": 1.08,
    "1.3 MP": 1.3,
    "1.5 MP": 1.5,
    "2.0 MP": 2.0,
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
    def IS_CHANGED(cls, proporcion, megapixeles, intercambiar=False, batch=1, resultado=""):
        w, h = compute_size(proporcion, megapixeles, intercambiar)
        return f"{w}x{h}x{int(batch)}"

    def build(self, proporcion, megapixeles, intercambiar=False, batch=1, resultado=""):
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




NODE_CLASS_MAPPINGS = {
    "LD_LMStudioConfig": LD_LMStudioConfig,
    "LD_LMStudioPromptWriterV2": LD_LMStudioPromptWriterV2,
    "LD_Tamano": LD_Tamano,
    NODE_NAME: LD_LMStudioPromptWriter,  # combined node, kept for old workflows
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "LD_LMStudioConfig": "LM Studio Config (LD)",
    "LD_LMStudioPromptWriterV2": "LM Studio Prompt Writer (LD)",
    "LD_Tamano": "Tamaño (LD)",
    NODE_NAME: "LM Studio Prompt Writer (LD) (viejo)",
}
