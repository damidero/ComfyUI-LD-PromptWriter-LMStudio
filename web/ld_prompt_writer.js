import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const AUTO_MODEL = "(auto: el cargado)";
const LABEL_SUFFIX = /\s*\((?:cargado|visi[oó]n|vision)(?:,\s*(?:cargado|visi[oó]n|vision))*\)\s*$/i;
const MISSING_IDEA_OR_IMAGE = "⚠️ Escribí una idea o elegí una imagen de referencia";
const OLD_WRITER = "LD_LMStudioPromptWriter";
const CONFIG_NODE = "LD_LMStudioConfig";
const WRITER_V2 = "LD_LMStudioPromptWriterV2";
const ESTILO_SALIDA_DEFAULT = "(como la referencia)";
const ESTILO_SALIDA_OPTIONS = [
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
];

const THEME = {
    config: { color: "#26374b", bgcolor: "#1b222b", accent: "#88b8f3", accent2: "#73d7e0" },
    writer: { color: "#203c40", bgcolor: "#1b222b", accent: "#73d7e0", accent2: "#86dcba" },
    old: { color: "#35294b", bgcolor: "#1b222b", accent: "#bea8ff", accent2: "#ed98c2" },
};

const STYLE_ID = "ld-promptwriter-theme";

function ensureThemeStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const css = document.createElement("style");
    css.id = STYLE_ID;
    css.textContent = `
.ld-panel {
    font-family: "Segoe UI", Inter, ui-sans-serif, system-ui, sans-serif;
    color: #e8eef2;
    background: linear-gradient(180deg, #1e2830 0%, #151c22 100%);
    border: 1px solid rgba(115, 215, 224, 0.28);
    border-radius: 12px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 24px rgba(0,0,0,0.25);
    box-sizing: border-box;
}
.ld-panel.ld-config { border-color: rgba(136, 184, 243, 0.32); }
.ld-panel.ld-old { border-color: rgba(190, 168, 255, 0.32); }
.ld-label {
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(232, 238, 242, 0.62);
    font-weight: 600;
}
.ld-btn {
    cursor: pointer;
    padding: 7px 14px;
    border-radius: 10px;
    border: 1px solid rgba(115, 215, 224, 0.45);
    background: linear-gradient(180deg, #73d7e0 0%, #4fb8c4 100%);
    color: #0b1618;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.01em;
    white-space: nowrap;
    font-family: inherit;
    box-shadow: 0 1px 0 rgba(255,255,255,0.25) inset, 0 2px 8px rgba(0,0,0,0.25);
}
.ld-btn:hover { filter: brightness(1.08); }
.ld-btn:disabled { opacity: 0.55; cursor: default; filter: none; }
.ld-btn.ld-btn-blue {
    border-color: rgba(136, 184, 243, 0.5);
    background: linear-gradient(180deg, #88b8f3 0%, #5d91d4 100%);
    color: #0b1520;
}
.ld-btn.ld-btn-purple {
    border-color: rgba(190, 168, 255, 0.5);
    background: linear-gradient(180deg, #bea8ff 0%, #8f7ad4 100%);
    color: #140c24;
}
.ld-status {
    display: inline-flex;
    align-items: center;
    flex: 1 1 auto;
    min-height: 22px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 11px;
    line-height: 1.3;
    background: rgba(115, 215, 224, 0.1);
    border: 1px solid rgba(115, 215, 224, 0.18);
    color: #d7eef1;
    overflow: hidden;
}
.ld-status.ok { background: rgba(134, 220, 186, 0.14); border-color: rgba(134, 220, 186, 0.35); color: #c8f0dc; }
.ld-status.warn { background: rgba(242, 203, 118, 0.14); border-color: rgba(242, 203, 118, 0.35); color: #f6e2b0; }
.ld-status.err { background: rgba(232, 120, 120, 0.14); border-color: rgba(232, 120, 120, 0.35); color: #f3c0c0; }
.ld-textarea {
    width: 100%;
    min-height: 64px;
    resize: none;
    box-sizing: border-box;
    background: #12181f;
    color: #e8eef2;
    border: 1px solid rgba(115, 215, 224, 0.22);
    border-radius: 8px;
    padding: 8px 10px;
    font-family: ui-monospace, "Cascadia Mono", SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 12px;
    line-height: 1.4;
}
.ld-textarea:focus { outline: none; border-color: rgba(115, 215, 224, 0.7); }
.ld-select {
    width: 100%;
    box-sizing: border-box;
    background: #12181f;
    color: #e8eef2;
    border: 1px solid rgba(115, 215, 224, 0.22);
    border-radius: 8px;
    padding: 7px 10px;
    font-family: inherit;
    font-size: 12px;
}
.ld-select:focus { outline: none; border-color: rgba(115, 215, 224, 0.7); }
.ld-note {
    font-size: 10px;
    line-height: 1.35;
    color: rgba(232, 238, 242, 0.62);
    background: rgba(115, 215, 224, 0.08);
    border: 1px solid rgba(115, 215, 224, 0.18);
    border-radius: 8px;
    padding: 6px 8px;
}
.ld-chip-row { display: flex; flex-wrap: wrap; gap: 4px; }
.ld-chip {
    cursor: pointer;
    border-radius: 999px;
    border: 1px solid rgba(115, 215, 224, 0.28);
    background: #12181f;
    color: #c5d0d4;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.02em;
    padding: 3px 8px;
    font-family: inherit;
}
.ld-chip.on {
    background: linear-gradient(180deg, #73d7e0 0%, #4fb8c4 100%);
    color: #0b1618;
    border-color: rgba(115, 215, 224, 0.6);
}
.ld-img-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    flex: 0 0 auto;
    min-height: 210px;
}
.ld-img-col {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
    background: rgba(0,0,0,0.18);
    border: 1px solid rgba(115, 215, 224, 0.16);
    border-radius: 10px;
    padding: 6px;
}
.ld-desc {
    height: 90px;
    min-height: 90px;
    max-height: 90px;
    overflow: auto;
    flex: 0 0 auto;
    font-size: 11px;
}
.ld-btn.ld-btn-small { padding: 4px 8px; font-size: 11px; border-radius: 8px; }

.ld-thumb {
    position: relative;
    height: 210px;
    border-radius: 8px;
    border: 1px dashed rgba(115, 215, 224, 0.35);
    background: #0e1419;
    overflow: hidden;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
}
.ld-thumb.has-img { border-style: solid; border-color: rgba(115, 215, 224, 0.28); }
.ld-thumb.drag { outline: 2px solid #73d7e0; outline-offset: -1px; }
.ld-thumb img { width: 100%; height: 100%; object-fit: contain; object-position: center; display: block; pointer-events: none; }
.ld-thumb-ph {
    font-size: 11px;
    color: rgba(232,238,242,0.55);
    text-align: center;
    padding: 8px;
    line-height: 1.35;
    pointer-events: none;
}
.ld-thumb-clear, .ld-thumb-pick {
    position: absolute;
    top: 4px;
    width: 22px;
    height: 22px;
    border-radius: 999px;
    border: 0;
    background: rgba(0,0,0,0.68);
    color: #e8eef2;
    cursor: pointer;
    font-size: 12px;
    line-height: 22px;
    text-align: center;
    padding: 0;
    z-index: 2;
    font-family: inherit;
}
.ld-thumb-clear { right: 4px; }
.ld-thumb-pick { left: 4px; }
.ld-thumb-clear:hover, .ld-thumb-pick:hover { background: rgba(115, 215, 224, 0.85); color: #0b1618; }
.ld-thumb-badge {
    position: absolute;
    left: 4px;
    bottom: 4px;
    font-size: 9px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    background: rgba(115, 215, 224, 0.9);
    color: #0b1618;
    border-radius: 6px;
    padding: 1px 6px;
    font-weight: 700;
}
.ld-thumb-name {
    font-size: 10px;
    color: rgba(232,238,242,0.6);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-height: 14px;
}
.ld-picker {
    position: absolute;
    z-index: 30;
    min-width: 180px;
    max-width: 260px;
    max-height: 220px;
    overflow: auto;
    background: #151c22;
    border: 1px solid rgba(115, 215, 224, 0.35);
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    padding: 4px;
}
.ld-picker button {
    display: block;
    width: 100%;
    text-align: left;
    background: transparent;
    color: #e8eef2;
    border: 0;
    padding: 5px 8px;
    font-size: 11px;
    cursor: pointer;
    border-radius: 5px;
    font-family: inherit;
}
.ld-picker button:hover { background: rgba(115, 215, 224, 0.16); }
.ld-img-grid { min-height: 380px; flex: 1 1 auto; align-items: stretch; }
.ld-panel.ld-writer-root { overflow-y: auto !important; }

`;
    document.head.appendChild(css);
}

function applyNodeTheme(node, theme) {
    if (!node) return;
    if (!node.color) node.color = theme.color;
    if (!node.bgcolor) node.bgcolor = theme.bgcolor;
}

function stripLabel(value) {
    return String(value ?? "").trim().replace(LABEL_SUFFIX, "").trim();
}

function isAuto(value) {
    const s = stripLabel(value);
    return !s || s === AUTO_MODEL || s.toLowerCase() === "auto" || s.toLowerCase() === "(auto)";
}

function applyModelOptions(widget, models, currentValue) {
    const labels = { [AUTO_MODEL]: AUTO_MODEL };
    for (const m of models || []) {
        if (m && m.id) {
            labels[m.id] = m.label || m.id;
        }
    }
    const ids = [AUTO_MODEL, ...(models || []).map((m) => m.id).filter(Boolean)];

    let current = currentValue;
    if (current && typeof current === "object" && "value" in current) {
        current = current.value;
    }
    if (isAuto(current)) {
        current = AUTO_MODEL;
    } else {
        const stripped = stripLabel(current);
        current = ids.includes(stripped) ? stripped : stripped || AUTO_MODEL;
        if (current !== AUTO_MODEL && !ids.includes(current)) {
            ids.push(current);
            labels[current] = current;
        }
    }

    widget.options = widget.options || {};
    widget.options.values = ids;
    widget.options.ldLabels = labels;
    widget.value = current;
    patchComboDisplay(widget);
}

function patchComboDisplay(widget) {
    if (!widget || widget._ldDisplayPatched) {
        return;
    }
    widget._ldDisplayPatched = true;
    const origDraw = widget.draw;
    if (typeof origDraw === "function") {
        widget.draw = function (ctx, node, width, y, height) {
            const saved = this.value;
            const labels = this.options?.ldLabels || {};
            if (saved in labels) {
                this.value = labels[saved];
            }
            try {
                return origDraw.apply(this, arguments);
            } finally {
                this.value = saved;
            }
        };
    }
}

async function fetchModels(url) {
    const res = await api.fetchApi(
        `/ld_promptwriter/models?url=${encodeURIComponent(url)}`
    );
    if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
    }
    return res.json();
}

function widgetByName(node, name) {
    return node?.widgets?.find((w) => w.name === name);
}

function widgetValue(node, name, fallback = "") {
    const w = widgetByName(node, name);
    return w != null && w.value != null ? w.value : fallback;
}

function widgetUrl(node) {
    return String(widgetByName(node, "url")?.value || "http://127.0.0.1:1234").trim();
}

function moveWidgetAfter(node, widget, afterName) {
    const w = node.widgets;
    if (!w) return;
    const after = w.findIndex((x) => x.name === afterName);
    const at = w.indexOf(widget);
    if (after >= 0 && at > after + 1) {
        w.splice(at, 1);
        w.splice(after + 1, 0, widget);
    }
}

function hideWidget(widget) {
    if (!widget) return;
    widget.hidden = true;
    widget.computedHeight = 0;
    widget.computeSize = () => [0, -4];
    if (widget.element) {
        widget.element.style.display = "none";
    }
}

function getLink(graph, linkId) {
    if (linkId == null || !graph) return null;
    const links = graph.links;
    if (!links) return null;
    if (typeof links.get === "function") {
        return links.get(linkId);
    }
    return links[linkId];
}

function getOriginNode(graph, link) {
    if (!link || !graph) return null;
    const originId = link.origin_id ?? link[1];
    return graph.getNodeById?.(originId) || null;
}

function walkUpstream(node, inputName) {
    const graph = node?.graph || app.graph;
    const inputIndex = (node.inputs || []).findIndex((i) => i.name === inputName);
    if (inputIndex < 0) {
        return null;
    }
    const input = node.inputs[inputIndex];
    let origin = null;
    if (typeof node.getInputNode === "function") {
        try {
            origin = node.getInputNode(inputIndex);
        } catch (_e) {
            origin = null;
        }
    }
    if (!origin && input?.link != null) {
        origin = getOriginNode(graph, getLink(graph, input.link));
    }
    const seen = new Set();
    while (origin && !seen.has(origin.id)) {
        seen.add(origin.id);
        const typ = String(origin.type || origin.comfyClass || "");
        if (!/reroute/i.test(typ) && typ !== "Reroute") {
            return origin;
        }
        const nextIn = (origin.inputs || []).find((i) => i.link != null) || origin.inputs?.[0];
        if (!nextIn || nextIn.link == null) {
            if (typeof origin.getInputNode === "function") {
                origin = origin.getInputNode(0);
                continue;
            }
            break;
        }
        origin = getOriginNode(graph, getLink(graph, nextIn.link));
    }
    return origin;
}

function isNodeBypassed(node) {
    const mode = node?.mode;
    // ComfyUI: 2 = never / mute, 4 = bypass
    return mode === 2 || mode === 4 || !!node?.flags?.muted;
}

function findUpstreamLoadImage(node, inputName) {
    const origin = walkUpstream(node, inputName);
    if (!origin) {
        return null;
    }
    if (isNodeBypassed(origin)) {
        console.log("[LD-PromptWriter] se ignora", inputName, "porque el nodo está en bypass/mute");
        return null;
    }
    const typ = String(origin.type || origin.comfyClass || "");
    if (!/^LoadImage$/i.test(typ) && typ !== "LoadImage" && !/loadimage/i.test(typ)) {
        return null;
    }
    const imgW =
        origin.widgets?.find((w) => w.name === "image") ||
        origin.widgets?.find((w) => w.name === "filename");
    let filename =
        imgW?.value ??
        origin.widgets_values_named?.image ??
        origin.widgets_values?.[0] ??
        "";
    let subfolder = "";
    let type = "input";
    if (filename && typeof filename === "object") {
        subfolder = filename.subfolder || "";
        type = filename.type || "input";
        filename = filename.filename || filename.image || "";
    }
    filename = String(filename || "").trim();
    if (!filename) {
        return null;
    }
    return { filename, subfolder, type };
}

function findAllUpstreamImages(node) {
    const image_1 = findUpstreamLoadImage(node, "image_1") || findUpstreamLoadImage(node, "image");
    const image_2 = findUpstreamLoadImage(node, "image_2");
    const image_3 = findUpstreamLoadImage(node, "image_3");
    const image_4 = findUpstreamLoadImage(node, "image_4");
    const images = { image_1, image_2, image_3, image_4 };
    const n = [image_1, image_2, image_3, image_4].filter(Boolean).length;
    console.log("[LD-PromptWriter] imágenes en el pedido:", n, images);
    return { ...images, count: n };
}

const ASPECT_KEYS = ["accion", "persona", "fondo", "estilo", "ropa"];
const ASPECT_LABELS = {
    accion: "acción",
    persona: "persona",
    fondo: "fondo",
    estilo: "estilo",
    ropa: "ropa",
};

function readImageAspects(node, index) {
    const active = [];
    for (const k of ASPECT_KEYS) {
        if (widgetValue(node, `img${index}_${k}`, false)) active.push(k);
    }
    return active;
}


function parseArchivo(raw) {
    if (raw && typeof raw === "object") {
        const filename = raw.filename || raw.image || raw.name || "";
        if (!filename) return null;
        return { filename, subfolder: raw.subfolder || "", type: raw.type || "input" };
    }
    const s = String(raw ?? "").trim();
    if (!s) return null;
    let type = "input";
    let name = s;
    const m = s.match(/^(.*)\s*\[(input|output|temp)\]\s*$/i);
    if (m) {
        name = m[1].trim();
        type = m[2].toLowerCase();
    }
    let subfolder = "";
    const norm = name.replace(/\\/g, "/");
    const slash = norm.lastIndexOf("/");
    if (slash >= 0) {
        subfolder = norm.slice(0, slash);
        name = norm.slice(slash + 1);
    } else {
        name = norm;
    }
    return { filename: name, subfolder, type };
}

function serializeArchivo(info) {
    if (!info?.filename) return "";
    const typ = info.type || "input";
    const sub = (info.subfolder || "").replace(/\\/g, "/").replace(/^\/+|\/+$/g, "");
    const name = sub ? `${sub}/${info.filename}` : info.filename;
    if (typ && typ !== "input") return `${name} [${typ}]`;
    return name;
}

function imageViewUrl(info) {
    if (!info?.filename) return "";
    const p = new URLSearchParams({
        filename: info.filename,
        type: info.type || "input",
        subfolder: info.subfolder || "",
    });
    return api.apiURL(`/view?${p}`);
}

function refImageInfo(node, index) {
    const connected =
        findUpstreamLoadImage(node, `image_${index}`) ||
        (index === 1 ? findUpstreamLoadImage(node, "image") : null);
    if (connected) return { ...connected, connected: true };
    return parseArchivo(widgetValue(node, `archivo_imagen_${index}`, ""));
}

async function uploadInputImage(file) {
    const form = new FormData();
    form.append("image", file);
    form.append("overwrite", "true");
    form.append("type", "input");
    const res = await api.fetchApi("/upload/image", { method: "POST", body: form });
    let data = null;
    try {
        data = await res.json();
    } catch (_e) {
        throw new Error(`No pude subir la imagen (${res.status || "sin estado"}).`);
    }
    if (!res.ok) {
        throw new Error(data?.error || data?.message || `No pude subir la imagen (${res.status}).`);
    }
    return {
        filename: data.name || data.filename || file.name,
        subfolder: data.subfolder || "",
        type: data.type || "input",
    };
}

async function fetchInputImages() {
    const res = await api.fetchApi("/ld_promptwriter/input_images");
    const data = await res.json();
    return data.files || [];
}

function closeLdPicker() {
    document.querySelectorAll(".ld-picker").forEach((el) => el.remove());
}

function showImagePicker(anchor, onPick) {
    closeLdPicker();
    const box = document.createElement("div");
    box.className = "ld-picker";
    const rect = anchor.getBoundingClientRect();
    box.style.left = `${Math.min(rect.left, window.innerWidth - 280)}px`;
    box.style.top = `${Math.min(rect.bottom + 4, window.innerHeight - 80)}px`;
    const uploadBtn = document.createElement("button");
    uploadBtn.type = "button";
    uploadBtn.textContent = "⬆ Subir archivo…";
    uploadBtn.addEventListener("click", () => {
        closeLdPicker();
        onPick({ upload: true });
    });
    box.appendChild(uploadBtn);
    document.body.appendChild(box);
    const closer = (ev) => {
        if (!box.contains(ev.target) && ev.target !== anchor) {
            closeLdPicker();
            document.removeEventListener("mousedown", closer, true);
        }
    };
    document.addEventListener("mousedown", closer, true);
    fetchInputImages()
        .then((files) => {
            if (!box.isConnected) return;
            if (!files.length) {
                const empty = document.createElement("button");
                empty.type = "button";
                empty.textContent = "(no hay imágenes en input)";
                empty.disabled = true;
                box.appendChild(empty);
                return;
            }
            for (const f of files) {
                const b = document.createElement("button");
                b.type = "button";
                b.textContent = f.filename || f.name;
                b.addEventListener("click", () => {
                    closeLdPicker();
                    onPick({
                        filename: f.filename || f.name,
                        subfolder: f.subfolder || "",
                        type: f.type || "input",
                    });
                });
                box.appendChild(b);
            }
        })
        .catch(() => {});
}

async function postDescribe(body) {
    const res = await api.fetchApi("/ld_promptwriter/describe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    let data = null;
    try {
        data = await res.json();
    } catch (_e) {
        throw new Error(`Error de red o el servidor no respondió (${res.status || "sin estado"}).`);
    }
    if (!res.ok && !data?.message) {
        throw new Error(`Error de red (${res.status}).`);
    }
    return data;
}

const TAMANO_RATIOS = {
    "1:1": [1, 1], "2:3": [2, 3], "3:2": [3, 2], "3:4": [3, 4], "4:3": [4, 3],
    "9:16": [9, 16], "16:9": [16, 9], "4:5": [4, 5], "5:4": [5, 4], "21:9": [21, 9],
    "9:21": [9, 21], "1:2": [1, 2], "2:1": [2, 1], "3:5": [3, 5], "5:3": [5, 3],
};

function computeTamano(proporcion, megapixeles, intercambiar) {
    let ratio = String(proporcion || "2:3");
    let pair = TAMANO_RATIOS[ratio] || [2, 3];
    let rw = pair[0], rh = pair[1];
    if (intercambiar) { const tmp = rw; rw = rh; rh = tmp; }
    let mp = parseFloat(String(megapixeles || "1.08").replace(",", ".").replace(/[^\d.]/g, "")) || 1.08;
    if (ratio === "2:3" && !intercambiar && Math.abs(mp - 1.08) < 0.02) return [864, 1248];
    if (ratio === "3:2" && intercambiar && Math.abs(mp - 1.08) < 0.02) return [864, 1248];
    const area = Math.max(0.1, mp) * 1e6;
    let height = Math.sqrt(area * rh / rw);
    let width = height * rw / rh;
    const w = Math.max(16, Math.round(width / 16) * 16);
    const h = Math.max(16, Math.round(height / 16) * 16);
    return [w, h];
}

function findUpstreamConfig(node) {
    const origin = walkUpstream(node, "config");
    if (!origin) {
        return null;
    }
    const typ = String(origin.type || origin.comfyClass || "");
    if (typ === CONFIG_NODE || typ === "LD_LMStudioConfig") {
        return origin;
    }
    return origin;
}

function collectLoraNames(origin) {
    const names = [];
    const add = (item) => {
        if (!item) return;
        if (typeof item === "string") {
            const s = item.trim();
            if (s) names.push(s);
            return;
        }
        if (typeof item !== "object") return;
        if (item.active === false) return;
        const n = item.name || item.lora || item.file_name || item.filename || item.lora_name;
        if (n) names.push(String(n));
    };
    const w =
        origin.widgets?.find((x) => x.name === "loras") ||
        origin.widgets?.find((x) => x.name === "lora");
    let val = w?.value;
    if (val && typeof val === "object" && !Array.isArray(val) && Array.isArray(val.loras)) {
        val = val.loras;
    }
    if (Array.isArray(val)) val.forEach(add);
    return names;
}

function collectToggleTags(origin) {
    const w =
        origin.tagWidget ||
        origin.widgets?.find((x) => x.name === "tags" || x.name === "toggle_tags" || x.name === "trigger_tags");
    const val = w?.value ?? origin.tags;
    const arr = Array.isArray(val) ? val : val?.tags;
    const texts = [];
    if (Array.isArray(arr)) {
        for (const t of arr) {
            if (!t || t.active === false) continue;
            const text = t.text || t.tag || t.name || (typeof t === "string" ? t : "");
            if (text) texts.push(String(text));
        }
    }
    return texts;
}

async function fetchLoraTriggerWords(loraName) {
    const res = await api.fetchApi(
        `/api/lm/loras/get-trigger-words?name=${encodeURIComponent(loraName)}`
    );
    if (!res.ok) return [];
    const data = await res.json();
    const words = data?.trigger_words;
    if (Array.isArray(words)) return words.filter(Boolean).map(String);
    if (typeof words === "string" && words.trim()) return [words.trim()];
    return [];
}

function uniqueTriggers(words) {
    const seen = new Set();
    const out = [];
    for (const w of words || []) {
        const t = String(w || "").trim();
        const k = t.toLowerCase();
        if (!t || seen.has(k)) continue;
        seen.add(k);
        out.push(t);
    }
    return out;
}

async function readUpstreamLoraTriggers(node) {
    const origin = walkUpstream(node, "lora_triggers");
    if (!origin) return { text: "", source: "none" };
    const typ = String(origin.type || origin.comfyClass || "");
    const isLoader = /lora\s*loader/i.test(typ) || typ.includes("LoraManager") || typ.includes("Lora Loader");
    const isToggle = /trigger\s*word/i.test(typ);

    if (isToggle) {
        const tags = collectToggleTags(origin);
        if (tags.length) return { text: uniqueTriggers(tags).join(", "), source: "toggle" };
    }
    if (isLoader) {
        const names = collectLoraNames(origin);
        if (!names.length) return { text: "", source: "loader-empty" };
        const words = [];
        let failed = false;
        for (const name of names) {
            try {
                words.push(...(await fetchLoraTriggerWords(name)));
            } catch (_e) {
                failed = true;
            }
        }
        const uniq = uniqueTriggers(words);
        if (uniq.length) return { text: uniq.join(", "), source: "loader-api" };
        return { text: "", source: failed ? "loader-no-words" : "loader-no-words" };
    }
    const strW = origin.widgets?.find(
        (w) => w.name === "value" || w.name === "string" || w.name === "trigger_words" || w.name === "text"
    );
    if (strW && typeof strW.value === "string" && strW.value.trim()) {
        return { text: strW.value.trim(), source: "widget" };
    }
    return { text: "", source: "unknown" };
}

function readConfigValues(cfgNode) {
    if (!cfgNode) {
        return null;
    }
    return {
        url: String(widgetValue(cfgNode, "url", "http://127.0.0.1:1234")).trim(),
        model: widgetValue(cfgNode, "model", AUTO_MODEL),
        mode: widgetValue(cfgNode, "mode", "Krea2 (natural)"),
        temperature: widgetValue(cfgNode, "temperature", 0.7),
        max_tokens: widgetValue(cfgNode, "max_tokens", 600),
        seed: widgetValue(cfgNode, "seed", 0),
        extra_instructions: widgetValue(cfgNode, "extra_instructions", ""),
        unload_after: !!widgetValue(cfgNode, "unload_after", true),
    };
}

async function postGenerate(body) {
    const res = await api.fetchApi("/ld_promptwriter/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    let data = null;
    try {
        data = await res.json();
    } catch (_e) {
        throw new Error(
            `Error de red o el servidor no respondió (${res.status || "sin estado"}).`
        );
    }
    if (!res.ok && !data?.message) {
        throw new Error(`Error de red (${res.status}).`);
    }
    return data;
}

function styleEl(tag, styles, text) {
    const el = document.createElement(tag);
    Object.assign(el.style, styles);
    if (text != null) {
        el.textContent = text;
    }
    return el;
}

function makeTextarea(placeholder, flex) {
    const el = document.createElement("textarea");
    el.className = "ld-textarea";
    el.style.flex = flex;
    el.placeholder = placeholder;
    return el;
}

function setStatusBadge(el, msg) {
    el.textContent = msg || "";
    el.classList.remove("ok", "warn", "err");
    const s = String(msg || "");
    if (/✅/.test(s)) el.classList.add("ok");
    else if (/❌/.test(s)) el.classList.add("err");
    else if (/⚠️/.test(s)) el.classList.add("warn");
}

async function attachModelRefresh(node, setStatus) {
    node._ldRefreshModels = async (fromButton = false) => {
        const combo = widgetByName(node, "model");
        if (!combo) return;
        const url = widgetUrl(node);
        if (fromButton) {
            setStatus?.("Actualizando modelos…");
        }
        try {
            const data = await fetchModels(url);
            const models = data.models || [];
            applyModelOptions(combo, models, combo.value);
            if (fromButton) {
                if (data.reachable) {
                    setStatus?.(
                        models.length > 0
                            ? `Modelos actualizados: ${models.length}`
                            : "LM Studio OK — ningún modelo de chat listado"
                    );
                } else {
                    setStatus?.(`❌ LM Studio no responde en ${url}`);
                    applyModelOptions(combo, [], combo.value);
                }
            }
        } catch (_err) {
            applyModelOptions(combo, [], combo.value);
            if (fromButton) {
                setStatus?.(`❌ LM Studio no responde en ${url}`);
            }
        }
    };

    const refreshBtn = node.addWidget(
        "button",
        "🔄 Actualizar modelos",
        null,
        () => node._ldRefreshModels(true)
    );
    refreshBtn.serialize = false;
    moveWidgetAfter(node, refreshBtn, "model");

    const testBtn = node.addWidget("button", "🔌 Probar conexión", null, async () => {
        const url = widgetUrl(node);
        setStatus?.("Probando conexión…");
        try {
            const res = await api.fetchApi(
                `/ld_promptwriter/test?url=${encodeURIComponent(url)}`
            );
            const data = await res.json();
            if (!res.ok && !data?.message) {
                setStatus?.(`❌ Error de red (${res.status}).`);
                return;
            }
            const msg =
                data.message ||
                (data.reachable
                    ? "✅ LM Studio OK"
                    : `❌ LM Studio no responde en ${url}`);
            setStatus?.(msg);
        } catch (err) {
            setStatus?.(`❌ ${err?.message || "Error de red al probar la conexión."}`);
        }
    });
    testBtn.serialize = false;

    const combo = widgetByName(node, "model");
    if (combo) {
        if (isAuto(combo.value)) {
            combo.value = AUTO_MODEL;
        }
        patchComboDisplay(combo);
    }
    node._ldRefreshModels(false);
}

function attachStatusLine(node, compact, tone) {
    ensureThemeStyles();
    const el = styleEl("div", {}, "");
    el.className = "ld-status";
    const wrap = styleEl("div", { width: "100%", boxSizing: "border-box", padding: "2px 2px 0 2px" });
    wrap.className = `ld-panel ${tone === "config" ? "ld-config" : ""}`;
    Object.assign(wrap.style, {
        display: "flex",
        alignItems: "center",
        padding: "6px 8px",
        minHeight: compact ? "28px" : "34px",
    });
    wrap.appendChild(el);
    const dom = node.addDOMWidget("ld_status", "div", wrap, {
        hideOnZoom: false,
        serialize: false,
    });
    dom.serialize = false;
    if (compact) {
        dom.computeSize = (width) => [width || 200, 36];
    }
    const setStatus = (msg) => setStatusBadge(el, msg);
    node._ldSetStatus = setStatus;
    return setStatus;
}

function buildWriterPanel(node, { includeIdea, onGenerate, tone }) {
    ensureThemeStyles();
    const root = styleEl("div", {
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        height: "100%",
        width: "100%",
        boxSizing: "border-box",
        padding: "10px",
        overflow: "hidden",
    });
    root.className = `ld-panel ${tone === "old" ? "ld-old" : "ld-writer-root"}`;

    const top = styleEl("div", {
        display: "flex",
        flexDirection: "row",
        gap: "10px",
        flex: "0 0 auto",
        minHeight: "130px",
    });
    const left = styleEl("div", {
        display: "flex",
        flexDirection: "column",
        gap: "5px",
        flex: "1 1 42%",
        minWidth: "200px",
        overflow: "hidden",
    });
    const right = styleEl("div", {
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        flex: "1 1 58%",
        minWidth: "220px",
        overflow: "hidden",
    });

    let ideaArea = null;
    let estiloSel = null;
    let useBox = null;
    if (includeIdea) {
        const estiloLabel = styleEl("div", {}, "estilo de salida");
        estiloLabel.className = "ld-label";
        left.appendChild(estiloLabel);
        estiloSel = document.createElement("select");
        estiloSel.className = "ld-select";
        for (const opt of ESTILO_SALIDA_OPTIONS) {
            const o = document.createElement("option");
            o.value = opt;
            o.textContent = opt;
            estiloSel.appendChild(o);
        }
        estiloSel.value = ESTILO_SALIDA_DEFAULT;
        left.appendChild(estiloSel);

        const note = styleEl(
            "div",
            {},
            "Si no hay interruptores activos en una imagen, se usan todos los aspectos (todo). Si elegís un estilo de salida (p. ej. Realista), ese estilo gana sobre el interruptor «estilo» de las imágenes."
        );
        note.className = "ld-note";
        left.appendChild(note);

        const ideaLabel = styleEl("div", {}, "idea");
        ideaLabel.className = "ld-label";
        left.appendChild(ideaLabel);
        ideaArea = makeTextarea("La idea (o dejala vacía y usá una imagen de referencia).", "1 1 auto");
        ideaArea.style.minHeight = "54px";
        left.appendChild(ideaArea);
    }

    const actions = styleEl("div", {
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        gap: "8px",
        flex: "0 0 auto",
    });
    const btn = styleEl("button", {}, "✍️ Generar prompt");
    btn.className = `ld-btn ${tone === "old" ? "ld-btn-purple" : ""}`;
    const status = styleEl("div", { flex: "1 1 auto" }, "");
    status.className = "ld-status";
    const clearAllBtn = styleEl("button", {}, "🧹 Limpiar");
    clearAllBtn.type = "button";
    clearAllBtn.className = "ld-btn ld-btn-blue";
    clearAllBtn.title = "Borra idea, prompts, las 4 imágenes y sus descripciones (no toca interruptores, estilo ni LoRA).";
    if (tone === "old") clearAllBtn.style.display = "none";
    actions.append(btn, clearAllBtn, status);
    right.appendChild(actions);
    const setStatus = (msg) => setStatusBadge(status, msg);

    if (includeIdea) {
        const useNote = styleEl(
            "div",
            { fontSize: "11px", color: "rgba(232,238,242,0.72)", lineHeight: "1.35" },
            "Si el recuadro positivo tiene texto, al ejecutar se usa tal cual (no llama al LLM). Si está vacío, se genera. Los trigger words de LoRA se agregan si faltan."
        );
        useNote.className = "ld-note";
        right.appendChild(useNote);
    }

    const mid = styleEl("div", {
        display: "flex",
        flexDirection: "row",
        gap: "8px",
        flex: "0 0 auto",
        alignItems: "flex-start",
        overflow: "hidden",
    });
    const midL = styleEl("div", { display: "flex", flexDirection: "column", gap: "4px", flex: "1 1 60%", minWidth: "0", overflow: "hidden" });
    const midR = styleEl("div", { display: "flex", flexDirection: "column", gap: "4px", flex: "1 1 40%", minWidth: "0", overflow: "hidden" });
    const posLabel = styleEl("div", {}, "prompt generado · positivo");
    posLabel.className = "ld-label";
    midL.appendChild(posLabel);
    const pos = makeTextarea("Prompt positivo. Editable antes de correr el workflow.", "0 0 auto");
    Object.assign(pos.style, { height: "140px", minHeight: "140px", maxHeight: "140px", overflow: "auto", resize: "none" });
    midL.appendChild(pos);
    const negLabel = styleEl("div", {}, "negativo generado");
    negLabel.className = "ld-label";
    midR.appendChild(negLabel);
    const neg = makeTextarea("Prompt negativo (Illustrious). En Krea2 suele quedar vacío.", "0 0 auto");
    Object.assign(neg.style, { height: "70px", minHeight: "70px", maxHeight: "70px", overflow: "auto", resize: "none" });
    midR.appendChild(neg);
    mid.append(midL, midR);

    const grid = styleEl("div", {});
    grid.className = "ld-img-grid";
    const cols = [];
    for (let i = 1; i <= 4; i++) {
        const col = styleEl("div", {});
        col.className = "ld-img-col";
        const title = styleEl("div", {}, `imagen ${i}`);
        title.className = "ld-label";
        col.appendChild(title);
        const chips = styleEl("div", {});
        chips.className = "ld-chip-row";
        const chipMap = {};
        for (const key of ASPECT_KEYS) {
            const chip = styleEl("button", {}, ASPECT_LABELS[key]);
            chip.type = "button";
            chip.className = "ld-chip";
            chip.dataset.aspect = key;
            chip.addEventListener("click", () => {
                const w = widgetByName(node, `img${i}_${key}`);
                const next = !(w ? w.value : chip.classList.contains("on"));
                if (w) w.value = next;
                chip.classList.toggle("on", next);
                node.graph?.setDirtyCanvas?.(true);
            });
            chips.appendChild(chip);
            chipMap[key] = chip;
        }
        col.appendChild(chips);
        const thumb = styleEl("div", {});
        thumb.className = "ld-thumb";
        const ph = styleEl("div", {}, "Clic o arrastrá una imagen");
        ph.className = "ld-thumb-ph";
        const imgEl = document.createElement("img");
        imgEl.alt = "";
        imgEl.style.display = "none";
        const badge = styleEl("div", {}, "conectada");
        badge.className = "ld-thumb-badge";
        badge.style.display = "none";
        const pickBtn = styleEl("button", {}, "📂");
        pickBtn.type = "button";
        pickBtn.className = "ld-thumb-pick";
        pickBtn.title = "Elegir de la carpeta input";
        const clearBtn = styleEl("button", {}, "✖");
        clearBtn.type = "button";
        clearBtn.className = "ld-thumb-clear";
        clearBtn.title = "Quitar imagen";
        const fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = "image/*";
        fileInput.style.display = "none";
        thumb.append(ph, imgEl, badge, pickBtn, clearBtn, fileInput);
        const nameEl = styleEl("div", {}, "");
        nameEl.className = "ld-thumb-name";
        col.append(thumb, nameEl);
        const refreshThumb = () => {
            const info = refImageInfo(node, i);
            const has = !!(info && info.filename);
            thumb.classList.toggle("has-img", has);
            if (has) {
                imgEl.src = imageViewUrl(info);
                imgEl.style.display = "block";
                ph.style.display = "none";
                nameEl.textContent = info.filename + (info.subfolder ? ` (${info.subfolder})` : "");
            } else {
                imgEl.removeAttribute("src");
                imgEl.style.display = "none";
                ph.style.display = "";
                nameEl.textContent = "";
            }
            badge.style.display = info?.connected ? "" : "none";
            clearBtn.style.display = has && !info?.connected ? "" : "none";
        };
        const setArchivo = (info) => {
            const w = widgetByName(node, `archivo_imagen_${i}`);
            if (w) w.value = serializeArchivo(info);
            refreshThumb();
            node.graph?.setDirtyCanvas?.(true);
        };
        thumb.addEventListener("click", (ev) => {
            if (ev.target === pickBtn || ev.target === clearBtn) return;
            if (refImageInfo(node, i)?.connected) return;
            fileInput.click();
        });
        pickBtn.addEventListener("click", (ev) => {
            ev.stopPropagation();
            if (refImageInfo(node, i)?.connected) return;
            showImagePicker(pickBtn, (choice) => {
                if (choice?.upload) fileInput.click();
                else if (choice?.filename) setArchivo(choice);
            });
        });
        clearBtn.addEventListener("click", (ev) => {
            ev.stopPropagation();
            setArchivo(null);
        });
        fileInput.addEventListener("change", async () => {
            const file = fileInput.files && fileInput.files[0];
            fileInput.value = "";
            if (!file) return;
            try {
                const info = await uploadInputImage(file);
                setArchivo(info);
            } catch (err) {
                setStatus(`❌ ${err.message || "No pude subir la imagen."}`);
            }
        });
        for (const evn of ["dragenter", "dragover"]) {
            thumb.addEventListener(evn, (ev) => {
                ev.preventDefault();
                thumb.classList.add("drag");
            });
        }
        thumb.addEventListener("dragleave", (ev) => {
            ev.preventDefault();
            thumb.classList.remove("drag");
        });
        thumb.addEventListener("drop", async (ev) => {
            ev.preventDefault();
            thumb.classList.remove("drag");
            if (refImageInfo(node, i)?.connected) {
                setStatus("⚠️ Esta columna usa la entrada IMAGE conectada.");
                return;
            }
            const file = ev.dataTransfer?.files?.[0];
            if (!file) return;
            try {
                const info = await uploadInputImage(file);
                setArchivo(info);
            } catch (err) {
                setStatus(`❌ ${err.message || "No pude subir la imagen."}`);
            }
        });
        const desc = makeTextarea("Descripción informativa. Pulsá 🔄 Describir.", "1 1 auto");
        desc.className = "ld-textarea ld-desc";
        desc.readOnly = true;
        col.appendChild(desc);
        const dBtn = styleEl("button", {}, "🔄 Describir");
        dBtn.type = "button";
        dBtn.className = "ld-btn ld-btn-small";
        col.appendChild(dBtn);
        grid.appendChild(col);
        cols.push({ index: i, desc, button: dBtn, chips: chipMap, refreshThumb });
    }

    if (includeIdea) {
        top.append(left, right);
        root.append(top, mid, grid);
    } else {
        root.append(right, mid);
    }

    const syncFromWidgets = () => {
        const pw = widgetByName(node, "prompt_generado");
        const nw = widgetByName(node, "negativo_generado");
        const iw = widgetByName(node, "idea");
        const uw = widgetByName(node, "usar_prompt_generado");
        if (pw && pos.value !== String(pw.value ?? "")) pos.value = String(pw.value ?? "");
        if (nw && neg.value !== String(nw.value ?? "")) neg.value = String(nw.value ?? "");
        if (includeIdea && ideaArea && iw && ideaArea.value !== String(iw.value ?? "")) {
            ideaArea.value = String(iw.value ?? "");
        }
        const ew = widgetByName(node, "estilo_salida");
        if (includeIdea && estiloSel && ew) {
            const ev = String(ew.value ?? ESTILO_SALIDA_DEFAULT);
            if (estiloSel.value !== ev) estiloSel.value = ev;
        }
        if (includeIdea && useBox && uw) useBox.checked = !!uw.value;
        for (const col of cols) {
            for (const key of ASPECT_KEYS) {
                const on = !!widgetValue(node, `img${col.index}_${key}`, false);
                col.chips[key].classList.toggle("on", on);
            }
            const dw = widgetByName(node, `desc_imagen_${col.index}`);
            if (dw && col.desc.value !== String(dw.value ?? "")) col.desc.value = String(dw.value ?? "");
            col.refreshThumb?.();
        }
    };
    const syncToWidgets = () => {
        const pw = widgetByName(node, "prompt_generado");
        const nw = widgetByName(node, "negativo_generado");
        const iw = widgetByName(node, "idea");
        const ew = widgetByName(node, "estilo_salida");
        const uw = widgetByName(node, "usar_prompt_generado");
        if (pw) pw.value = pos.value;
        if (nw) nw.value = neg.value;
        if (includeIdea && ideaArea && iw) iw.value = ideaArea.value;
        if (includeIdea && estiloSel && ew) ew.value = estiloSel.value;
        if (includeIdea && useBox && uw) uw.value = useBox.checked;
        for (const col of cols) {
            const dw = widgetByName(node, `desc_imagen_${col.index}`);
            if (dw) dw.value = col.desc.value;
        }
        node.graph?.setDirtyCanvas?.(true);
    };
    pos.addEventListener("input", syncToWidgets);
    neg.addEventListener("input", syncToWidgets);
    ideaArea?.addEventListener("input", syncToWidgets);
    estiloSel?.addEventListener("change", syncToWidgets);
    useBox?.addEventListener("change", syncToWidgets);

    for (const col of cols) {
        col.button.addEventListener("click", async () => {
            const img = refImageInfo(node, col.index);
            if (!img) {
                setStatus(`⚠️ No hay imagen ${col.index}. Elegí o arrastrá un archivo en la miniatura.`);
                return;
            }
            const cfgNode = findUpstreamConfig(node);
            const cfg = readConfigValues(cfgNode);
            if (!cfg) {
                setStatus("⚠️ Conectá el nodo LM Studio Config (LD) a la entrada config.");
                return;
            }
            setStatus(`⏳ Describiendo imagen ${col.index}…`);
            col.button.disabled = true;
            try {
                const data = await postDescribe({
                    url: cfg.url,
                    model: cfg.model,
                    image: img,
                    temperature: 0.3,
                    max_tokens: 400,
                    unload_after: !!cfg.unload_after,
                });
                if (!data?.ok) {
                    setStatus(data?.message || `❌ No pude describir la imagen ${col.index}.`);
                    return;
                }
                col.desc.value = data.description || "";
                syncToWidgets();
                setStatus(`✅ Descripción de la imagen ${col.index} lista (solo informativa).`);
            } catch (err) {
                setStatus(`❌ ${err?.message || "No pude describir la imagen."}`);
            } finally {
                col.button.disabled = false;
            }
        });
    }

    clearAllBtn.addEventListener("click", () => {
        if (ideaArea) ideaArea.value = "";
        pos.value = "";
        neg.value = "";
        for (const col of cols) {
            col.desc.value = "";
            const aw = widgetByName(node, `archivo_imagen_${col.index}`);
            if (aw) aw.value = "";
            col.refreshThumb?.();
        }
        syncToWidgets();
        status.textContent = "";
        status.className = "ld-status";
        setStatus("🧹 Listo: idea, prompts, imágenes y descripciones borrados.");
    });

    btn.addEventListener("click", async () => {
        setStatus("⏳ Generando...");
        btn.disabled = true;
        try {
            syncToWidgets();
            await onGenerate({
                setStatus,
                pos,
                neg,
                ideaArea,
                syncToWidgets,
            });
        } catch (err) {
            setStatus(`❌ ${err?.message || "No pude generar el prompt."}`);
        } finally {
            btn.disabled = false;
        }
    });

    return { root, pos, neg, ideaArea, estiloSel, setStatus, syncFromWidgets, syncToWidgets, btn };
}

function visibleHeaderHeight(node) {
    let y = 30;
    try {
        if (typeof LiteGraph !== "undefined" && LiteGraph.NODE_TITLE_HEIGHT) {
            y = LiteGraph.NODE_TITLE_HEIGHT;
        }
    } catch (_e) {}
    // Sit the panel immediately under the title so slot connectors stay on the
    // left edge without a large empty band. Hidden widgets must not add space.
    return y + 2;
}


function placeDom(el, node, opts) {
    if (!el) return;
    if (node.flags?.collapsed) {
        el.style.display = "none";
        return;
    }
    const margin = opts.margin ?? 8;
    const header = opts.header ?? 30;
    const left = opts.left ?? 0;
    const w = Math.max(160, (node.size?.[0] || 400) - left - margin);
    const h = Math.max(80, (node.size?.[1] || 300) - header - margin);
    Object.assign(el.style, {
        display: "flex",
        position: "absolute",
        left: `${left}px`,
        top: `${header}px`,
        width: `${w}px`,
        height: `${h}px`,
        overflow: "hidden",
        zIndex: 3,
        boxSizing: "border-box",
    });
    const inner = el.firstElementChild && el.classList.contains("ld-panel") ? null : el.querySelector?.(":scope > .ld-panel");
    if (inner) inner.style.height = `${h}px`;
}

function hookExecuted(nodeType) {
    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
        onExecuted?.apply(this, arguments);
        const posW = widgetByName(this, "prompt_generado");
        const negW = widgetByName(this, "negativo_generado");
        if (message?.prompt_generado && posW) {
            const v = Array.isArray(message.prompt_generado)
                ? message.prompt_generado[0]
                : message.prompt_generado;
            posW.value = v ?? "";
        } else if (message?.text && posW) {
            const texts = Array.isArray(message.text)
                ? message.text.join("\n")
                : String(message.text);
            const parts = texts.split(/\n--- negative ---\n/);
            posW.value = parts[0] || "";
            if (negW && parts[1] != null) negW.value = parts[1];
        }
        if (message?.negativo_generado && negW) {
            const v = Array.isArray(message.negativo_generado)
                ? message.negativo_generado[0]
                : message.negativo_generado;
            negW.value = v ?? "";
        }
        this._ldPanel?.syncFromWidgets();
    };
}

function setupConfigNode(nodeType) {
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, arguments);
        ensureThemeStyles();
        applyNodeTheme(this, THEME.config);
        const setStatus = attachStatusLine(this, true, "config");
        attachModelRefresh(this, setStatus);
    };
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (info) {
        onConfigure?.apply(this, arguments);
        applyNodeTheme(this, THEME.config);
        const combo = widgetByName(this, "model");
        if (combo && isAuto(combo.value)) combo.value = AUTO_MODEL;
        this._ldRefreshModels?.(false);
    };
}

const WRITER_NODE_W = 1320;
const WRITER_NODE_H = 1040;
const WRITER_NODE_H_MAX = 1300;
const WRITER_PANEL_H = WRITER_NODE_H - 36;

function clampWriterSize(node) {
    const w = Math.max(1100, Math.min(node.size?.[0] || WRITER_NODE_W, 1800));
    let h = node.size?.[1] || WRITER_NODE_H;
    if (h < WRITER_NODE_H || h > WRITER_NODE_H_MAX) h = WRITER_NODE_H;
    if (!node.size || node.size[0] !== w || node.size[1] !== h) {
        if (typeof node.setSize === "function") node.setSize([w, h]);
        else node.size = [w, h];
    }
}

function setupWriterV2(nodeType) {
    const origComputeSize = nodeType.prototype.computeSize;
    nodeType.prototype.computeSize = function () {
        return [WRITER_NODE_W, WRITER_NODE_H];
    };

    const hideWriterWidgets = (node) => {
        for (const w of node.widgets || []) {
            if (!w || w.name === "ld_writer_panel") continue;
            hideWidget(w);
        }
    };

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, arguments);
        ensureThemeStyles();
        applyNodeTheme(this, THEME.writer);
        hideWriterWidgets(this);

        const panel = buildWriterPanel(this, {
            includeIdea: true,
            tone: "writer",
            onGenerate: async ({ setStatus, pos, neg, syncToWidgets }) => {
                const cfgNode = findUpstreamConfig(this);
                const cfg = readConfigValues(cfgNode);
                if (!cfg) {
                    setStatus("⚠️ Conectá el nodo LM Studio Config (LD) a la entrada config.");
                    return;
                }
                const idea = String(widgetValue(this, "idea", "")).trim();
                const refs = {};
                let n = 0;
                for (let i = 1; i <= 4; i++) {
                    const img = refImageInfo(this, i);
                    if (img) {
                        refs[i] = img;
                        n += 1;
                    }
                }
                if (!idea && !n) {
                    setStatus(MISSING_IDEA_OR_IMAGE);
                    return;
                }
                const estilo = String(widgetValue(this, "estilo_salida", ESTILO_SALIDA_DEFAULT));
                let triggerInfo = { text: "", source: "none" };
                try {
                    triggerInfo = await readUpstreamLoraTriggers(this);
                } catch (_e) {
                    triggerInfo = { text: "", source: "unknown" };
                }
                const aspects = {};
                const body = {
                    ...cfg,
                    idea,
                    usar_imagen_1: widgetValue(this, "usar_imagen_1", "todo"),
                    usar_imagen_2: widgetValue(this, "usar_imagen_2", "todo"),
                    estilo_salida: estilo,
                };
                for (let i = 1; i <= 4; i++) {
                    const img = refs[i];
                    if (img) {
                        body[`image_${i}`] = img;
                        body[`archivo_imagen_${i}`] = serializeArchivo(img);
                    }
                    const active = readImageAspects(this, i);
                    aspects[String(i)] = active;
                    for (const k of ASPECT_KEYS) {
                        body[`img${i}_${k}`] = !!widgetValue(this, `img${i}_${k}`, false);
                    }
                }
                body.aspects = aspects;
                if (triggerInfo.text) body.lora_triggers = triggerInfo.text;
                setStatus(
                    n > 1
                        ? `⏳ Generando con ${n} imágenes (se describe cada una por separado)…`
                        : "⏳ Generando..."
                );
                console.log("[LD-PromptWriter] POST /generate con", n, "imagen(es)", body);
                let data;
                try {
                    data = await postGenerate(body);
                } catch (err) {
                    setStatus(`❌ ${err.message}`);
                    return;
                }
                if (!data?.ok) {
                    setStatus(data?.message || "❌ No pude generar el prompt.");
                    return;
                }
                pos.value = data.positive || "";
                neg.value = data.negative || "";
                syncToWidgets();
                if (!triggerInfo.text && (triggerInfo.source === "unknown" || triggerInfo.source === "loader-no-words")) {
                    setStatus("✅ Prompt generado. Los trigger words de los LoRA se completan al ejecutar el workflow.");
                } else {
                    setStatus("✅ Prompt generado. Revisalo y después ejecutá el workflow.");
                }
            },
        });
        this._ldPanel = panel;
        this._ldSetStatus = panel.setStatus;

        const self = this;
        const dom = this.addDOMWidget("ld_writer_panel", "div", panel.root, {
            hideOnZoom: false,
            serialize: false,
        });
        dom.serialize = false;
        // Fixed height: never derive it from node.size (that fed back into
        // node.computeSize and made the node grow on every load/resize).
        dom.computeSize = (width) => [width || 0, WRITER_PANEL_H];
        dom.getMinHeight = () => WRITER_PANEL_H;
        dom.getMaxHeight = () => WRITER_PANEL_H;
        dom.draw = function () {
            const header = visibleHeaderHeight(self);
            placeDom(this.element || panel.root, self, { header, left: 6, margin: 4 });
        };

        clampWriterSize(this);
        panel.syncFromWidgets();
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (info) {
        onConfigure?.apply(this, arguments);
        applyNodeTheme(this, THEME.writer);
        hideWriterWidgets(this);
        clampWriterSize(this);
        this._ldPanel?.syncFromWidgets();
    };
    const onResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function (size) {
        onResize?.apply(this, arguments);
        if (size && size[1] > WRITER_NODE_H_MAX) size[1] = WRITER_NODE_H_MAX;
    };
    hookExecuted(nodeType);
}

function setupTamano(nodeType) {
    const sizeLabel = (node) => {
        const prop = widgetValue(node, "proporcion", "2:3");
        const mp = widgetValue(node, "megapixeles", "1.08 MP");
        const swap = !!widgetValue(node, "intercambiar", false);
        const [w, h] = computeTamano(prop, mp, swap);
        return `${w}×${h}`;
    };
    const refresh = (node) => {
        const label = sizeLabel(node);
        const pretty = label.replace("×", " × ");
        const res = widgetByName(node, "resultado");
        if (res) res.value = pretty;
        node._ldTamanoLabel = label;
        node.graph?.setDirtyCanvas?.(true);
    };
    const decorateMp = (node) => {
        const mp = widgetByName(node, "megapixeles");
        if (!mp || mp._ldDecorated) return;
        mp._ldDecorated = true;
        const origDraw = mp.draw;
        mp.draw = function (ctx, n, width, y, height) {
            const gap = 100;
            if (typeof origDraw === "function") {
                origDraw.call(this, ctx, n, Math.max(80, width - gap), y, height);
            }
            const label = node._ldTamanoLabel || sizeLabel(node);
            ctx.save();
            ctx.font = "bold 12px sans-serif";
            ctx.fillStyle = "#d7eef1";
            ctx.textAlign = "right";
            ctx.textBaseline = "middle";
            ctx.fillText(label, width - 6, y + height / 2);
            ctx.restore();
        };
    };
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, arguments);
        applyNodeTheme(this, { color: "#44391f", bgcolor: "#1b222b" });
        for (const name of ["proporcion", "megapixeles", "intercambiar"]) {
            const w = widgetByName(this, name);
            if (w) {
                const orig = w.callback;
                w.callback = (...args) => {
                    orig?.apply(this, args);
                    refresh(this);
                };
            }
        }
        const res = widgetByName(this, "resultado");
        if (res) {
            res.disabled = true;
            if (res.inputEl) res.inputEl.readOnly = true;
            hideWidget(res);
        }
        decorateMp(this);
        refresh(this);
        if (!this.size || this.size[0] < 300) {
            if (typeof this.setSize === "function") this.setSize([300, 180]);
            else this.size = [300, 180];
        }
    };
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (info) {
        onConfigure?.apply(this, arguments);
        applyNodeTheme(this, { color: "#44391f", bgcolor: "#1b222b" });
        refresh(this);
    };
    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
        onExecuted?.apply(this, arguments);
        const res = widgetByName(this, "resultado");
        const v = message?.resultado;
        if (res && v != null) res.value = Array.isArray(v) ? v[0] : v;
    };
}


function setupOldWriter(nodeType) {
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, arguments);
        ensureThemeStyles();
        applyNodeTheme(this, THEME.old);
        hideWidget(widgetByName(this, "prompt_generado"));
        hideWidget(widgetByName(this, "negativo_generado"));

        const panel = buildWriterPanel(this, {
            includeIdea: false,
            tone: "old",
            onGenerate: async ({ setStatus, pos, neg, syncToWidgets }) => {
                const img = findUpstreamLoadImage(this, "image");
                const idea = String(widgetValue(this, "idea", "")).trim();
                if (!idea && !img) {
                    setStatus(MISSING_IDEA_OR_IMAGE);
                    return;
                }
                const body = {
                    url: widgetUrl(this),
                    model: widgetValue(this, "model", AUTO_MODEL),
                    mode: widgetValue(this, "mode", "Krea2 (natural)"),
                    temperature: widgetValue(this, "temperature", 0.7),
                    max_tokens: widgetValue(this, "max_tokens", 600),
                    seed: widgetValue(this, "seed", 0),
                    extra_instructions: widgetValue(this, "extra_instructions", ""),
                    unload_after: !!widgetValue(this, "unload_after", true),
                    idea,
                };
                if (img) body.image = img;
                let data;
                try {
                    data = await postGenerate(body);
                } catch (err) {
                    setStatus(`❌ ${err.message}`);
                    return;
                }
                if (!data?.ok) {
                    setStatus(data?.message || "❌ No pude generar el prompt.");
                    return;
                }
                pos.value = data.positive || "";
                neg.value = data.negative || "";
                syncToWidgets();
                setStatus("✅ Prompt generado. Revisalo y después ejecutá el workflow.");
            },
        });
        this._ldPanel = panel;
        this._ldSetStatus = panel.setStatus;

        const dom = this.addDOMWidget("ld_side_panel", "div", panel.root, {
            hideOnZoom: false,
            serialize: false,
        });
        dom.serialize = false;
        dom.computeSize = () => [0, -4];
        const self = this;
        dom.draw = function () {
            placeDom(this.element || panel.root, self, { header: 34, left: 440, margin: 8 });
        };

        attachModelRefresh(this, (msg) => this._ldSetStatus?.(msg));
        if (!this.size || this.size[0] < 800) {
            if (typeof this.setSize === "function") this.setSize([900, 500]);
            else this.size = [900, 500];
        }
        panel.syncFromWidgets();
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (info) {
        onConfigure?.apply(this, arguments);
        applyNodeTheme(this, THEME.old);
        hideWidget(widgetByName(this, "prompt_generado"));
        hideWidget(widgetByName(this, "negativo_generado"));
        const combo = widgetByName(this, "model");
        if (combo && isAuto(combo.value)) combo.value = AUTO_MODEL;
        this._ldPanel?.syncFromWidgets();
        this._ldRefreshModels?.(false);
    };
    hookExecuted(nodeType);
}



app.registerExtension({
    name: "LD.LMStudioPromptWriter",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        const name = nodeData.name;
        if (name === CONFIG_NODE) {
            setupConfigNode(nodeType);
        } else if (name === WRITER_V2) {
            setupWriterV2(nodeType);
        } else if (name === "LD_Tamano") {
            setupTamano(nodeType);
        } else if (name === OLD_WRITER) {
            setupOldWriter(nodeType);
        }
    },
});
