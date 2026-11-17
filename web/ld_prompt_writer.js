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
    align-items: flex-start;
    flex: 1 1 auto;
    min-height: 22px;
    padding: 4px 10px;
    border-radius: 10px;
    font-size: 11px;
    line-height: 1.35;
    background: rgba(115, 215, 224, 0.1);
    border: 1px solid rgba(115, 215, 224, 0.18);
    color: #d7eef1;
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 90px;
}
.ld-status.ld-status-config {
    min-height: 52px;
    max-height: 96px;
    width: 100%;
    box-sizing: border-box;
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
.ld-chip-row { display: flex; flex-wrap: wrap; gap: 3px; }
.ld-chip {
    cursor: pointer;
    border-radius: 999px;
    border: 1px solid rgba(115, 215, 224, 0.28);
    background: #12181f;
    color: #c5d0d4;
    font-size: 9.5px;
    font-weight: 600;
    letter-spacing: 0.01em;
    line-height: 1.25;
    padding: 2px 6px;
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
    height: 60px;
    min-height: 60px;
    max-height: 60px;
    overflow: auto;
    flex: 0 0 60px;
    font-size: 11px;
    resize: none;
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
.ld-img-grid { min-height: 0; flex: 0 0 auto; align-items: stretch; }
.ld-panel.ld-writer-root { overflow-y: auto !important; }
.ld-writer-slot-gap { flex: 0 0 12px; height: 12px; pointer-events: none; }
.ld-log-wrap { flex: 0 0 auto; margin-top: 6px; display: flex; flex-direction: column; gap: 4px; }
.ld-log-wrap.ld-log-config { margin-top: 0; padding: 2px 8px 6px 8px; box-sizing: border-box; width: 100%; height: 100%; }
.ld-log-config .ld-log { height: auto; flex: 1 1 auto; min-height: 60px; }
.ld-pair-row { display: flex; flex-direction: row; gap: 8px; align-items: flex-end; width: 100%; flex: 0 0 auto; }
.ld-pair-row > .ld-field-stack { flex: 1 1 50%; min-width: 0; width: auto; }
.ld-log {
    height: 88px;
    overflow: auto;
    margin: 0;
    padding: 6px 8px;
    font-size: 11px;
    line-height: 1.35;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    background: rgba(0,0,0,0.35);
    border: 1px solid rgba(115, 215, 224, 0.22);
    border-radius: 8px;
    color: rgba(232, 238, 242, 0.88);
    white-space: pre-wrap;
    word-break: break-word;
}
.ld-log .ld-log-err { color: #ff8a8a; }
.ld-idea-row { display: flex; flex-direction: column; gap: 5px; align-items: stretch; width: 100%; flex: 1 1 auto; min-height: 54px; }
.ld-cam-col { display: flex; flex-direction: column; gap: 4px; width: 100%; flex: 0 0 auto; }
.ld-field-stack { display: flex; flex-direction: column; gap: 4px; width: 100%; flex: 0 0 auto; }
.ld-pos-row { display: flex; flex-direction: row; gap: 8px; align-items: stretch; width: 100%; flex: 0 0 auto; }
.ld-pos-col { display: flex; flex-direction: column; gap: 4px; flex: 1 1 50%; min-width: 0; overflow: hidden; }
.ld-neg-full { display: flex; flex-direction: column; gap: 4px; width: 100%; flex: 0 0 auto; }
.ld-vista-es { display: flex; flex-direction: column; gap: 4px; flex: 1 1 50%; min-width: 0; margin-top: 0; }
.ld-vista-es textarea {
    height: 140px !important;
    min-height: 140px !important;
    max-height: 140px !important;
    flex: 0 0 140px !important;
    resize: none;
    overflow-y: auto;
}
.ld-vista-es.ld-vista-hidden { display: none !important; }
.ld-modify-row {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 8px;
    flex: 0 0 auto;
}
.ld-modify-input {
    flex: 1 1 auto;
    min-width: 120px;
    box-sizing: border-box;
    background: #12181f;
    color: #e8eef2;
    border: 1px solid rgba(115, 215, 224, 0.22);
    border-radius: 8px;
    padding: 7px 10px;
    font-family: inherit;
    font-size: 12px;
}
.ld-modify-input:focus { outline: none; border-color: rgba(115, 215, 224, 0.7); }
.ld-writer-head {
    display: flex;
    align-items: center;
    min-height: 28px;
    height: 28px;
    box-sizing: border-box;
    padding: 0 12px 0 20px;
    margin: -10px -10px 2px;
    border-bottom: 1px solid rgba(115, 215, 224, 0.22);
    background: rgba(115, 215, 224, 0.08);
    border-radius: 12px 12px 0 0;
    pointer-events: none;
}
.ld-writer-head-title {
    font-size: 13px;
    font-weight: 700;
    color: #e8eef2;
    letter-spacing: 0.02em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    user-select: none;
    pointer-events: none;
}
.ld-fold {
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,0,0,0.22);
    border: 1px solid rgba(115, 215, 224, 0.2);
    border-radius: 8px;
    color: #d7eef1;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 5px 10px;
    font-family: inherit;
    width: 100%;
    text-align: left;
    box-sizing: border-box;
}
.ld-fold:hover { border-color: rgba(115, 215, 224, 0.45); }
.ld-switch-row { display: flex; gap: 8px; width: 100%; }
.ld-switch {
    flex: 1 1 50%;
    cursor: pointer;
    border-radius: 10px;
    padding: 8px 10px;
    border: 1px solid rgba(115, 215, 224, 0.28);
    background: #12181f;
    color: #c5d0d4;
    font-weight: 700;
    font-size: 13px;
    font-family: inherit;
}
.ld-switch.on {
    background: linear-gradient(180deg, #73d7e0 0%, #4fb8c4 100%);
    color: #0b1618;
    border-color: rgba(115, 215, 224, 0.6);
}
.ld-modelo-panel {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 4px 2px 2px;
    box-sizing: border-box;
}
.ld-people-custom { width: 72px; flex: 0 0 72px; }
.ld-pasadas-row { display: flex; gap: 6px; width: 100%; margin-top: 6px; }
.ld-pasadas-row .ld-switch { padding: 5px 8px; font-size: 12px; border-radius: 8px; }
.ld-pair-row.ld-pair-low { margin-top: 2px; }
.ld-tamano-box { display: flex; flex-direction: column; gap: 4px; width: 100%; box-sizing: border-box; padding: 2px 2px 0; font-family: "Segoe UI", Inter, ui-sans-serif, system-ui, sans-serif; color: #e8eef2; }
.ld-tamano-size {
    text-align: center;
    font-weight: 700;
    font-size: 13px;
    color: #d7eef1;
    padding: 6px 4px 2px;
    letter-spacing: 0.03em;
    width: 100%;
    box-sizing: border-box;
}

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
    // Keep the value in widgets_values / the queued prompt. If a hidden
    // combo (e.g. Config.idioma) is omitted, later widgets such as
    // descarga_idle_min (0) shift onto it and the queue fails.
    widget.serialize = true;
    if (widget.element) {
        widget.element.style.display = "none";
    }
}

function comboOptions(widget) {
    if (!widget) return [];
    const opts = widget.options?.values ?? widget.options;
    if (!Array.isArray(opts)) return [];
    return opts.map((o) => (o && typeof o === "object" ? o.value ?? o : o));
}

function sanitizeWidgetValue(widget) {
    if (!widget) return;
    const values = comboOptions(widget);
    const isCombo =
        values.length > 0 ||
        String(widget.type || "").toLowerCase() === "combo";
    if (!isCombo) return;
    const current = widget.value;
    if (values.includes(current)) return;
    const asText = current == null ? "" : String(current).trim();
    const match = values.find((opt) => String(opt) === asText || String(opt).toLowerCase() === asText.toLowerCase());
    if (match !== undefined) {
        widget.value = match;
        return;
    }
    if (typeof current === "number" && current >= 0 && current < values.length) {
        widget.value = values[current];
        return;
    }
    if (/^\d+$/.test(asText)) {
        const idx = Number(asText);
        if (idx >= 0 && idx < values.length && !values.map(String).includes(asText)) {
            widget.value = values[idx];
            return;
        }
    }
    const fallback = widget.options?.default ?? values[0];
    if (fallback !== undefined) widget.value = fallback;
}

function isControlAfterValue(v) {
    const s = String(v ?? "").toLowerCase();
    return s === "fixed" || s === "increment" || s === "decrement" || s === "randomize";
}

function isLangValue(v, allowed) {
    const s = String(v ?? "").trim();
    if (allowed && allowed.includes(v)) return true;
    return s === "Español" || s === "English" || /^eng/i.test(s) || /^esp/i.test(s);
}

function repairShiftedConfigWidgets(node) {
    const typ = String(node?.type || node?.comfyClass || "");
    if (typ && typ !== "LD_LMStudioConfig") return;
    const idioma = widgetByName(node, "idioma");
    const idle = widgetByName(node, "descarga_idle_min");
    const extra = widgetByName(node, "extra_instructions");
    const unload = widgetByName(node, "unload_after");
    const ctrl = widgetByName(node, "control_after_generate");
    const langs = comboOptions(idioma);
    const allowed = langs.length ? langs : ["Español", "English"];

    // Seed widgets inject control_after_generate after seed. If widgets_values
    // omitted it, unload_after's boolean lands on control and everything after
    // seed shifts (unload gets "", extra gets the language, idioma gets idle's 0).
    if (ctrl && unload && !isControlAfterValue(ctrl.value) && typeof ctrl.value === "boolean") {
        const stolenUnload = !!ctrl.value;
        const stolenExtra = typeof unload.value === "string" ? unload.value : "";
        const stolenLang = extra && isLangValue(extra.value, allowed) ? extra.value : null;
        const stolenIdle = idioma && typeof idioma.value === "number" ? idioma.value : null;
        ctrl.value = "fixed";
        unload.value = stolenUnload;
        if (extra) extra.value = isLangValue(stolenExtra, allowed) ? "" : stolenExtra;
        if (stolenLang && idioma) idioma.value = stolenLang;
        if (stolenIdle != null && idle) idle.value = stolenIdle;
    }

    if (idioma) {
        if (!allowed.includes(idioma.value)) {
            if (allowed.includes(extra?.value)) {
                if (typeof idioma.value === "number" && idle) idle.value = idioma.value;
                idioma.value = extra.value;
                if (extra) extra.value = "";
            } else {
                if (typeof idioma.value === "number" && idle && (idle.value == null || idle.value === "")) {
                    idle.value = idioma.value;
                } else if (typeof idioma.value === "number" && idle && idle.value === 0 && idioma.value !== 0) {
                    idle.value = idioma.value;
                }
                idioma.value = "Español";
            }
        }
    }

    if (unload && typeof unload.value !== "boolean") {
        const s = String(unload.value ?? "").trim().toLowerCase();
        if (s === "false" || s === "0") unload.value = false;
        else if (s === "true" || s === "1") unload.value = true;
        else unload.value = true;
    }
}

function repairNodeWidgets(node) {
    if (!node || !node.widgets) return;
    repairShiftedConfigWidgets(node);
    repairI2IWidgets(node);
    for (const w of node.widgets) {
        try {
            sanitizeWidgetValue(w);
        } catch (_e) {}
    }
}

function repairAllGraphWidgets(graph) {
    const g = graph || (typeof app !== "undefined" ? app.graph : null);
    const nodes = g?._nodes || g?.nodes || [];
    for (const n of nodes) {
        try {
            repairNodeWidgets(n);
        } catch (_e) {}
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

function findLoadImageOnWriterOrConfig(node, index) {
    const slot = `image_${index}`;
    const local = findUpstreamLoadImage(node, slot)
        || (index === 1 ? findUpstreamLoadImage(node, "image") : null);
    if (local) return local;
    const cfg = findUpstreamConfig(node);
    if (!cfg || cfg === node) return null;
    return findUpstreamLoadImage(cfg, slot)
        || (index === 1 ? findUpstreamLoadImage(cfg, "image") : null);
}

function findAllUpstreamImages(node) {
    const images = {};
    for (let i = 1; i <= N_IMAGES; i++) {
        images[`image_${i}`] = findLoadImageOnWriterOrConfig(node, i);
    }
    const n = Object.values(images).filter(Boolean).length;
    console.log("[LD-PromptWriter] imágenes en el pedido:", n, images);
    return { ...images, count: n };
}

const N_IMAGES = 8;
const PERSONAS_AUTO = "Auto (decide el LLM)";
const PERSONAS_CUSTOM = "Personalizado";
const PERSONAS_OPTIONS = [PERSONAS_AUTO, "1", "2", "3", "4", "5", "6", "7", "8", PERSONAS_CUSTOM];
const PASADAS_1 = "1 pasada";
const PASADAS_2 = "2 pasadas";
const PASADAS_OPTIONS = [PASADAS_1, PASADAS_2];
function normalizePasadas(v) {
    return String(v ?? "").trim().startsWith("2") ? PASADAS_2 : PASADAS_1;
}
const ROPA_AUTO = "LoRA";
const ROPA_FOTO = "Foto";
const ROPA_DESNUDO = "Desnudo";
const ROPA_OPTIONS = [ROPA_AUTO, ROPA_FOTO, ROPA_DESNUDO];
const ROPA_I18N = { "LoRA": "ropaAuto", "Foto": "ropaFoto", "Desnudo": "ropaDesnudo" };
// 1.1.2 saved "Automático"; read it (and anything unknown) as LoRA.
function normalizeRopa(v) {
    const s = String(v ?? "").trim().toLowerCase();
    if (s === "foto" || s === "photo") return ROPA_FOTO;
    if (s === "desnudo" || s === "nude") return ROPA_DESNUDO;
    return ROPA_AUTO;
}
const MODELO_GEN = "LD_ModeloGen";

// Chip display order: alphabetical by the Spanish label (same order in English).
const ASPECT_KEYS = ["accesorios", "accion", "camara", "colores", "estilo", "expresion", "fondo", "iluminacion", "pelo", "persona", "pose", "ropa"];
const ASPECT_LABELS = {
    accesorios: "Accesorios",
    colores: "Colores",
    expresion: "Expresión",
    iluminacion: "Iluminación",
    pelo: "Pelo",
    accion: "Acción",
    pose: "Pose",
    persona: "Persona",
    ropa: "Ropa",
    fondo: "Fondo",
    estilo: "Estilo",
    camara: "Cámara",
};
const ASPECT_LABELS_EN = {
    accesorios: "Accessories",
    colores: "Colors",
    expresion: "Expression",
    iluminacion: "Lighting",
    pelo: "Hair",
    accion: "Action",
    pose: "Pose",
    persona: "Person",
    ropa: "Clothing",
    fondo: "Background",
    estilo: "Style",
    camara: "Camera",
};
const CAMARA_AUTO = "(Automático - decide el LLM)";
const CAMARA_OPTIONS = [
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
];
const CAMARA_LABELS_EN = {
    [CAMARA_AUTO]: "(Automatic — the LLM decides)",
    "Primer plano / Close-up": "Close-up",
    "Plano medio / Medium shot": "Medium shot",
    "Plano americano / Cowboy shot": "Cowboy shot",
    "Cuerpo entero / Full body": "Full body",
    "Plano general / Wide shot": "Wide shot",
    "Picado / High angle": "High angle",
    "Contrapicado / Low angle": "Low angle",
    "Vista cenital / Top-down": "Top-down",
    "A nivel de ojos / Eye level": "Eye level",
    "POV primera persona": "First-person POV",
    "Por encima del hombro / Over the shoulder": "Over the shoulder",
    "Perfil / Side view": "Side view",
    "De espaldas / From behind": "From behind",
    "Ángulo holandés / Dutch angle": "Dutch angle",
    "Macro": "Macro",
    "Gran angular / Wide-angle lens": "Wide-angle lens",
    "Teleobjetivo / Telephoto": "Telephoto",
    "Selfie": "Selfie",
};

const I18N = {
    es: {
        writerTitle: "LM Studio Prompt Writer (LD)",
        estiloSalida: "Estilo de salida",
        idea: "Idea",
        ideaPh: "La idea (o dejala vacía y usá una imagen de referencia).",
        generar: "✍️ Generar prompt",
        limpiar: "🧹 Limpiar",
        limpiarTitle: "Borra idea, prompts, las 8 imágenes, sus selecciones y descripciones, y vuelve las listas (Estilo, Cámara, Participantes, Ropa, Pasadas) a sus valores por defecto. No toca Config, LoRA, interruptores ni la imagen i2i.",
        useNote: "Si el recuadro positivo tiene texto, al ejecutar se usa tal cual (no llama al LLM). Si está vacío, se genera. Los trigger words de LoRA se agregan si faltan.",
        posLabel: "Prompt generado · positivo",
        vistaEs: "Vista en español ⓘ",
        vistaEsTitle: "Cómo funciona: primero se genera el prompt en inglés; después una llamada aparte traduce al español el inglés FINAL (con los triggers de LoRA). Podés editar el español: antes de generar o encolar se traduce de vuelta al inglés. Con Español es una llamada extra al LLM. Si agregás un LoRA después de generar, apretá Generar de nuevo para que el español lo incluya. En Illustrious se muestra una explicación de los tags.",
        vistaPh: "Editable. Si la cambiás, se traduce al inglés antes de generar.",
        usedEditedPos: "Usando el prompt en inglés (editado a mano).",
        usedTranslatedEs: "Traduje la vista en español y actualicé el positivo.",
        translatingEs: "⏳ Traduciendo la vista en español…",
        translateFail: "❌ No pude traducir la vista en español.",
        negLabel: "Negativo generado",
        posPh: "Prompt positivo. Editable antes de correr el workflow.",
        negPh: "Prompt negativo (Illustrious). En Krea2 suele quedar vacío.",
        numPersonas: "Participantes",
        pasadas1: "1 pasada",
        pasadas2: "2 pasadas",
        pasadasTitle: "1 pasada: Generar describe las imágenes que hagan falta y escribe el prompt. 2 pasadas: en el mismo Generar, después del prompt hace una segunda pasada que lo revisa con todas las especificaciones (imágenes, chips, ropa, participantes, estilo, cámara, LoRA) y lo corrige o mejora. Tarda más.",
        generating2: "⏳ Generando (2 pasadas: prompt + revisión)…",
        ropa: "Ropa",
        ropaAuto: "LoRA",
        ropaFoto: "Foto",
        ropaDesnudo: "Desnudo",
        ropaTitle: "LoRA: usa la ropa que indican los triggers del LoRA (sin triggers decide el LLM). Foto: gana la ropa de la imagen con Ropa activado (se elige solo al prender un chip Ropa). Desnudo: sin ropa.",
        imagen: "Imagen {n}",
        descPh: "Descripción informativa. Pulsá 🔄 Describir.",
        describir: "🔄 Describir",
        thumbPh: "Clic o arrastrá una imagen",
        pickTitle: "Elegir de la carpeta input",
        clearTitle: "Quitar imagen",
        connected: "conectada",
        missingCfg: "⚠️ Conectá el nodo LM Studio Config (LD) a la entrada config.",
        missingIdea: "⚠️ Escribí una idea o elegí una imagen de referencia",
        noImage: "⚠️ No hay imagen {n}. Elegí o arrastrá un archivo en la miniatura.",
        describing: "⏳ Describiendo imagen {n}…",
        described: "✅ Descripción de la imagen {n} lista (solo informativa).",
        describeFail: "❌ No pude describir la imagen {n}.",
        generating: "⏳ Generando...",
        generatingN: "⏳ Generando con {n} imágenes (se describe cada una por separado)…",
        genOk: "✅ Prompt generado. Revisalo y después ejecutá el workflow.",
        genOkTriggers: "✅ Prompt generado. Los trigger words de los LoRA se completan al ejecutar el workflow.",
        genFail: "❌ No pude generar el prompt.",
        cleared: "🧹 Listo: idea, prompts, imágenes, selecciones y descripciones borrados; listas en sus valores por defecto.",
        uploadFail: "❌ No pude subir la imagen.",
        connectedWarn: "⚠️ Esta columna usa la entrada IMAGE conectada.",
        testing: "Probando conexión…",
        refreshModels: "Actualizando modelos…",
        modelsUpdated: "Modelos actualizados: {n}",
        noModels: "LM Studio OK — ningún modelo de chat listado",
        lmsDown: "❌ LM Studio no responde en {url}",
        testOk: "✅ LM Studio OK",
        netErr: "❌ Error de red ({status}).",
        btnTest: "🔌 Probar conexión",
        btnRefresh: "🔄 Actualizar modelos",
        noteEstilo: "Si no hay interruptores activos en una imagen, se usan todos los aspectos (Todo). Si elegís un estilo de salida (p. ej. Realista), ese estilo gana sobre el interruptor «Estilo» de las imágenes.",
        uploadItem: "⬆ Subir archivo…",
        noInputImgs: "(no hay imágenes en input)",
        camara: "Cámara",
        actividad: "Actividad del LLM",
        modificar: "✏️ Modificar",
        cambios: "Cambios",
        cambiosPh: "Ej.: cambiar el color de pelo a rojo",
        modifying: "⏳ Aplicando cambios…",
        modifyOk: "✅ Prompt modificado. Revisalo antes de ejecutar.",
        modifyFail: "❌ No pude modificar el prompt.",
        modifyNeedPrompt: "⚠️ Primero generá un prompt (o escribí uno en el recuadro positivo).",
        modifyNeedChange: "⚠️ Escribí qué querés cambiar (por ejemplo el color de pelo).",
        ajustes: "Ajustes",
        seccionImagenes: "Imágenes de referencia",
        personasAuto: "Auto (decide el LLM)",
        personasCustom: "Personalizado",
        guardarAuto: "Guardado automático",
        btnGuardar: "💾 Guardar",
        guardarSaving: "⏳ Guardando…",
        guardarOk: "✅ Guardado: {name}",
        guardarFail: "❌ No pude guardar.",
        guardarNeedImage: "⚠️ No hay una imagen para guardar. Ejecutá el workflow primero.",
        i2iLabel: "Imagen base (i2i)",
        i2iHint: "Sin imagen: texto a imagen (denoise 1). Con imagen: i2i al tamaño de Tamaño.",
        i2iWarn: "⚠ La IA no ve esta imagen: solo es el punto de partida. Con denoise bajo se conserva su ropa, pose y colores aunque el prompt diga otra cosa; con denoise alto se parece menos. Para copiar ropa/pose usá las imágenes del Writer con sus chips.",
        denoise: "Denoise",
        stepsKrea2: "Steps Krea2",
    },
    en: {
        writerTitle: "LM Studio Prompt Writer (LD)",
        estiloSalida: "Output style",
        idea: "Idea",
        ideaPh: "The idea (or leave it empty and use a reference image).",
        generar: "✍️ Generate prompt",
        limpiar: "🧹 Clear",
        limpiarTitle: "Clears idea, prompts, the 8 images, their selections and descriptions, and resets the dropdowns (Style, Camera, Participants, Clothing, Passes) to their defaults. Does not touch Config, LoRA, switches or the i2i image.",
        useNote: "If the positive box already has text, execution uses it as-is (no LLM call). If empty, a prompt is generated. LoRA trigger words are added if missing.",
        posLabel: "Generated prompt · positive",
        vistaEs: "Spanish view ⓘ",
        vistaEsTitle: "How it works: the English prompt is generated first; then a separate call translates the FINAL English (with the LoRA triggers) into Spanish. You can edit the Spanish: before generating or queueing it is translated back to English. With Español this is one extra LLM call. If you add a LoRA after generating, press Generate again so the Spanish includes it. Illustrious shows an explanation of the tags.",
        vistaPh: "Editable. If you change it, it is translated to English before generating.",
        usedEditedPos: "Using the English prompt (edited by hand).",
        usedTranslatedEs: "Translated the Spanish view and updated the positive prompt.",
        translatingEs: "⏳ Translating the Spanish view…",
        translateFail: "❌ I couldn't translate the Spanish view.",
        negLabel: "Generated negative",
        posPh: "Positive prompt. Editable before you run the workflow.",
        negPh: "Negative prompt (Illustrious). Usually empty for Krea2.",
        numPersonas: "Participants",
        pasadas1: "1 pass",
        pasadas2: "2 passes",
        pasadasTitle: "1 pass: Generate describes the images that need it and writes the prompt. 2 passes: in the same Generate, after the prompt a second pass reviews it against all the settings (images, chips, clothing, participants, style, camera, LoRA) and fixes or improves it. Slower.",
        generating2: "⏳ Generating (2 passes: prompt + review)…",
        ropa: "Clothing",
        ropaAuto: "LoRA",
        ropaFoto: "Photo",
        ropaDesnudo: "Nude",
        ropaTitle: "LoRA: uses the clothing given by the LoRA triggers (the LLM decides if there are none). Photo: clothing from the image with Clothing on wins (picked automatically when you turn a Clothing chip on). Nude: no clothing.",
        imagen: "Image {n}",
        descPh: "Informational description. Click 🔄 Describe.",
        describir: "🔄 Describe",
        thumbPh: "Click or drop an image",
        pickTitle: "Pick from the input folder",
        clearTitle: "Remove image",
        connected: "connected",
        missingCfg: "⚠️ Connect the LM Studio Config (LD) node to the config input.",
        missingIdea: "⚠️ Type an idea or choose a reference image",
        noImage: "⚠️ No image {n}. Choose or drop a file on the thumbnail.",
        describing: "⏳ Describing image {n}…",
        described: "✅ Description of image {n} is ready (informational only).",
        describeFail: "❌ I couldn't describe image {n}.",
        generating: "⏳ Generating...",
        generatingN: "⏳ Generating with {n} images (each one is described separately)…",
        genOk: "✅ Prompt generated. Review it, then run the workflow.",
        genOkTriggers: "✅ Prompt generated. LoRA trigger words are completed when you run the workflow.",
        genFail: "❌ I couldn't generate the prompt.",
        cleared: "🧹 Done: idea, prompts, images, selections and descriptions cleared; dropdowns reset to defaults.",
        uploadFail: "❌ I couldn't upload the image.",
        connectedWarn: "⚠️ This column uses the connected IMAGE input.",
        testing: "Testing connection…",
        refreshModels: "Refreshing models…",
        modelsUpdated: "Models updated: {n}",
        noModels: "LM Studio OK — no chat model listed",
        lmsDown: "❌ LM Studio is not responding at {url}",
        testOk: "✅ LM Studio OK",
        netErr: "❌ Network error ({status}).",
        btnTest: "🔌 Test connection",
        btnRefresh: "🔄 Refresh models",
        noteEstilo: "If no toggles are on for an image, every aspect is used (All). If you pick an output style (e.g. Realistic), it overrides the image «Style» toggle.",
        uploadItem: "⬆ Upload file…",
        noInputImgs: "(no images in input)",
        camara: "Camera",
        actividad: "LLM activity",
        modificar: "✏️ Edit",
        cambios: "Changes",
        cambiosPh: "E.g.: change the hair color to red",
        modifying: "⏳ Applying changes…",
        modifyOk: "✅ Prompt updated. Review it before you run the workflow.",
        modifyFail: "❌ I couldn't edit the prompt.",
        modifyNeedPrompt: "⚠️ Generate a prompt first (or type one in the positive box).",
        modifyNeedChange: "⚠️ Type the change you want (for example the hair color).",
        ajustes: "Settings",
        seccionImagenes: "Reference images",
        personasAuto: "Auto (the LLM decides)",
        personasCustom: "Custom",
        guardarAuto: "Autosave",
        btnGuardar: "💾 Save",
        guardarSaving: "⏳ Saving…",
        guardarOk: "✅ Saved: {name}",
        guardarFail: "❌ Could not save.",
        guardarNeedImage: "⚠️ No image to save. Run the workflow first.",
        i2iLabel: "Base image (i2i)",
        i2iHint: "No image: text-to-image (denoise 1). With an image: i2i at the Tamaño size.",
        i2iWarn: "⚠ The AI does not see this image: it is only the starting point. At low denoise its clothing, pose and colors stay even if the prompt says otherwise; at high denoise it looks less like it. To copy clothing/pose, use the Writer images with their chips.",
        denoise: "Denoise",
        stepsKrea2: "Krea2 steps",
    },
};


const NOTES_CONFIG = {
    es: `Configuración

Krea2
• UNET: Krea2-Turbo-HD-V1-int8_convrot.safetensors
• CLIP: qwen3vl_4b_fp8_scaled.safetensors (tipo krea2)
• VAE: qwen_image_vae.safetensors

LoRAs
• Los LoRA de Krea2 no sirven en Illustrious y al revés.
  Cuando cambies de motor, cambiá también los LoRA del loader
  (se usa un solo Lora Loader para las dos ramas).

Illustrious
• Checkpoint: waiIllustriousSDXL_v170.safetensors
  El archivo tiene que estar en ComfyUI/models/checkpoints
  y seleccionarse en el nodo Load Checkpoint.
  El CLIP y el VAE vienen incluidos; no hace falta cargarlos aparte.
• Alternativa realista: illustriousRealism_ilXL10V40.safetensors
  (estilo más realista; también va en ComfyUI/models/checkpoints
  y se elige en el mismo Load Checkpoint).
• Sampler: euler ancestral (euler_a), 28 pasos, CFG 5.5, ~1 MP (p. ej. 2:3).
• Embeddings negativos: van en ComfyUI/models/embeddings
  y se eligen en el nodo Embeddings negativos (LD)
  (se agregan al prompt negativo de Illustrious).

LLM (LM Studio)
• Recomendado: qwen_qwen3-vl-8b-instruct
  (Qwen3-VL 8B Instruct, con visión: hace falta para describir imágenes).
• Activá el servidor local de LM Studio (pestaña Developer / Local Server)
  y usá esa URL en el nodo Config.

Nodos necesarios

• LD PromptWriter (LM Studio) — este pack
• ComfyUI-Lora-Manager (Lora Loader)
• ComfyUI-Custom-Scripts (PlaySound, opcional)
El resto de los nodos son de ComfyUI (core).

Instalación: ComfyUI Manager → Install via Git URL
(o git clone del repo dentro de ComfyUI/custom_nodes) y reiniciá.`,
    en: `Setup

Krea2
• UNET: Krea2-Turbo-HD-V1-int8_convrot.safetensors
• CLIP: qwen3vl_4b_fp8_scaled.safetensors (type krea2)
• VAE: qwen_image_vae.safetensors

LoRAs
• Krea2 LoRAs do not work in Illustrious and vice versa.
  When you switch engines, also change the LoRAs in the loader
  (one shared Lora Loader is used for both branches).

Illustrious
• Checkpoint: waiIllustriousSDXL_v170.safetensors
  Put the file in ComfyUI/models/checkpoints and select it
  in the Load Checkpoint node.
  CLIP and VAE are built in; you don't need to load them separately.
• Realistic alternative: illustriousRealism_ilXL10V40.safetensors
  (more realistic look; also goes in ComfyUI/models/checkpoints
  and is selected in the same Load Checkpoint).
• Sampler: euler ancestral (euler_a), 28 steps, CFG 5.5, ~1 MP (e.g. 2:3).
• Negative embeddings go in ComfyUI/models/embeddings
  and are chosen in the Embeddings negativos (LD) node
  (they are appended to the Illustrious negative prompt).

LLM (LM Studio)
• Recommended: qwen_qwen3-vl-8b-instruct
  (Qwen3-VL 8B Instruct, vision-capable; required for image description).
• Enable the LM Studio local server (Developer / Local Server tab)
  and use that URL in the Config node.

Required nodes

• LD PromptWriter (LM Studio) — this pack
• ComfyUI-Lora-Manager (Lora Loader)
• ComfyUI-Custom-Scripts (PlaySound, optional)
All other nodes are ComfyUI core.

Install: ComfyUI Manager → Install via Git URL
(or git clone the repo into ComfyUI/custom_nodes), then restart.`,
};
const NOTES_SPECS = {
    es: `Especificaciones

Pasadas
• 1 pasada: Generar describe las imágenes que hagan falta y
  escribe el prompt.
• 2 pasadas: en el mismo Generar, una segunda llamada revisa el
  prompt con todas las especificaciones (imágenes, chips, ropa,
  participantes, estilo, cámara, LoRA) y lo corrige o mejora.
  Tarda más. La actividad muestra Pasada 1/2 y 2/2.
• Si el modelo responde muy corto, se le pide el prompt completo
  otra vez automáticamente.
• max_tokens recomendado en Config: 2048.

Prompt positivo
• Si el recuadro positivo tiene texto, al ejecutar se usa tal cual
  (no llama al LLM). Si está vacío, se genera.
• Los trigger words de LoRA se agregan si faltan.
• Generar describe antes las imágenes sin descripción al día
  (solo con los chips activos).
• Modificar: aplica un cambio puntual al prompt actual.
• Limpiar: borra idea, prompts, las imágenes del Writer, sus chips
  y descripciones, y vuelve las listas (Estilo, Cámara, Participantes,
  Ropa, Pasadas) a su valor por defecto. No toca Config, LoRA ni la imagen i2i.

Imágenes del Writer (chips)
• Chips: Accesorios, Acción, Cámara, Colores, Estilo, Expresión,
  Fondo, Iluminación, Pelo, Persona, Pose, Ropa.
• Cada imagen aporta solo los aspectos con el chip prendido;
  sin ningún chip se usa todo (menos Cámara).
• Las imágenes con Persona se asignan en orden a las personas.
• Pelo, Expresión o Accesorios de otra imagen se aplican a la
  persona elegida sin cambiar su identidad.
• Iluminación: solo la luz (hora, dirección, calidad, temperatura).
  Colores: solo la paleta. Accesorios: joyas, anteojos, objetos
  en la mano (aparte de la ropa; con Desnudo se mantienen).
• El chip Cámara gana sobre el selector Cámara.

Vista en español
• Primero se genera el prompt en inglés. Después, una llamada aparte
  traduce al español el inglés FINAL (con los triggers de LoRA).
• Podés editar el español: antes de generar o encolar se traduce
  de vuelta al inglés.
• Con Español es una llamada extra al LLM (un poco más lento).
• Si agregás un LoRA después de generar, apretá Generar de nuevo
  para que el español lo incluya.
• En Illustrious se muestra una explicación de los tags.

Ropa (selector del Writer)
• LoRA: la ropa de los triggers del LoRA (sin triggers decide el LLM).
• Foto: gana la ropa de la imagen con el chip Ropa. Se elige solo al
  prender un chip Ropa y vuelve a LoRA al apagarlos (o con Limpiar).
• Desnudo: sin ropa; ignora la ropa de imágenes y LoRA.
  Nunca se cambia solo.

Imagen de referencia (i2i)
• La IA no ve esta imagen: solo es el punto de partida del render.
• Sin imagen: texto a imagen (denoise 1). Con imagen: se recorta
  al Tamaño y se usa con el denoise (0.6 por defecto).
• Con denoise bajo se conservan su ropa, pose y colores aunque el
  prompt diga otra cosa (también con Desnudo). Subilo a 0.75–0.9
  para que gane el prompt (se parece menos a la foto).
• Para copiar ropa o pose, cargá la misma foto en una imagen
  del Writer con los chips Ropa / Pose.
• Limpiar no la borra: usá su ✖.

Actividad del LLM
• Está en el nodo Config, debajo de Probar conexión.`,
    en: `How it works

Passes
• 1 pass: Generate describes the images that need it and writes
  the prompt.
• 2 passes: in the same Generate, a second call reviews the prompt
  against all the settings (images, chips, clothing, participants,
  style, camera, LoRA) and fixes or improves it. Slower.
  The activity shows Pass 1/2 and 2/2.
• If the model answers too briefly, it is automatically asked
  for the complete prompt again.
• Recommended max_tokens in Config: 2048.

Positive prompt
• If the positive box has text, execution uses it as-is
  (no LLM call). If it is empty, a prompt is generated.
• LoRA trigger words are added if missing.
• Generate first describes images whose description is out of date
  (only with the active chips).
• Modify: applies a precise change to the current prompt.
• Clear: clears idea, prompts, the Writer images, their chips
  and descriptions, and resets the dropdowns (Style, Camera, Participants,
  Clothing, Passes) to their defaults. Does not touch Config, LoRA or the i2i image.

Writer images (chips)
• Chips (Spanish alphabetical order): Accessories, Action, Camera,
  Colors, Style, Expression, Background, Lighting, Hair, Person,
  Pose, Clothing.
• Each image contributes only the aspects whose chip is on;
  with no chip on, everything is used (except Camera).
• Images with Person are assigned to the people in order.
• Hair, Expression or Accessories from another image are applied
  to the chosen person without changing their identity.
• Lighting: only the light (time, direction, quality, temperature).
  Colors: only the palette. Accessories: jewelry, glasses, held
  objects (separate from clothing; kept with Nude).
• The Camera chip wins over the Camera selector.

Spanish view
• The English prompt is generated first. Then a separate call
  translates the FINAL English (with the LoRA triggers) into Spanish.
• You can edit the Spanish: before generating or queueing it is
  translated back to English.
• With Español this is one extra LLM call (a bit slower).
• If you add a LoRA after generating, press Generate again
  so the Spanish includes it.
• Illustrious shows an explanation of the tags.

Clothing (Writer selector)
• LoRA: clothing from the LoRA triggers (the LLM decides if there are none).
• Photo: clothing from the image with the Clothing chip wins. Picked
  automatically when you turn a Clothing chip on; back to LoRA when
  they are all off (or with Clear).
• Nude: no clothing; ignores clothing from images and LoRAs.
  Never changed automatically.

Reference image (i2i)
• The AI does not see this image: it is only the render's starting point.
• No image: text-to-image (denoise 1). With an image: it is cropped
  to the Tamaño size and used with the denoise (0.6 by default).
• At low denoise its clothing, pose and colors stay even if the
  prompt says otherwise (Nude too). Raise it to 0.75–0.9
  so the prompt wins (it looks less like the photo).
• To copy clothing or pose, load the same photo into a Writer
  image with the Clothing / Pose chips.
• Clear does not remove it: use its ✖.

LLM activity
• It is in the Config node, below Test connection.`,
};
const NOTE_TITLES = {
    config: { es: "Configuración", en: "Setup" },
    specs: { es: "Especificaciones", en: "How it works" },
};
// Back-compat alias (older code paths / forks).
const NOTES_RECOMENDACIONES = NOTES_CONFIG;

function findModeloGen() {
    const nodes = app.graph?._nodes || app.graph?.nodes || [];
    return nodes.find((n) => n && n.type === MODELO_GEN) || null;
}

function currentIdioma() {
    const sel = findModeloGen();
    if (sel) return String(widgetValue(sel, "idioma", "Español") || "Español");
    const nodes = app.graph?._nodes || app.graph?.nodes || [];
    const cfg = nodes.find((n) => n && n.type === CONFIG_NODE);
    return cfg ? String(widgetValue(cfg, "idioma", "Español") || "Español") : "Español";
}

function currentLangFrom(node) {
    const raw = currentIdioma();
    return /^eng/i.test(raw) ? "en" : "es";
}

function syncIdiomaToConfig(idioma) {
    const nodes = app.graph?._nodes || app.graph?.nodes || [];
    for (const n of nodes) {
        if (n.type !== CONFIG_NODE) continue;
        const w = widgetByName(n, "idioma");
        if (w && w.value !== idioma) w.value = idioma;
    }
}

// Pack-managed notes: the "config" note (legacy title "Recomendaciones de
// modelos" / node 186) and the "specs" note. A note is recognised by its
// properties.ld_note flag first, then by its title. Text and title follow
// the workflow language.
function ldNoteKind(n) {
    const typ = String(n?.type || "");
    if (typ !== "Note" && typ !== "MarkdownNote") return null;
    const flag = n.properties?.ld_note;
    if (flag === "config" || flag === "specs") return flag;
    const title = String(n.title || "");
    if (/especificaciones|how it works/i.test(title)) return null; // only with flag
    if (/recomendaciones de modelos|model recommendations/i.test(title)) return "config";
    if (n.id === 186 && !flag) return "config";
    return null;
}

function applyNotesI18n() {
    const lang = currentLangFrom();
    const nodes = app.graph?._nodes || app.graph?.nodes || [];
    for (const n of nodes) {
        const kind = ldNoteKind(n);
        if (!kind) continue;
        const src = kind === "specs" ? NOTES_SPECS : NOTES_CONFIG;
        const text = src[lang] || src.es;
        n.properties = n.properties || {};
        n.properties.ld_note = kind;
        const title = NOTE_TITLES[kind][lang] || NOTE_TITLES[kind].es;
        if (n.title !== title) n.title = title;
        if (Array.isArray(n.widgets_values) && n.widgets_values.length) n.widgets_values[0] = text;
        const w = (n.widgets || [])[0];
        if (w && w.value !== undefined) w.value = text;
        n.properties.text = text;
        if (typeof n.setDirtyCanvas === "function") n.setDirtyCanvas(true, true);
    }
    app.graph?.setDirtyCanvas?.(true, true);
}

function t(nodeOrLang, key, vars) {
    const lang = typeof nodeOrLang === "string" ? nodeOrLang : currentLangFrom(nodeOrLang);
    let s = (I18N[lang] && I18N[lang][key]) || I18N.es[key] || key;
    if (vars) {
        for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, v);
    }
    return s;
}

function aspectLabel(node, key) {
    const lang = currentLangFrom(node);
    const map = lang === "en" ? ASPECT_LABELS_EN : ASPECT_LABELS;
    return map[key] || key;
}

function camaraLabel(nodeOrLang, value) {
    const lang = typeof nodeOrLang === "string" ? nodeOrLang : currentLangFrom(nodeOrLang);
    if (lang === "en") return CAMARA_LABELS_EN[value] || value;
    return value;
}

function appendActivityLine(box, msg, err) {
    if (!box || !msg) return;
    const ts = new Date().toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
    const line = document.createElement("div");
    if (err) line.className = "ld-log-err";
    line.textContent = `[${ts}] ${msg}`;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
}

function hookActivityLog() {
    if (hookActivityLog._on) return;
    hookActivityLog._on = true;
    api.addEventListener("ld_promptwriter_activity", (ev) => {
        const d = ev?.detail ?? ev;
        const msg = (d && (d.message || d.msg)) || (typeof d === "string" ? d : "");
        if (!msg) return;
        const err = d?.level === "err" || d?.key === "error";
        document.querySelectorAll(".ld-log").forEach((box) => appendActivityLine(box, msg, err));
    });
    hookVistaEsEvents();
}

function hookVistaEsEvents() {
    if (hookVistaEsEvents._on) return;
    hookVistaEsEvents._on = true;
    api.addEventListener("ld_promptwriter_vista_es", (ev) => {
        const d = ev?.detail ?? ev;
        const text = d && d.text != null ? d.text : (d?.vista_es ?? "");
        const nodes = app.graph?._nodes || app.graph?.nodes || [];
        for (const n of nodes) {
            if (n?._ldPanel?.vistaEsArea) setVistaEs(n, text);
        }
    });
    api.addEventListener("ld_promptwriter_desc", (ev) => {
        const d = ev?.detail ?? ev;
        const index = Number(d?.index || d?.n || 0);
        if (!index) return;
        const text = d?.text ?? d?.description ?? "";
        const aspects = d?.aspects ?? "";
        const nodes = app.graph?._nodes || app.graph?.nodes || [];
        for (const n of nodes) {
            if (isWriterNode(n) || n?._ldPanel?.cols) {
                setImageDescription(n, index, text, aspects);
                n._ldPanel?.syncToWidgets?.();
            }
        }
    });
}

function setVistaEs(node, text, { clearDirty = true } = {}) {
    if (!node) return;
    const val = String(text ?? "");
    node.properties = node.properties || {};
    node.properties.ld_vista_es = val;
    const panel = node._ldPanel;
    if (panel?.vistaEsArea && panel.vistaEsArea.value !== val) {
        panel.vistaEsArea.value = val;
    }
    if (clearDirty) {
        node.properties.ld_vista_es_dirty = false;
        node.properties.ld_pos_dirty = false;
    }
    applyVistaVisibility(node);
}

function applyVistaVisibility(node) {
    const panel = node?._ldPanel;
    if (!panel?.vistaWrap) return;
    const hide = currentLangFrom(node) === "en";
    panel.vistaWrap.classList.toggle("ld-vista-hidden", hide);
    panel.vistaWrap.style.display = hide ? "none" : "";
}

function markPosDirty(node, dirty) {
    node.properties = node.properties || {};
    node.properties.ld_pos_dirty = !!dirty;
}

function markVistaDirty(node, dirty) {
    node.properties = node.properties || {};
    node.properties.ld_vista_es_dirty = !!dirty;
    if (node._ldPanel?.vistaEsArea) {
        node.properties.ld_vista_es = node._ldPanel.vistaEsArea.value;
    }
}

const TODO_ASPECTS = ["accion", "pose", "persona", "ropa", "fondo", "estilo", "accesorios", "colores", "expresion", "iluminacion", "pelo"];

function aspectListForImage(node, index) {
    let active = readImageAspects(node, index);
    if (!active.length) active = TODO_ASPECTS.slice();
    const estilo = String(widgetValue(node, "estilo_salida", ESTILO_SALIDA_DEFAULT) || ESTILO_SALIDA_DEFAULT);
    if (estilo !== ESTILO_SALIDA_DEFAULT) active = active.filter((a) => a !== "estilo");
    return active;
}

function aspectSignature(node, index) {
    return aspectListForImage(node, index).slice().sort().join(",");
}

function getDescMeta(node) {
    node.properties = node.properties || {};
    if (!node.properties.ld_desc_meta || typeof node.properties.ld_desc_meta !== "object") {
        node.properties.ld_desc_meta = {};
    }
    return node.properties.ld_desc_meta;
}

function setImageDescription(node, index, text, aspectsSig) {
    const val = String(text || "");
    const col = (node._ldPanel?.cols || []).find((c) => c.index === index);
    if (col?.desc && col.desc.value !== val) col.desc.value = val;
    const dw = widgetByName(node, `desc_imagen_${index}`);
    if (dw) dw.value = val;
    const meta = getDescMeta(node);
    meta[String(index)] = String(aspectsSig || "");
    node.properties.ld_desc_meta = meta;
}

function descriptionNeedsRefresh(node, index) {
    const col = (node._ldPanel?.cols || []).find((c) => c.index === index);
    const dw = widgetByName(node, `desc_imagen_${index}`);
    const text = String((col?.desc?.value ?? dw?.value) || "").trim();
    if (!text) return true;
    const meta = getDescMeta(node);
    return String(meta[String(index)] || "") !== aspectSignature(node, index);
}

async function postTranslateEs(body) {
    const res = await api.fetchApi("/ld_promptwriter/translate_es", {
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

async function ensureEnglishFromSpanish(node, { setStatus } = {}) {
    if (!node) return false;
    if (currentLangFrom(node) === "en") return false;
    const props = node.properties = node.properties || {};
    if (props.ld_pos_dirty) return false;
    if (!props.ld_vista_es_dirty) return false;
    const panel = node._ldPanel;
    const es = String(panel?.vistaEsArea?.value || props.ld_vista_es || "").trim();
    if (!es) return false;
    const cfgNode = findUpstreamConfig(node);
    const cfg = readConfigValues(cfgNode);
    if (!cfg) {
        const msg = t(node, "missingCfg");
        setStatus?.(msg);
        throw new Error(msg);
    }
    setStatus?.(t(node, "translatingEs"));
    const data = await postTranslateEs({
        ...cfg,
        text: es,
        vista_es: es,
        idioma: cfg.idioma || "Español",
        unload_after: false,
        descarga_idle_min: cfg.descarga_idle_min || 0,
    });
    if (!data?.ok) {
        const msg = data?.message || t(node, "translateFail");
        setStatus?.(msg);
        throw new Error(msg);
    }
    const english = data.positive || data.english || "";
    if (panel?.pos) panel.pos.value = english;
    const pw = widgetByName(node, "prompt_generado");
    if (pw) pw.value = english;
    props.ld_vista_es = es;
    props.ld_vista_es_dirty = false;
    props.ld_pos_dirty = false;
    panel?.syncToWidgets?.();
    return true;
}

async function ensureImageDescriptions(node, { setStatus } = {}) {
    if (!node) return;
    const needed = [];
    for (let i = 1; i <= N_IMAGES; i++) {
        const img = refImageInfo(node, i);
        if (!img) continue;
        if (!descriptionNeedsRefresh(node, i)) continue;
        needed.push({
            i,
            img,
            aspects: aspectListForImage(node, i),
            sig: aspectSignature(node, i),
        });
    }
    if (!needed.length) return 0;
    const cfgNode = findUpstreamConfig(node);
    const cfg = readConfigValues(cfgNode);
    if (!cfg) {
        const msg = t(node, "missingCfg");
        setStatus?.(msg);
        throw new Error(msg);
    }
    for (const item of needed) {
        setStatus?.(t(node, "describing", { n: item.i }));
        const data = await postDescribe({
            url: cfg.url,
            model: cfg.model,
            image: item.img,
            aspects: item.aspects,
            index: item.i,
            temperature: 0.3,
            max_tokens: 400,
            unload_after: false,
            descarga_idle_min: cfg.descarga_idle_min || 0,
            idioma: cfg.idioma || "Español",
        });
        if (!data?.ok) {
            throw new Error(data?.message || t(node, "describeFail", { n: item.i }));
        }
        setImageDescription(node, item.i, data.description || "", data.aspects || item.sig);
    }
    node._ldPanel?.syncToWidgets?.();
    return needed.length;
}

async function resolveEditedPrompts(node, { setStatus, pos } = {}) {
    const props = node.properties = node.properties || {};
    const en = String(pos?.value || widgetValue(node, "prompt_generado", "") || "").trim();
    if (props.ld_pos_dirty && en) {
        setStatus?.(t(node, "usedEditedPos"));
        props.ld_pos_dirty = false;
        node._ldPanel?.syncToWidgets?.();
        return "english";
    }
    if (await ensureEnglishFromSpanish(node, { setStatus })) {
        setStatus?.(t(node, "usedTranslatedEs"));
        return "spanish";
    }
    return "";
}

function migrateAccionPoseSplit(node) {
    if (!node || node.properties?.ld_accion_pose_split) return;
    for (let i = 1; i <= N_IMAGES; i++) {
        const acc = widgetByName(node, `img${i}_accion`);
        const pose = widgetByName(node, `img${i}_pose`);
        if (pose && acc && !!acc.value) pose.value = true;
    }
    node.properties = node.properties || {};
    node.properties.ld_accion_pose_split = true;
}


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
    const connected = findLoadImageOnWriterOrConfig(node, index);
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
    uploadBtn.textContent = t("es", "uploadItem"); uploadBtn.dataset.i18n = "uploadItem";
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
    let origin = walkUpstream(node, "lora_triggers");
    if (!origin) {
        const cfg = findUpstreamConfig(node);
        if (cfg && cfg !== node) origin = walkUpstream(cfg, "lora_triggers");
    }
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
        max_tokens: widgetValue(cfgNode, "max_tokens", 2048),
        seed: widgetValue(cfgNode, "seed", 0),
        extra_instructions: widgetValue(cfgNode, "extra_instructions", ""),
        unload_after: !!widgetValue(cfgNode, "unload_after", true),
        idioma: currentIdioma(),
        descarga_idle_min: widgetValue(cfgNode, "descarga_idle_min", 0),
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

async function postModify(body) {
    const res = await api.fetchApi("/ld_promptwriter/modify", {
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
        throw new Error(`Error de red (${res.status || "sin estado"}).`);
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
            setStatus?.(t(node, "refreshModels"));
        }
        try {
            const data = await fetchModels(url);
            const models = data.models || [];
            applyModelOptions(combo, models, combo.value);
            if (fromButton) {
                if (data.reachable) {
                    setStatus?.(
                        models.length > 0
                            ? t(node, "modelsUpdated", { n: models.length })
                            : t(node, "noModels")
                    );
                } else {
                    setStatus?.(t(node, "lmsDown", { url }));
                    applyModelOptions(combo, [], combo.value);
                }
            }
        } catch (_err) {
            applyModelOptions(combo, [], combo.value);
            if (fromButton) {
                setStatus?.(t(node, "lmsDown", { url }));
            }
        }
    };

    const refreshBtn = node.addWidget(
        "button",
        t(node, "btnRefresh"),
        null,
        () => node._ldRefreshModels(true)
    );
    node._ldRefreshBtn = refreshBtn;
    refreshBtn.serialize = false;
    moveWidgetAfter(node, refreshBtn, "model");

    const testBtn = node.addWidget("button", t(node, "btnTest"), null, async () => {
        node._ldTestBtn = testBtn;
        const url = widgetUrl(node);
        setStatus?.(t(node, "testing"));
        try {
            const res = await api.fetchApi(
                `/ld_promptwriter/test?url=${encodeURIComponent(url)}`
            );
            const data = await res.json();
            if (!res.ok && !data?.message) {
                setStatus?.(t(node, "netErr", { status: res.status }));
                return;
            }
            const msg =
                data.message ||
                (data.reachable
                    ? t(node, "testOk")
                    : t(node, "lmsDown", { url }));
            setStatus?.(msg);
        } catch (err) {
            setStatus?.(`❌ ${err?.message || t(node, "netErr", { status: "red" })}`);
        }
    });
    testBtn.serialize = false;
    node._ldTestBtn = testBtn;
    node._ldRefreshI18n = () => {
        if (node._ldRefreshBtn) node._ldRefreshBtn.name = t(node, "btnRefresh");
        if (node._ldTestBtn) node._ldTestBtn.name = t(node, "btnTest");
        node.graph?.setDirtyCanvas?.(true);
    };

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
    if (tone === "config") el.classList.add("ld-status-config");
    Object.assign(wrap.style, {
        display: "flex",
        alignItems: "stretch",
        padding: "6px 8px",
        minHeight: tone === "config" ? "64px" : (compact ? "28px" : "34px"),
    });
    wrap.appendChild(el);
    const dom = node.addDOMWidget("ld_status", "div", wrap, {
        hideOnZoom: false,
        serialize: false,
    });
    dom.serialize = false;
    if (tone === "config") {
        dom.computeSize = (width) => [width || 200, 80];
    } else if (compact) {
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
        height: "auto",
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
    let camSel = null;
    let camWrap = null;
    let useNote = null;
    if (includeIdea) {
        const ideaLabel = styleEl("div", {}, t(node, "idea")); ideaLabel.dataset.i18n = "idea";
        ideaLabel.className = "ld-label";
        left.appendChild(ideaLabel);
        ideaArea = makeTextarea(t(node, "ideaPh"), "1 1 auto"); ideaArea.dataset.i18nPh = "ideaPh";
        ideaArea.style.minHeight = "54px";
        left.appendChild(ideaArea);

        const estiloStack = styleEl("div", {});
        estiloStack.className = "ld-field-stack";
        const estiloLabel = styleEl("div", {}, t(node, "estiloSalida")); estiloLabel.dataset.i18n = "estiloSalida";
        estiloLabel.className = "ld-label";
        estiloSel = document.createElement("select");
        estiloSel.className = "ld-select";
        for (const opt of ESTILO_SALIDA_OPTIONS) {
            const o = document.createElement("option");
            o.value = opt;
            o.textContent = opt;
            estiloSel.appendChild(o);
        }
        estiloSel.value = ESTILO_SALIDA_DEFAULT;
        const note = styleEl("div", {}, t(node, "noteEstilo"));
        note.className = "ld-note";
        note.dataset.i18n = "noteEstilo";
        estiloStack.append(estiloLabel, estiloSel, note);
        left.appendChild(estiloStack);

        const camLabel = styleEl("div", {}, t(node, "camara"));
        camLabel.className = "ld-label";
        camLabel.dataset.i18n = "camara";
        camSel = document.createElement("select");
        camSel.className = "ld-select";
        for (const val of CAMARA_OPTIONS) {
            const o = document.createElement("option");
            o.value = val;
            o.textContent = camaraLabel(node, val);
            camSel.appendChild(o);
        }
        camSel.value = String(widgetValue(node, "camara", CAMARA_AUTO) || CAMARA_AUTO);
        camWrap = styleEl("div", {});
        camWrap.className = "ld-field-stack";
        camWrap.append(camLabel, camSel);
        left.appendChild(camWrap);
    }

    const actions = styleEl("div", {
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        gap: "8px",
        flex: "0 0 auto",
    });
    const btn = styleEl("button", {}, t(node, "generar")); btn.dataset.i18n = "generar";
    btn.className = `ld-btn ${tone === "old" ? "ld-btn-purple" : ""}`;
    const status = styleEl("div", { flex: "1 1 auto" }, "");
    status.className = "ld-status";
    const clearAllBtn = styleEl("button", {}, t(node, "limpiar")); clearAllBtn.dataset.i18n = "limpiar";
    clearAllBtn.type = "button";
    clearAllBtn.className = "ld-btn ld-btn-blue";
    clearAllBtn.title = t(node, "limpiarTitle"); clearAllBtn.dataset.i18nTitle = "limpiarTitle";
    if (tone === "old") clearAllBtn.style.display = "none";
    actions.append(btn, clearAllBtn, status);
    right.appendChild(actions);
    const modifyRow = styleEl("div", {});
    modifyRow.className = "ld-modify-row";
    const cambiosLabel = styleEl("div", {}, t(node, "cambios"));
    cambiosLabel.className = "ld-label";
    cambiosLabel.dataset.i18n = "cambios";
    cambiosLabel.style.flex = "0 0 auto";
    const cambiosInput = document.createElement("input");
    cambiosInput.type = "text";
    cambiosInput.className = "ld-modify-input";
    cambiosInput.placeholder = t(node, "cambiosPh");
    cambiosInput.dataset.i18nPh = "cambiosPh";
    const modifyBtn = styleEl("button", {}, t(node, "modificar"));
    modifyBtn.type = "button";
    modifyBtn.className = "ld-btn ld-btn-blue";
    modifyBtn.dataset.i18n = "modificar";
    modifyRow.append(cambiosLabel, cambiosInput, modifyBtn);
    right.appendChild(modifyRow);
    const setStatus = (msg) => setStatusBadge(status, msg);

    modifyBtn.addEventListener("click", async () => {
        const change = String(cambiosInput.value || "").trim();
        const current = String(pos?.value || "").trim();
        if (!current) {
            setStatus(t(node, "modifyNeedPrompt"));
            return;
        }
        if (!change) {
            setStatus(t(node, "modifyNeedChange"));
            return;
        }
        const cfgNode = findUpstreamConfig(node);
        const cfg = readConfigValues(cfgNode);
        if (!cfg) {
            setStatus(t(node, "missingCfg"));
            return;
        }
        modifyBtn.disabled = true;
        btn.disabled = true;
        setStatus(t(node, "modifying"));
        try {
            await ensureEnglishFromSpanish(node, { setStatus });
            const promptNow = String(pos?.value || "").trim() || current;
            const data = await postModify({
                ...cfg,
                prompt: promptNow,
                prompt_generado: promptNow,
                negative: String(neg?.value || ""),
                negativo_generado: String(neg?.value || ""),
                change,
                cambios: change,
                idioma: cfg.idioma || "Español",
            });
            if (!data?.ok) {
                setStatus(data?.message || t(node, "modifyFail"));
                return;
            }
            if (pos) pos.value = data.positive || "";
            if (neg && data.negative != null) neg.value = data.negative;
            setVistaEs(node, data.vista_es || "");
            syncToWidgets();
            setStatus(t(node, "modifyOk"));
        } catch (err) {
            setStatus(`❌ ${err?.message || t(node, "modifyFail")}`);
        } finally {
            modifyBtn.disabled = false;
            btn.disabled = false;
        }
    });
    cambiosInput.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter") {
            ev.preventDefault();
            modifyBtn.click();
        }
    });

    if (includeIdea) {
        useNote = styleEl(
            "div",
            { fontSize: "11px", color: "rgba(232,238,242,0.72)", lineHeight: "1.35" },
            t(node, "useNote")
        );
        useNote.className = "ld-note";
        useNote.dataset.i18n = "useNote";
        right.appendChild(useNote);
    }

    const mid = styleEl("div", {
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        flex: "0 0 auto",
        alignItems: "stretch",
        overflow: "hidden",
        width: "100%",
    });
    const posRow = styleEl("div", {});
    posRow.className = "ld-pos-row";
    const midL = styleEl("div", {});
    midL.className = "ld-pos-col";
    const midR = styleEl("div", {});
    midR.className = "ld-neg-full";
    const posLabel = styleEl("div", {}, t(node, "posLabel")); posLabel.dataset.i18n = "posLabel";
    posLabel.className = "ld-label";
    midL.appendChild(posLabel);
    const pos = makeTextarea(t(node, "posPh"), "0 0 auto"); pos.dataset.i18nPh = "posPh";
    Object.assign(pos.style, { height: "140px", minHeight: "140px", maxHeight: "140px", overflow: "auto", resize: "none" });
    midL.appendChild(pos);
    const vistaWrap = styleEl("div", {});
    vistaWrap.className = "ld-vista-es";
    const vistaLabel = styleEl("div", {}, t(node, "vistaEs"));
    vistaLabel.className = "ld-label";
    vistaLabel.dataset.i18n = "vistaEs";
    vistaLabel.title = t(node, "vistaEsTitle");
    vistaLabel.dataset.i18nTitle = "vistaEsTitle";
    vistaLabel.style.cursor = "help";
    const vistaEsArea = makeTextarea(t(node, "vistaPh"), "0 0 140px");
    vistaEsArea.dataset.i18nPh = "vistaPh";
    vistaEsArea.title = t(node, "vistaEsTitle");
    vistaEsArea.dataset.i18nTitle = "vistaEsTitle";
    Object.assign(vistaEsArea.style, {
        height: "140px",
        minHeight: "140px",
        maxHeight: "140px",
        overflow: "auto",
        resize: "none",
        flex: "0 0 140px",
    });
    vistaWrap.append(vistaLabel, vistaEsArea);
    posRow.append(midL, vistaWrap);
    const negLabel = styleEl("div", {}, t(node, "negLabel")); negLabel.dataset.i18n = "negLabel";
    negLabel.className = "ld-label";
    midR.appendChild(negLabel);
    const neg = makeTextarea(t(node, "negPh"), "0 0 auto"); neg.dataset.i18nPh = "negPh";
    Object.assign(neg.style, { height: "70px", minHeight: "70px", maxHeight: "70px", overflow: "auto", resize: "none" });
    midR.appendChild(neg);
    const peopleLabel = styleEl("div", {}, t(node, "numPersonas"));
    peopleLabel.className = "ld-label";
    peopleLabel.dataset.i18n = "numPersonas";
    const peopleRow = styleEl("div", { display: "flex", gap: "6px", alignItems: "center" });
    const peopleSel = document.createElement("select");
    peopleSel.className = "ld-select";
    const peopleCustom = document.createElement("input");
    peopleCustom.type = "number";
    peopleCustom.min = "1";
    peopleCustom.max = "99";
    peopleCustom.step = "1";
    peopleCustom.className = "ld-modify-input ld-people-custom";
    const refreshPeopleOpts = () => {
        const keep = peopleSel.value;
        peopleSel.innerHTML = "";
        for (const val of PERSONAS_OPTIONS) {
            const o = document.createElement("option");
            o.value = val;
            o.textContent = val === PERSONAS_AUTO ? t(node, "personasAuto") : val === PERSONAS_CUSTOM ? t(node, "personasCustom") : val;
            peopleSel.appendChild(o);
        }
        const allowed = new Set(PERSONAS_OPTIONS);
        peopleSel.value = allowed.has(keep) ? keep : (allowed.has(String(widgetValue(node, "num_personas", "1"))) ? String(widgetValue(node, "num_personas", "1")) : "1");
        peopleCustom.style.display = peopleSel.value === PERSONAS_CUSTOM ? "" : "none";
    };
    peopleCustom.value = String(widgetValue(node, "num_personas_custom", 1) || 1);
    refreshPeopleOpts();
    const savedP = String(widgetValue(node, "num_personas", "1") || "1");
    if ([...peopleSel.options].some((o) => o.value === savedP)) peopleSel.value = savedP;
    peopleCustom.style.display = peopleSel.value === PERSONAS_CUSTOM ? "" : "none";
    peopleSel.addEventListener("change", () => {
        peopleCustom.style.display = peopleSel.value === PERSONAS_CUSTOM ? "" : "none";
    });
    peopleRow.append(peopleSel, peopleCustom);
    let ropaSel = null;
    let pairRowEl = null;
    let pasadasRow = null;
    const refreshPasadas = () => {
        if (!pasadasRow) return;
        const cur = normalizePasadas(widgetValue(node, "pasadas", PASADAS_1));
        for (const b of pasadasRow.querySelectorAll("button")) b.classList.toggle("on", b.dataset.pasadas === cur);
    };
    if (includeIdea) {
        // Ropa + N° de personas side by side in the right column (where the
        // LLM activity box used to be; that box now lives in the Config node).
        const ropaLabel = styleEl("div", {}, t(node, "ropa"));
        ropaLabel.className = "ld-label";
        ropaLabel.dataset.i18n = "ropa";
        ropaSel = document.createElement("select");
        ropaSel.className = "ld-select";
        ropaSel.title = t(node, "ropaTitle");
        ropaSel.dataset.i18nTitle = "ropaTitle";
        for (const val of ROPA_OPTIONS) {
            const o = document.createElement("option");
            o.value = val;
            o.textContent = t(node, ROPA_I18N[val]);
            ropaSel.appendChild(o);
        }
        const savedR = normalizeRopa(widgetValue(node, "modo_ropa", ROPA_AUTO));
        ropaSel.value = savedR;
        const rwInit = widgetByName(node, "modo_ropa");
        if (rwInit && rwInit.value !== savedR) rwInit.value = savedR;
        const ropaStack = styleEl("div", {});
        ropaStack.className = "ld-field-stack";
        ropaStack.append(ropaLabel, ropaSel);
        const peopleStack = styleEl("div", {});
        peopleStack.className = "ld-field-stack";
        peopleStack.append(peopleLabel, peopleRow);
        const pairRow = styleEl("div", {});
        pairRow.className = "ld-pair-row ld-pair-low";
        pairRow.append(ropaStack, peopleStack);
        // 1 pasada / 2 pasadas segmented toggle, above Ropa + Participantes.
        pasadasRow = styleEl("div", {});
        pasadasRow.className = "ld-pasadas-row";
        pasadasRow.title = t(node, "pasadasTitle");
        pasadasRow.dataset.i18nTitle = "pasadasTitle";
        for (const [val, key] of [[PASADAS_1, "pasadas1"], [PASADAS_2, "pasadas2"]]) {
            const b = styleEl("button", {}, t(node, key));
            b.type = "button";
            b.className = "ld-switch";
            b.dataset.i18n = key;
            b.dataset.pasadas = val;
            b.addEventListener("click", () => {
                const w = widgetByName(node, "pasadas");
                if (w) w.value = val;
                refreshPasadas();
                node.graph?.setDirtyCanvas?.(true);
            });
            pasadasRow.appendChild(b);
        }
        const pairWrap = styleEl("div", { display: "flex", flexDirection: "column", gap: "6px", width: "100%" });
        pairWrap.append(pasadasRow, pairRow);
        pairRowEl = pairWrap;
        if (useNote && useNote.parentNode === right) right.insertBefore(pairWrap, useNote);
        else right.appendChild(pairWrap);
    } else {
        midR.append(peopleLabel, peopleRow);
    }
    mid.append(posRow, midR);
    // Ropa chips drive the selector: any chip on -> Foto; all off -> back to
    // LoRA. Desnudo is never changed automatically.
    const anyRopaChipOn = () => {
        for (let k = 1; k <= N_IMAGES; k++) {
            if (widgetValue(node, `img${k}_ropa`, false)) return true;
        }
        return false;
    };
    const autoRopaFromChips = () => {
        if (!ropaSel) return;
        const cur = normalizeRopa(ropaSel.value);
        let next = cur;
        if (cur === ROPA_DESNUDO) return;
        if (anyRopaChipOn()) next = ROPA_FOTO;
        else if (cur === ROPA_FOTO) next = ROPA_AUTO;
        if (next !== ropaSel.value) {
            ropaSel.value = next;
            const rw = widgetByName(node, "modo_ropa");
            if (rw) rw.value = next;
        }
    };

    const grid = styleEl("div", {});
    grid.className = "ld-img-grid";
    const cols = [];
    for (let i = 1; i <= N_IMAGES; i++) {
        const col = styleEl("div", {});
        col.className = "ld-img-col";
        const title = styleEl("div", {}, t(node, "imagen", { n: i })); title.dataset.i18n = "imagen"; title.dataset.i18nN = String(i);
        title.className = "ld-label";
        col.appendChild(title);
        const chips = styleEl("div", {});
        chips.className = "ld-chip-row";
        const chipMap = {};
        for (const key of ASPECT_KEYS) {
            const chip = styleEl("button", {}, aspectLabel(node, key));
            chip.type = "button";
            chip.className = "ld-chip";
            chip.dataset.aspect = key;
            chip.addEventListener("click", () => {
                const w = widgetByName(node, `img${i}_${key}`);
                const next = !(w ? w.value : chip.classList.contains("on"));
                if (w) w.value = next;
                chip.classList.toggle("on", next);
                if (key === "ropa") autoRopaFromChips();
                node.graph?.setDirtyCanvas?.(true);
            });
            chips.appendChild(chip);
            chipMap[key] = chip;
        }
        col.appendChild(chips);
        const thumb = styleEl("div", {});
        thumb.className = "ld-thumb";
        const ph = styleEl("div", {}, t(node, "thumbPh")); ph.dataset.i18n = "thumbPh";
        ph.className = "ld-thumb-ph";
        const imgEl = document.createElement("img");
        imgEl.alt = "";
        imgEl.style.display = "none";
        const badge = styleEl("div", {}, t(node, "connected")); badge.dataset.i18n = "connected";
        badge.className = "ld-thumb-badge";
        badge.style.display = "none";
        const pickBtn = styleEl("button", {}, "📂");
        pickBtn.type = "button";
        pickBtn.className = "ld-thumb-pick";
        pickBtn.title = t(node, "pickTitle"); pickBtn.dataset.i18nTitle = "pickTitle";
        const clearBtn = styleEl("button", {}, "✖");
        clearBtn.type = "button";
        clearBtn.className = "ld-thumb-clear";
        clearBtn.title = t(node, "clearTitle"); clearBtn.dataset.i18nTitle = "clearTitle";
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
                setStatus(`❌ ${err.message || t(node, "uploadFail")}`);
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
                setStatus(t(node, "connectedWarn"));
                return;
            }
            const file = ev.dataTransfer?.files?.[0];
            if (!file) return;
            try {
                const info = await uploadInputImage(file);
                setArchivo(info);
            } catch (err) {
                setStatus(`❌ ${err.message || t(node, "uploadFail")}`);
            }
        });
        const desc = makeTextarea(t(node, "descPh"), "0 0 60px"); desc.dataset.i18nPh = "descPh";
        desc.className = "ld-textarea ld-desc";
        Object.assign(desc.style, { height: "60px", minHeight: "60px", maxHeight: "60px", overflow: "auto", resize: "none", flex: "0 0 60px" });
        desc.readOnly = true;
        col.appendChild(desc);
        const dBtn = styleEl("button", {}, t(node, "describir")); dBtn.dataset.i18n = "describir";
        dBtn.type = "button";
        dBtn.className = "ld-btn ld-btn-small";
        col.appendChild(dBtn);
        grid.appendChild(col);
        cols.push({ index: i, desc, button: dBtn, chips: chipMap, refreshThumb });
    }

    let writerHead = null;
    if (false) {
        writerHead = styleEl("div", {}, "");
        writerHead.className = "ld-writer-head";
        const titleEl = styleEl("div", {}, t(node, "writerTitle"));
        titleEl.className = "ld-writer-head-title";
        titleEl.dataset.i18n = "writerTitle";
        writerHead.appendChild(titleEl);
    }
    const foldAjustes = styleEl("button", {}, "");
    foldAjustes.type = "button";
    foldAjustes.className = "ld-fold";
    const foldImagenes = styleEl("button", {}, "");
    foldImagenes.type = "button";
    foldImagenes.className = "ld-fold";
    const refreshFolds = () => {
        const hideA = !!widgetValue(node, "ocultar_ajustes", false);
        const hideI = !!widgetValue(node, "ocultar_imagenes", false);
        foldAjustes.textContent = (hideA ? "▸ " : "▾ ") + t(node, "ajustes");
        foldImagenes.textContent = (hideI ? "▸ " : "▾ ") + t(node, "seccionImagenes");
        left.style.display = hideA ? "none" : "";
        if (typeof useNote !== "undefined" && useNote) useNote.style.display = hideA ? "none" : "";
        if (pairRowEl) pairRowEl.style.display = hideA ? "none" : "";
        grid.style.display = hideI ? "none" : "";
        left.style.flex = hideA ? "0 0 0" : "1 1 42%";
        right.style.flex = hideA ? "1 1 auto" : "1 1 58%";
    };
    foldAjustes.addEventListener("click", () => {
        const w = widgetByName(node, "ocultar_ajustes");
        if (w) w.value = !w.value;
        refreshFolds();
        scheduleWriterResize(node);
        node.graph?.setDirtyCanvas?.(true);
    });
    foldImagenes.addEventListener("click", () => {
        const w = widgetByName(node, "ocultar_imagenes");
        if (w) w.value = !w.value;
        refreshFolds();
        scheduleWriterResize(node);
        node.graph?.setDirtyCanvas?.(true);
    });
    if (includeIdea) {
        top.append(left, right);
        if (writerHead) {
            // Transparent band under the title where LiteGraph draws the config connector.
            const slotGap = styleEl("div", {}, "");
            slotGap.className = "ld-writer-slot-gap";
            root.append(writerHead, slotGap, foldAjustes, top, mid, foldImagenes, grid);
        }
        else root.append(foldAjustes, top, mid, foldImagenes, grid);
        refreshFolds();
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
        const nwP = widgetByName(node, "num_personas");
        if (peopleSel && nwP) {
            const pv = String(nwP.value ?? "1");
            if (peopleSel.value !== pv) peopleSel.value = pv;
            if (peopleCustom) peopleCustom.style.display = peopleSel.value === PERSONAS_CUSTOM ? "" : "none";
        }
        const nwC = widgetByName(node, "num_personas_custom");
        if (peopleCustom && nwC && String(peopleCustom.value) !== String(nwC.value ?? 1)) {
            peopleCustom.value = String(nwC.value ?? 1);
        }
        refreshPasadas();
        const rw = widgetByName(node, "modo_ropa");
        if (ropaSel) {
            const want = normalizeRopa(rw?.value ?? ROPA_AUTO);
            if (rw && rw.value !== want) rw.value = want;
            if (ropaSel.value !== want) ropaSel.value = want;
        }
        const cw = widgetByName(node, "camara");
        if (includeIdea && camSel && cw) {
            const cv = String(cw.value ?? CAMARA_AUTO);
            if (camSel.value !== cv) camSel.value = cv;
        }
        if (includeIdea && useBox && uw) useBox.checked = !!uw.value;
        if (vistaEsArea) {
            const savedVista = String(node.properties?.ld_vista_es ?? "");
            if (vistaEsArea.value !== savedVista) vistaEsArea.value = savedVista;
        }
        applyVistaVisibility(node);
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
        const nwP = widgetByName(node, "num_personas");
        if (peopleSel && nwP) nwP.value = peopleSel.value;
        const nwC = widgetByName(node, "num_personas_custom");
        if (peopleCustom && nwC) {
            const n = parseInt(peopleCustom.value, 10);
            nwC.value = Number.isFinite(n) && n >= 1 ? n : 1;
        }
        const cw = widgetByName(node, "camara");
        if (includeIdea && camSel && cw) cw.value = camSel.value;
        const rw = widgetByName(node, "modo_ropa");
        if (ropaSel && rw) rw.value = ropaSel.value;
        for (const col of cols) {
            const dw = widgetByName(node, `desc_imagen_${col.index}`);
            if (dw) dw.value = col.desc.value;
        }
        node.graph?.setDirtyCanvas?.(true);
    };
    pos.addEventListener("input", () => {
        syncToWidgets();
        markPosDirty(node, true);
    });
    vistaEsArea.addEventListener("input", () => {
        markVistaDirty(node, true);
    });
    neg.addEventListener("input", syncToWidgets);
    ideaArea?.addEventListener("input", syncToWidgets);
    estiloSel?.addEventListener("change", syncToWidgets);
    useBox?.addEventListener("change", syncToWidgets);
    peopleSel?.addEventListener("change", syncToWidgets);
    peopleCustom?.addEventListener("input", syncToWidgets);
    camSel?.addEventListener("change", syncToWidgets);
    ropaSel?.addEventListener("change", syncToWidgets);

    for (const col of cols) {
        col.button.addEventListener("click", async () => {
            const img = refImageInfo(node, col.index);
            if (!img) {
                setStatus(t(node, "noImage", { n: col.index }));
                return;
            }
            const cfgNode = findUpstreamConfig(node);
            const cfg = readConfigValues(cfgNode);
            if (!cfg) {
                setStatus(t(node, "missingCfg"));
                return;
            }
            setStatus(t(node, "describing", { n: col.index }));
            col.button.disabled = true;
            try {
                const aspects = aspectListForImage(node, col.index);
                const data = await postDescribe({
                    url: cfg.url,
                    model: cfg.model,
                    image: img,
                    aspects,
                    index: col.index,
                    temperature: 0.3,
                    max_tokens: 400,
                    unload_after: false,
                    descarga_idle_min: cfg.descarga_idle_min || 0,
                    idioma: cfg.idioma || "Español",
                });
                if (!data?.ok) {
                    setStatus(data?.message || t(node, "describeFail", { n: col.index }));
                    return;
                }
                setImageDescription(node, col.index, data.description || "", data.aspects || aspectSignature(node, col.index));
                syncToWidgets();
                setStatus(t(node, "described", { n: col.index }));
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
        setVistaEs(node, "");
        node.properties = node.properties || {};
        node.properties.ld_desc_meta = {};
        node.properties.ld_pos_dirty = false;
        node.properties.ld_vista_es_dirty = false;
        for (const col of cols) {
            col.desc.value = "";
            const aw = widgetByName(node, `archivo_imagen_${col.index}`);
            if (aw) aw.value = "";
            for (const [key, chip] of Object.entries(col.chips || {})) {
                const cw = widgetByName(node, `img${col.index}_${key}`);
                if (cw) cw.value = false;
                chip.classList.remove("on");
            }
            col.refreshThumb?.();
        }
        // Dropdowns back to their Python defaults (not Config, LoRA, switches or i2i).
        if (estiloSel) estiloSel.value = ESTILO_SALIDA_DEFAULT;
        if (camSel) camSel.value = CAMARA_AUTO;
        if (peopleSel) peopleSel.value = "1";
        if (peopleCustom) {
            peopleCustom.value = "1";
            peopleCustom.style.display = "none";
        }
        if (ropaSel) ropaSel.value = ROPA_AUTO;
        for (const [name, val] of [
            ["estilo_salida", ESTILO_SALIDA_DEFAULT],
            ["camara", CAMARA_AUTO],
            ["num_personas", "1"],
            ["num_personas_custom", 1],
            ["modo_ropa", ROPA_AUTO],
            ["usar_imagen_1", "todo"],
            ["usar_imagen_2", "todo"],
            ["pasadas", PASADAS_1],
        ]) {
            const w = widgetByName(node, name);
            if (w) w.value = val;
        }
        refreshPasadas();
        syncToWidgets();
        if (cambiosInput) cambiosInput.value = "";
        status.textContent = "";
        status.className = "ld-status";
        setStatus(t(node, "cleared"));
    });

    btn.addEventListener("click", async () => {
        setStatus("⏳ Generando...");
        btn.disabled = true;
        try {
            syncToWidgets();
            const used = await resolveEditedPrompts(node, { setStatus, pos });
            if (used) {
                syncToWidgets();
                return;
            }
            await ensureImageDescriptions(node, { setStatus });
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

    const applyI18n = () => {
        root.querySelectorAll("[data-i18n]").forEach((el) => {
            const key = el.dataset.i18n;
            const n = el.dataset.i18nN;
            el.textContent = n ? t(node, key, { n }) : t(node, key);
        });
        root.querySelectorAll("[data-i18n-ph]").forEach((el) => {
            el.placeholder = t(node, el.dataset.i18nPh);
        });
        root.querySelectorAll("[data-i18n-title]").forEach((el) => {
            el.title = t(node, el.dataset.i18nTitle);
        });
        for (const col of cols) {
            for (const key of ASPECT_KEYS) {
                if (col.chips[key]) col.chips[key].textContent = aspectLabel(node, key);
            }
        }
        if (camSel) {
            for (const o of camSel.options) o.textContent = camaraLabel(node, o.value);
        }
        if (ropaSel) {
            for (const o of ropaSel.options) o.textContent = t(node, ROPA_I18N[o.value] || "ropaAuto");
        }
        if (peopleSel) {
            for (const o of peopleSel.options) {
                o.textContent = o.value === PERSONAS_AUTO ? t(node, "personasAuto") : o.value === PERSONAS_CUSTOM ? t(node, "personasCustom") : o.value;
            }
        }
        applyVistaVisibility(node);
        refreshFolds();
        scheduleWriterResize(node);
    };

    applyVistaVisibility(node);
    if (vistaEsArea) {
        const savedVista = String(node.properties?.ld_vista_es ?? "");
        if (savedVista) vistaEsArea.value = savedVista;
    }

    return { root, pos, neg, ideaArea, estiloSel, peopleSel, ropaSel, camSel, setStatus, syncFromWidgets, syncToWidgets, btn, applyI18n, vistaEsArea, vistaWrap, cols };
}

const WRITER_HEAD_H = 28;
const WRITER_SLOT_Y = 14;
// Title strip (28) + its bottom margin (2) + flex gap (8) + half of the 12px slot gap.
const WRITER_SLOT_IN_PANEL = 28 + 2 + 8 + 6;

function writerSlotY(node) {
    let top = NaN;
    try {
        const w = widgetByName(node, "ld_writer_panel");
        top = Number(w?.last_y ?? w?.y);
    } catch (_e) {}
    if (!Number.isFinite(top)) top = Number(node?.widgets_start_y ?? 2) || 2;
    return top + WRITER_SLOT_IN_PANEL;
}

function setWriterWidgetsStart(node) {
    // Native layout (same as the Config node): LiteGraph title, config slot
    // under it, panel right after the slot row.
    try {
        if (node && node.widgets_start_y === 2) delete node.widgets_start_y;
    } catch (_e) {}
}

function visibleHeaderHeight(node) {
    const typ = String(node?.type || node?.comfyClass || "");
    if (typ === "LD_LMStudioPromptWriterV2") {
        let sh = 20;
        try {
            if (typeof LiteGraph !== "undefined" && LiteGraph.NODE_SLOT_HEIGHT) sh = LiteGraph.NODE_SLOT_HEIGHT;
        } catch (_e) {}
        return sh + 8;
    }
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
        if (message && Object.prototype.hasOwnProperty.call(message, "vista_es")) {
            const v = Array.isArray(message.vista_es) ? message.vista_es[0] : message.vista_es;
            setVistaEs(this, v ?? "");
        }
        this._ldPanel?.syncFromWidgets();
    };
}

function attachConfigActivityLog(node) {
    if (node._ldLogDom) return;
    const wrap = styleEl("div", {});
    wrap.className = "ld-panel ld-config ld-log-wrap ld-log-config";
    const logLabel = styleEl("div", {}, t(node, "actividad"));
    logLabel.className = "ld-label";
    const logBox = styleEl("div", {});
    logBox.className = "ld-log";
    logBox.setAttribute("aria-readonly", "true");
    wrap.append(logLabel, logBox);
    const dom = node.addDOMWidget("ld_activity_log", "div", wrap, {
        hideOnZoom: false,
        serialize: false,
    });
    dom.serialize = false;
    dom.computeSize = (width) => [width || 200, 120];
    node._ldLogDom = dom;
    node._ldLogLabel = logLabel;
    node._ldLogBox = logBox;
    const prevI18n = node._ldRefreshI18n;
    node._ldRefreshI18n = () => {
        prevI18n?.();
        if (node._ldLogLabel) node._ldLogLabel.textContent = t(node, "actividad");
    };
    hookActivityLog();
}

function growConfigToFit(node) {
    try {
        const min = typeof node.computeSize === "function" ? node.computeSize() : null;
        if (!min || !node.size) return;
        if (node.size[1] < min[1]) {
            if (typeof node.setSize === "function") node.setSize([node.size[0], min[1]]);
            else node.size[1] = min[1];
            node.graph?.setDirtyCanvas?.(true, true);
        }
    } catch (_e) {}
}

function setupConfigNode(nodeType) {
    installSafeHook(nodeType, "onNodeCreated", function () {
        ensureThemeStyles();
        applyNodeTheme(this, THEME.config);
        const setStatus = attachStatusLine(this, true, "config");
        attachModelRefresh(this, setStatus);
        attachConfigActivityLog(this);
        shrinkExtraInstructions(this);
        hookIdiomaWidget(this);
        if (findModeloGen()) hideWidget(widgetByName(this, "idioma"));
        if (!this.size || this.size[1] < 900) {
            if (typeof this.setSize === "function") this.setSize([400, 940]);
            else this.size = [400, 940];
        }
    });
    installSafeHook(nodeType, "onConfigure", function (info) {
        repairNodeWidgets(this);
        applyNodeTheme(this, THEME.config);
        const combo = widgetByName(this, "model");
        if (combo && isAuto(combo.value)) combo.value = AUTO_MODEL;
        shrinkExtraInstructions(this);
        hookIdiomaWidget(this);
        if (findModeloGen()) hideWidget(widgetByName(this, "idioma"));
        this._ldRefreshModels?.(false);
        refreshAllWriterI18n();
        // Saved workflows keep their size; grow only the height if the new
        // activity box below "Probar conexión" doesn't fit.
        setTimeout(() => growConfigToFit(this), 0);
    });
}

function shrinkExtraInstructions(node) {
    const w = widgetByName(node, "extra_instructions");
    if (!w) return;
    w.computeSize = (width) => [width || 200, 52];
    if (w.inputEl) {
        w.inputEl.style.minHeight = "36px";
        w.inputEl.style.height = "40px";
        w.inputEl.style.maxHeight = "52px";
    }
}

function hookIdiomaWidget(node) {
    const w = widgetByName(node, "idioma");
    if (!w || w._ldIdiomaHooked) return;
    w._ldIdiomaHooked = true;
    if (w.label !== undefined) w.label = "idioma";
    const orig = w.callback;
    w.callback = function (...args) {
        orig?.apply(this, args);
        const idioma = String(w.value || "Español");
        if (node.type === MODELO_GEN) syncIdiomaToConfig(idioma);
        if (node.type === CONFIG_NODE) {
            const sel = findModeloGen();
            const sw = sel && widgetByName(sel, "idioma");
            if (sw && sw.value !== idioma) sw.value = idioma;
        }
        refreshAllWriterI18n();
        node.graph?.setDirtyCanvas?.(true);
    };
}

function refreshAllWriterI18n() {
    const nodes = app.graph?._nodes || app.graph?.nodes || [];
    for (const n of nodes) {
        n._ldPanel?.applyI18n?.();
        n._ldRefreshI18n?.();
    }
    applyNotesI18n();
}

function applyBranchMode(modelo) {
    const want = String(modelo || "Krea2");
    const modeName = want === "Illustrious" ? "Illustrious (tags)" : "Krea2 (natural)";
    const nodes = app.graph?._nodes || app.graph?.nodes || [];
    for (const n of nodes) {
        if (n.type === CONFIG_NODE) {
            const w = widgetByName(n, "mode");
            if (w && w.value !== modeName) w.value = modeName;
        }
        const br = n.properties?.ld_branch;
        if (!br) continue;
        const on = (br === "illustrious") === (want === "Illustrious");
        n.mode = on ? 0 : 2; // 2 = mute
    }
    app.graph?.setDirtyCanvas?.(true, true);
}

function setupModeloGen(nodeType) {
    const paint = (node) => applyNodeTheme(node, { color: "#473122", bgcolor: "#1b222b" });
    const ensureUi = (node) => {
        paint(node);
        hideWidget(widgetByName(node, "modelo"));
        hideWidget(widgetByName(node, "idioma"));
        hookIdiomaWidget(node);
        if (node._ldModeloUi) {
            node._ldRefreshI18n?.();
            return;
        }
        const root = styleEl("div", {});
        root.className = "ld-modelo-panel";
        const langLabel = styleEl("div", {}, t(node, "idioma") === "idioma" ? "Idioma" : t(node, "idioma"));
        langLabel.className = "ld-label";
        langLabel.dataset.i18n = "idiomaSel";
        langLabel.textContent = currentLangFrom(node) === "en" ? "Language" : "Idioma";
        const langSel = document.createElement("select");
        langSel.className = "ld-select";
        for (const [val, es, en] of [["Español", "Español", "Spanish"], ["English", "English", "English"]]) {
            const o = document.createElement("option");
            o.value = val;
            o.textContent = currentLangFrom(node) === "en" ? en : es;
            langSel.appendChild(o);
        }
        langSel.value = String(widgetValue(node, "idioma", "Español") || "Español");
        langSel.addEventListener("change", () => {
            const w = widgetByName(node, "idioma");
            if (w) w.value = langSel.value;
            syncIdiomaToConfig(langSel.value);
            refreshAllWriterI18n();
            node.graph?.setDirtyCanvas?.(true, true);
        });
        const row = styleEl("div", {});
        row.className = "ld-switch-row";
        const mkSwitch = (value, label) => {
            const b = styleEl("button", {}, label);
            b.type = "button";
            b.className = "ld-switch";
            b.dataset.modelo = value;
            b.addEventListener("click", () => {
                const w = widgetByName(node, "modelo");
                if (w) w.value = value;
                refreshSw();
                applyBranchMode(value);
                node.graph?.setDirtyCanvas?.(true, true);
            });
            return b;
        };
        const swK = mkSwitch("Krea2", "Krea2");
        const swI = mkSwitch("Illustrious", "Illustrious");
        row.append(swK, swI);
        const refreshSw = () => {
            const cur = String(widgetValue(node, "modelo", "Krea2") || "Krea2");
            const il = cur !== "Krea2" && /illust/i.test(cur);
            swK.classList.toggle("on", !il);
            swI.classList.toggle("on", il);
        };
        root.append(langLabel, langSel, row);
        const mw = widgetByName(node, "modelo");
        if (mw) {
            const orig = mw.callback;
            mw.callback = (...args) => {
                orig?.apply(this, args);
                refreshSw();
                applyBranchMode(mw.value);
            };
        }
        const dom = node.addDOMWidget("ld_modelo_ui", "div", root, { serialize: false });
        if (dom) {
            dom.serialize = false;
            dom.computeSize = (width) => [width || 200, 96];
        }
        // idioma first visually: DOM already starts with language, then switches.
        node._ldModeloUi = root;
        node._ldRefreshI18n = () => {
            langLabel.textContent = currentLangFrom(node) === "en" ? "Language" : "Idioma";
            const map = { Español: currentLangFrom(node) === "en" ? "Spanish" : "Español", English: "English" };
            for (const o of langSel.options) o.textContent = map[o.value] || o.value;
            langSel.value = String(widgetValue(node, "idioma", "Español") || "Español");
            refreshSw();
        };
        refreshSw();
        hookIdiomaWidget(node);
    };
    installSafeHook(nodeType, "onNodeCreated", function () {
        ensureUi(this);
        setTimeout(() => {
            applyBranchMode(widgetValue(this, "modelo", "Krea2"));
            applyNotesI18n();
        }, 50);
        if (!this.size || this.size[0] < 400) {
            if (typeof this.setSize === "function") this.setSize([420, 220]);
            else this.size = [420, 220];
        }
    });
    installSafeHook(nodeType, "onConfigure", function (info) {
        repairNodeWidgets(this);
        ensureUi(this);
        applyBranchMode(widgetValue(this, "modelo", "Krea2"));
        applyNotesI18n();
    });
}


const WRITER_NODE_W = 1320;
const WRITER_NODE_H = 800;
const WRITER_NODE_H_MAX = 2000;
const WRITER_PANEL_H_MIN = 260;

const WRITER_BG_EXTRA = 18;

function scheduleWriterResize(node) {
    if (!node) return;
    if (node._ldResizeTok) cancelAnimationFrame(node._ldResizeTok);
    node._ldResizeTok = requestAnimationFrame(() => {
        node._ldResizeTok = 0;
        const el = node._ldPanel?.root;
        if (!el) return;
        el.style.height = "auto";
        const panelH = Math.max(WRITER_PANEL_H_MIN, Math.ceil(el.scrollHeight || 0));
        // Stretch the background down to the node's bottom edge.
        el.style.height = `${panelH + WRITER_BG_EXTRA}px`;
        if (node._ldPanelH && Math.abs(node._ldPanelH - panelH) < 2) return;
        node._ldPanelH = panelH;
        const nodeH = panelH + visibleHeaderHeight(node) + 4;
        const w = Math.max(1100, Math.min(node.size?.[0] || WRITER_NODE_W, 1800));
        if (!node.size || node.size[0] !== w || Math.abs((node.size[1] || 0) - nodeH) >= 2) {
            if (typeof node.setSize === "function") node.setSize([w, nodeH]);
            else node.size = [w, nodeH];
        }
        const dom = (node.widgets || []).find((x) => x && x.name === "ld_writer_panel");
        if (dom) {
            dom.computeSize = (width) => [width || 0, panelH];
            dom.getMinHeight = () => panelH;
            dom.getMaxHeight = () => panelH;
        }
        node.graph?.setDirtyCanvas?.(true);
    });
}

function clampWriterSize(node) {
    const w = Math.max(1100, Math.min(node.size?.[0] || WRITER_NODE_W, 1800));
    if (node.size && node.size[0] !== w) {
        const h = node.size[1] || WRITER_NODE_H;
        if (typeof node.setSize === "function") node.setSize([w, h]);
        else node.size = [w, h];
    }
    scheduleWriterResize(node);
}

const WRITER_MOVED_INPUTS = new Set([
    "image",
    "image_1", "image_2", "image_3", "image_4",
    "image_5", "image_6", "image_7", "image_8",
    "lora_triggers", "neg_embeddings",
]);

function writerDefinedInputNames(node) {
    const names = new Set(["config"]);
    const data = node?.constructor?.nodeData || {};
    const input = data.input || {};
    for (const group of [input.required, input.optional]) {
        if (group && typeof group === "object") {
            for (const k of Object.keys(group)) names.add(k);
        }
    }
    return names;
}

function cleanupWriterGraphSlots(node) {
    if (!node) return;
    node.properties = node.properties || {};
    node.properties.ld_io_on_config = true;
    const defined = writerDefinedInputNames(node);
    const inputs = node.inputs || [];
    for (let i = inputs.length - 1; i >= 0; i--) {
        const inp = inputs[i];
        if (!inp) continue;
        const name = String(inp.name || "");
        if (name === "config") continue;
        if (inp.widget) continue;
        const connected = inp.link != null;
        const stale = WRITER_MOVED_INPUTS.has(name) || !defined.has(name);
        if (!connected && stale) {
            if (typeof node.removeInput === "function") node.removeInput(i);
            else inputs.splice(i, 1);
        }
    }
    for (const inp of node.inputs || []) {
        if (!inp || inp.widget) continue;
        if (inp.name === "config") {
            inp.hidden = false;
            try { delete inp.pos; } catch (_e) {}
        } else {
            inp.hidden = inp.link == null;
        }
    }
    while (node.outputs && node.outputs.length) {
        if (typeof node.removeOutput === "function") node.removeOutput(node.outputs.length - 1);
        else node.outputs.pop();
    }
    node.setDirtyCanvas?.(true, true);
}

function liteGraphNoTitle() {
    return (typeof LiteGraph !== "undefined" && LiteGraph.NO_TITLE != null) ? LiteGraph.NO_TITLE : 1;
}

function propertyCanBeSet(obj, name) {
    if (obj == null) return false;
    let cur = obj;
    while (cur && cur !== Object.prototype) {
        let desc = null;
        try {
            desc = Object.getOwnPropertyDescriptor(cur, name);
        } catch (_e) {
            return false;
        }
        if (desc) {
            if (typeof desc.set === "function") return true;
            if (Object.prototype.hasOwnProperty.call(desc, "writable")) return !!desc.writable;
            if (typeof desc.get === "function" && !desc.set) return false;
            return false;
        }
        try {
            cur = Object.getPrototypeOf(cur);
        } catch (_e) {
            return false;
        }
    }
    return true;
}

function trySetTitleMode(target, value) {
    if (!target) return false;
    try {
        if (!propertyCanBeSet(target, "title_mode")) return false;
        target.title_mode = value;
        return true;
    } catch (_e) {
        return false;
    }
}

function applyWriterTypeChrome(nodeType) {
    if (!nodeType) return;
    const noTitle = liteGraphNoTitle();
    try {
        trySetTitleMode(nodeType, noTitle);
    } catch (_e) {}
    try {
        trySetTitleMode(nodeType.prototype, noTitle);
    } catch (_e) {}
}

function hideWriterTitleBarFallback(node) {
    if (!node) return;
    try {
        node.flags = node.flags || {};
    } catch (_e) {}
    if (node._ldTitleBarNoop) return;
    try {
        node.onDrawTitleBar = function () {
            // Custom DOM title lives in the panel; do not draw the LiteGraph title bar.
        };
        node._ldTitleBarNoop = true;
    } catch (_e) {}
}

function applyWriterChrome(node) {
    if (!node) return;
    // Never assign instance.title_mode: in current ComfyUI it can be a
    // getter-only property and throws TypeError, aborting workflow load.
    try {
        if (node._ldTitleBarNoop) {
            delete node.onDrawTitleBar;
            node._ldTitleBarNoop = false;
        }
    } catch (_e) {}
    try {
        cleanupWriterGraphSlots(node);
    } catch (err) {
        console.warn("[LD-PromptWriter] cleanupWriterGraphSlots:", err);
    }
}

function installSafeHook(nodeType, hookName, fn) {
    const orig = nodeType.prototype[hookName];
    nodeType.prototype[hookName] = function (...args) {
        try {
            if (typeof orig === "function") orig.apply(this, args);
        } catch (err) {
            console.warn(`[LD-PromptWriter] ${hookName} (original):`, err);
        }
        try {
            return fn.apply(this, args);
        } catch (err) {
            console.warn(`[LD-PromptWriter] ${hookName}:`, err);
        }
    };
}

function repairI2IWidgets(node) {
    const typ = String(node?.type || node?.comfyClass || "");
    if (typ !== "LD_ImagenBaseI2I") return;
    const modeloW = widgetByName(node, "modelo");
    const denoiseW = widgetByName(node, "denoise");
    if (modeloW || !denoiseW) return;
    const wv = Array.isArray(node.widgets_values) ? node.widgets_values : null;
    const isModelo = (v) => /^(krea2|illustrious)$/i.test(String(v ?? "").trim());
    if (wv && wv.length >= 4 && isModelo(wv[0])) {
        const stepsW = widgetByName(node, "steps_krea2");
        const archW = widgetByName(node, "archivo");
        denoiseW.value = wv[1];
        if (stepsW) stepsW.value = wv[2];
        if (archW) archW.value = wv[3];
        node.widgets_values = wv.slice(1);
        return;
    }
    if (isModelo(denoiseW.value)) {
        const stepsW = widgetByName(node, "steps_krea2");
        const archW = widgetByName(node, "archivo");
        denoiseW.value = stepsW ? stepsW.value : 0.6;
        if (stepsW) stepsW.value = archW ? archW.value : 8;
        if (archW && (typeof archW.value === "number" || /^\d+$/.test(String(archW.value)))) {
            archW.value = "";
        }
    }
}

function setupWriterV2(nodeType) {
    const origComputeSize = nodeType.prototype.computeSize;
    nodeType.prototype.computeSize = function () {
        const panelH = this._ldPanelH || WRITER_NODE_H;
        return [this.size?.[0] || WRITER_NODE_W, panelH + visibleHeaderHeight(this) + 4];
    };

    const hideWriterWidgets = (node) => {
        for (const w of node.widgets || []) {
            if (!w || w.name === "ld_writer_panel") continue;
            hideWidget(w);
        }
    };

    const hideWriterGraphSlots = (node) => {
        applyWriterChrome(node);
    };

    installSafeHook(nodeType, "onNodeCreated", function () {
        ensureThemeStyles();
        applyNodeTheme(this, THEME.writer);
        setWriterWidgetsStart(this);
        hideWriterWidgets(this);
        hideWriterGraphSlots(this);
        migrateAccionPoseSplit(this);

        const panel = buildWriterPanel(this, {
            includeIdea: true,
            tone: "writer",
            onGenerate: async ({ setStatus, pos, neg, syncToWidgets }) => {
                const cfgNode = findUpstreamConfig(this);
                const cfg = readConfigValues(cfgNode);
                if (!cfg) {
                    setStatus(t(this, "missingCfg"));
                    return;
                }
                const idea = String(widgetValue(this, "idea", "")).trim();
                const refs = {};
                let n = 0;
                for (let i = 1; i <= N_IMAGES; i++) {
                    const img = refImageInfo(this, i);
                    if (img) {
                        refs[i] = img;
                        n += 1;
                    }
                }
                if (!idea && !n) {
                    setStatus(t(this, "missingIdea"));
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
                    idioma: cfg.idioma || "Español",
                    num_personas: String(widgetValue(this, "num_personas", "1") || "1"),
                    num_personas_custom: widgetValue(this, "num_personas_custom", 1),
                    camara: String(widgetValue(this, "camara", CAMARA_AUTO) || CAMARA_AUTO),
                    modo_ropa: normalizeRopa(widgetValue(this, "modo_ropa", ROPA_AUTO)),
                    pasadas: normalizePasadas(widgetValue(this, "pasadas", PASADAS_1)),
                };
                for (let i = 1; i <= N_IMAGES; i++) {
                    const img = refs[i];
                    if (img) {
                        body[`image_${i}`] = img;
                        body[`archivo_imagen_${i}`] = serializeArchivo(img);
                    }
                    body[`desc_imagen_${i}`] = String(widgetValue(this, `desc_imagen_${i}`, "") || "");
                    body[`desc_aspects_${i}`] = aspectSignature(this, i);
                    const active = readImageAspects(this, i);
                    aspects[String(i)] = active;
                    for (const k of ASPECT_KEYS) {
                        body[`img${i}_${k}`] = !!widgetValue(this, `img${i}_${k}`, false);
                    }
                }
                body.aspects = aspects;
                if (triggerInfo.text) body.lora_triggers = triggerInfo.text;
                if (body.pasadas === PASADAS_2) setStatus(t(this, "generating2"));
                else setStatus(n > 1 ? t(this, "generatingN", { n }) : t(this, "generating"));
                console.log("[LD-PromptWriter] POST /generate con", n, "imagen(es)", body);
                let data;
                try {
                    data = await postGenerate(body);
                } catch (err) {
                    setStatus(`❌ ${err.message}`);
                    return;
                }
                if (!data?.ok) {
                    setStatus(data?.message || t(this, "genFail"));
                    return;
                }
                pos.value = data.positive || "";
                neg.value = data.negative || "";
                setVistaEs(this, data.vista_es || "");
                syncToWidgets();
                if (!triggerInfo.text && (triggerInfo.source === "unknown" || triggerInfo.source === "loader-no-words")) {
                    setStatus(t(this, "genOkTriggers"));
                } else {
                    setStatus(t(this, "genOk"));
                }
            },
        });
        this._ldPanel = panel;
        this._ldSetStatus = panel.setStatus;
        hookWriterSerialize(this);

        const self = this;
        const dom = this.addDOMWidget("ld_writer_panel", "div", panel.root, {
            hideOnZoom: false,
            serialize: false,
        });
        dom.serialize = false;
        // Height comes from content (cached _ldPanelH). Never read node.size
        // here — that fed back into computeSize and made the node grow.
        const panelH = () => this._ldPanelH || WRITER_PANEL_H_MIN;
        dom.computeSize = (width) => [width || 0, panelH()];
        dom.getMinHeight = () => panelH();
        dom.getMaxHeight = () => panelH();

        panel.syncFromWidgets();
        clampWriterSize(this);
    });

    installSafeHook(nodeType, "onConfigure", function (info) {
        repairNodeWidgets(this);
        applyNodeTheme(this, THEME.writer);
        setWriterWidgetsStart(this);
        hideWriterWidgets(this);
        hideWriterGraphSlots(this);
        migrateAccionPoseSplit(this);
        clampWriterSize(this);
        hookWriterSerialize(this);
        this._ldPanel?.syncFromWidgets();
    });
    const onResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function (size) {
        onResize?.apply(this, arguments);
        if (size && size[1] > WRITER_NODE_H_MAX) size[1] = WRITER_NODE_H_MAX;
    };
    hookExecuted(nodeType);
}

function restoreTamanoWidget(node, name) {
    const w = widgetByName(node, name);
    if (!w) return null;
    // If it was hidden or converted to an input, bring the combo back.
    if (w.origType && String(w.type || "").includes("converted")) {
        w.type = w.origType;
        delete w.origType;
    }
    w.hidden = false;
    w.computedHeight = undefined;
    if (typeof w.computeSize === "function" && w.computeSize([]) && false) {
        /* noop: keep real computeSize unless we hid it */
    }
    if (w._ldHidden) {
        delete w.computeSize;
        delete w._ldHidden;
    }
    if (w.element) w.element.style.display = "";
    return w;
}

function setupTamano(nodeType) {
    const sizeLabel = (node) => {
        const prop = widgetValue(node, "proporcion", "2:3");
        const mp = widgetValue(node, "megapixeles", "1.08 MP");
        const swap = !!widgetValue(node, "intercambiar", false);
        const [w, h] = computeTamano(prop, mp, swap);
        return [w, h, `≈ ${w} × ${h} px`];
    };
    const refresh = (node) => {
        const [w, h, pretty] = sizeLabel(node);
        const res = widgetByName(node, "resultado");
        if (res) res.value = `${w} × ${h}`;
        if (node._ldTamanoEl) node._ldTamanoEl.textContent = pretty;
        const sels = node._ldTamanoSels;
        if (sels) {
            for (const name of ["proporcion", "megapixeles"]) {
                const w = widgetByName(node, name);
                if (sels[name] && w && sels[name].value !== String(w.value)) sels[name].value = String(w.value);
            }
        }
        node._ldTamanoLabel = pretty;
        node.graph?.setDirtyCanvas?.(true);
    };
    const ensureSizeLabel = (node) => {
        if (node._ldTamanoEl && widgetByName(node, "ld_tamano_size")) {
            refresh(node);
            return;
        }
        ensureThemeStyles();
        const box = document.createElement("div");
        box.className = "ld-tamano-box";
        const makeSel = (name, labelEs, labelEn) => {
            const w = widgetByName(node, name);
            const lab = document.createElement("div");
            lab.className = "ld-label";
            lab.textContent = currentLangFrom(node) === "en" ? labelEn : labelEs;
            const sel = document.createElement("select");
            sel.className = "ld-select";
            for (const v of comboOptions(w)) {
                const o = document.createElement("option");
                o.value = String(v);
                o.textContent = String(v);
                sel.appendChild(o);
            }
            sel.value = String(w?.value ?? "");
            sel.addEventListener("change", () => {
                const ww = widgetByName(node, name);
                if (!ww) return;
                ww.value = sel.value;
                try { ww.callback?.(ww.value, app?.canvas, node); } catch (_e) {}
                refresh(node);
            });
            for (const ev of ["pointerdown", "mousedown", "wheel"]) sel.addEventListener(ev, (e) => e.stopPropagation());
            box.append(lab, sel);
            return sel;
        };
        const propSel = makeSel("proporcion", "Proporción", "Aspect ratio");
        const mpSel = makeSel("megapixeles", "Megapíxeles", "Megapixels");
        const el = document.createElement("div");
        el.className = "ld-tamano-size";
        el.textContent = sizeLabel(node)[2];
        box.appendChild(el);
        const dom = node.addDOMWidget("ld_tamano_size", "div", box, { serialize: false });
        if (dom) {
            dom.serialize = false;
            dom.computeSize = (width) => [width || 200, 150];
        }
        node._ldTamanoEl = el;
        node._ldTamanoSels = { proporcion: propSel, megapixeles: mpSel };
        moveWidgetAfter(node, dom, "megapixeles");
        refresh(node);
    };
    const hookWidgets = (node) => {
        for (const name of ["proporcion", "megapixeles", "intercambiar"]) {
            const w = restoreTamanoWidget(node, name);
            if (!w || w._ldTamanoHooked) continue;
            w._ldTamanoHooked = true;
            const orig = w.callback;
            w.callback = function (...args) {
                orig?.apply(this, args);
                refresh(node);
            };
        }
        const res = widgetByName(node, "resultado");
        if (res) {
            res.disabled = true;
            if (res.inputEl) res.inputEl.readOnly = true;
            hideWidget(res);
        }
        ensureSizeLabel(node);
        // The DOM dropdowns replace the canvas combos (values still serialize).
        for (const name of ["proporcion", "megapixeles"]) {
            const w = widgetByName(node, name);
            if (w) { hideWidget(w); w._ldHidden = true; }
        }
        refresh(node);
    };
    installSafeHook(nodeType, "onNodeCreated", function () {
        applyNodeTheme(this, { color: "#44391f", bgcolor: "#1b222b" });
        hookWidgets(this);
        if (!this.size || this.size[0] < 300 || this.size[1] < 220) {
            if (typeof this.setSize === "function") this.setSize([300, 230]);
            else this.size = [300, 230];
        }
    });
    installSafeHook(nodeType, "onConfigure", function (info) {
        repairNodeWidgets(this);
        applyNodeTheme(this, { color: "#44391f", bgcolor: "#1b222b" });
        hookWidgets(this);
    });
    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
        onExecuted?.apply(this, arguments);
        const res = widgetByName(this, "resultado");
        const v = message?.resultado;
        if (res && v != null) res.value = Array.isArray(v) ? v[0] : v;
        refresh(this);
    };
}


function formatEmbeddingToken(name, weight) {
    const base = String(name || "").split(/[\\/]/).pop().replace(/\.(pt|safetensors|bin|pth)$/i, "").trim();
    if (!base || /^\(?ninguno\)?$/i.test(base) || /^\(?none\)?$/i.test(base)) return "";
    const w = Number(weight);
    if (!Number.isFinite(w) || Math.abs(w - 1) < 0.001) return `embedding:${base}`;
    const ws = String(Math.round(w * 1000) / 1000);
    return `(embedding:${base}:${ws})`;
}

function setupEmbeddings(nodeType) {
    installSafeHook(nodeType, "onNodeCreated", function () {
        applyNodeTheme(this, { color: "#3a2a44", bgcolor: "#1b222b" });
        if (this._ldEmbBtn) return;
        const self = this;
        const btn = this.addWidget("button", "➕ Agregar", null, () => {
            const name = widgetValue(self, "embedding", "");
            const peso = widgetValue(self, "peso", 1);
            const token = formatEmbeddingToken(name, peso);
            const lista = widgetByName(self, "lista");
            if (!token || !lista) return;
            const cur = String(lista.value || "").trim();
            const lines = cur ? cur.split(/\n/).map((s) => s.trim()).filter(Boolean) : [];
            if (lines.some((l) => l.toLowerCase() === token.toLowerCase() || l.toLowerCase() === token.toLowerCase().replace(/^embedding:/, ""))) {
                return;
            }
            lista.value = cur ? `${cur}\n${token}` : token;
            self.graph?.setDirtyCanvas?.(true);
        });
        if (btn) {
            btn.serialize = false;
            moveWidgetAfter(self, btn, "peso");
        }
        this._ldEmbBtn = true;
        if (!this.size || this.size[0] < 320) {
            if (typeof this.setSize === "function") this.setSize([411, 220]);
            else this.size = [411, 220];
        }
    });
    installSafeHook(nodeType, "onConfigure", function (info) {
        repairNodeWidgets(this);
        applyNodeTheme(this, { color: "#3a2a44", bgcolor: "#1b222b" });
    });
}

function setupOldWriter(nodeType) {
    installSafeHook(nodeType, "onNodeCreated", function () {
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
                    setStatus(t(this, "missingIdea"));
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
                    setStatus(data?.message || t(this, "genFail"));
                    return;
                }
                pos.value = data.positive || "";
                neg.value = data.negative || "";
                setVistaEs(this, data.vista_es || "");
                syncToWidgets();
                setStatus(t(this, "genOk"));
            },
        });
        this._ldPanel = panel;
        this._ldSetStatus = panel.setStatus;
        hookWriterSerialize(this);

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
    });

    installSafeHook(nodeType, "onConfigure", function (info) {
        repairNodeWidgets(this);
        applyNodeTheme(this, THEME.old);
        hideWidget(widgetByName(this, "prompt_generado"));
        hideWidget(widgetByName(this, "negativo_generado"));
        const combo = widgetByName(this, "model");
        if (combo && isAuto(combo.value)) combo.value = AUTO_MODEL;
        this._ldPanel?.syncFromWidgets();
        this._ldRefreshModels?.(false);
    });
    hookExecuted(nodeType);
}



function imagesFromGuardarNode(node) {
    const out = app.nodeOutputs?.[String(node.id)] ?? app.nodeOutputs?.[node.id];
    if (Array.isArray(out?.images) && out.images.length) return out.images;
    if (Array.isArray(node.images) && node.images.length) return node.images;
    const imgs = node.imgs || node.imageIndex != null && node.overridenImgs;
    if (Array.isArray(node.imgs) && node.imgs.length) {
        return node.imgs
            .map((img) => {
                const src = img?.src || img?.currentSrc || "";
                if (!src) return null;
                try {
                    const u = new URL(src, location.origin);
                    const filename = u.searchParams.get("filename");
                    if (!filename) return null;
                    return {
                        filename,
                        subfolder: u.searchParams.get("subfolder") || "",
                        type: u.searchParams.get("type") || "temp",
                    };
                } catch (_e) {
                    return null;
                }
            })
            .filter(Boolean);
    }
    return [];
}

async function postGuardarImagen(body) {
    const res = await api.fetchApi("/ld_promptwriter/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    let data = null;
    try {
        data = await res.json();
    } catch (_e) {
        data = null;
    }
    if (!res.ok || !data?.ok) {
        const msg = data?.message || `HTTP ${res.status}`;
        throw new Error(msg);
    }
    return data;
}

function setupGuardarImagen(nodeType) {
    const paint = (node) => applyNodeTheme(node, { color: "#344029", bgcolor: "#1b222b" });
    const ensureUi = (node) => {
        paint(node);
        const autoW = widgetByName(node, "guardado_automatico");
        if (autoW && autoW.label !== undefined) autoW.label = t(node, "guardarAuto");
        if (node._ldGuardarUi) {
            node._ldRefreshI18n?.();
            return;
        }
        const setStatus = (msg, kind) => {
            if (!node._ldGuardarStatus) return;
            node._ldGuardarStatus.textContent = msg || "";
            node._ldGuardarStatus.className = "ld-status" + (kind ? " " + kind : "");
        };
        const status = document.createElement("div");
        status.className = "ld-status";
        status.style.minHeight = "18px";
        status.style.fontSize = "11px";
        const statusDom = node.addDOMWidget("ld_guardar_status", "div", status, { serialize: false, hideOnZoom: false });
        if (statusDom) {
            statusDom.serialize = false;
            statusDom.computeSize = (width) => [width || 200, 24];
        }
        node._ldGuardarStatus = status;
        const btn = node.addWidget("button", t(node, "btnGuardar"), null, async () => {
            const images = imagesFromGuardarNode(node);
            if (!images.length) {
                setStatus(t(node, "guardarNeedImage"), "warn");
                node.graph?.setDirtyCanvas?.(true);
                return;
            }
            setStatus(t(node, "guardarSaving"));
            node.graph?.setDirtyCanvas?.(true);
            try {
                const data = await postGuardarImagen({
                    images,
                    filename_prefix: widgetValue(node, "filename_prefix", "ComfyUI"),
                });
                const name = (data.saved || []).map((s) => s.filename || s).filter(Boolean).join(", ") || data.message || "";
                setStatus(t(node, "guardarOk", { name }), "ok");
            } catch (err) {
                const msg = String(err?.message || err || "");
                setStatus(msg ? `${t(node, "guardarFail")} ${msg}` : t(node, "guardarFail"), "err");
            }
            node.graph?.setDirtyCanvas?.(true);
        });
        if (btn) {
            btn.serialize = false;
            btn._ldGuardarBtn = true;
        }
        node._ldGuardarBtn = btn;
        node._ldRefreshI18n = () => {
            const aw = widgetByName(node, "guardado_automatico");
            if (aw && aw.label !== undefined) aw.label = t(node, "guardarAuto");
            if (node._ldGuardarBtn) node._ldGuardarBtn.name = t(node, "btnGuardar");
        };
        node._ldGuardarUi = true;
    };
    installSafeHook(nodeType, "onNodeCreated", function () {
        ensureUi(this);
        // Never shrink a node that already has preview space reserved.
        if (!this.size) this.size = [393, 648];
    });
    installSafeHook(nodeType, "onConfigure", function (info) {
        repairNodeWidgets(this);
        ensureUi(this);
    });
}


function setupImagenBaseI2I(nodeType) {
    const paint = (node) => applyNodeTheme(node, { color: "#203c40", bgcolor: "#1b222b" });
    const ensureUi = (node) => {
        paint(node);
        hideWidget(widgetByName(node, "archivo"));
        const modeloW = widgetByName(node, "modelo");
        const modeloLinked = (node.inputs || []).some((i) => i.name === "modelo" && i.link != null);
        if (modeloLinked) hideWidget(modeloW);
        const denoiseW = widgetByName(node, "denoise");
        if (denoiseW && denoiseW.label !== undefined) denoiseW.label = t(node, "denoise");
        const stepsW = widgetByName(node, "steps_krea2");
        if (stepsW && stepsW.label !== undefined) stepsW.label = t(node, "stepsKrea2");
        if (node._ldI2iUi) {
            node._ldRefreshI18n?.();
            return;
        }

        const root = document.createElement("div");
        root.className = "ld-panel";
        root.style.padding = "6px 8px 8px";
        const label = document.createElement("div");
        label.className = "ld-label";
        label.dataset.i18n = "i2iLabel";
        label.textContent = t(node, "i2iLabel");
        const hint = document.createElement("div");
        hint.className = "ld-hint";
        hint.dataset.i18n = "i2iHint";
        hint.textContent = t(node, "i2iHint");
        hint.style.fontSize = "11px";
        hint.style.opacity = "0.75";
        hint.style.margin = "0 0 6px";
        const warn = document.createElement("div");
        warn.className = "ld-hint ld-i2i-warn";
        warn.dataset.i18n = "i2iWarn";
        warn.textContent = t(node, "i2iWarn");
        Object.assign(warn.style, {
            fontSize: "10.5px",
            lineHeight: "1.3",
            color: "#f3d27a",
            background: "rgba(243, 210, 122, 0.08)",
            border: "1px solid rgba(243, 210, 122, 0.28)",
            borderRadius: "6px",
            padding: "4px 6px",
            margin: "0 0 6px",
            whiteSpace: "normal",
            overflowWrap: "anywhere",
        });

        const thumb = document.createElement("div");
        thumb.className = "ld-thumb";
        thumb.style.height = "140px";
        thumb.style.width = "100%";
        thumb.style.position = "relative";
        thumb.style.cursor = "pointer";
        const ph = document.createElement("div");
        ph.className = "ld-thumb-ph";
        ph.dataset.i18n = "thumbPh";
        ph.textContent = t(node, "thumbPh");
        const imgEl = document.createElement("img");
        imgEl.alt = "";
        imgEl.style.display = "none";
        const pickBtn = document.createElement("button");
        pickBtn.type = "button";
        pickBtn.className = "ld-thumb-pick";
        pickBtn.textContent = "📂";
        pickBtn.dataset.i18nTitle = "pickTitle";
        pickBtn.title = t(node, "pickTitle");
        const clearBtn = document.createElement("button");
        clearBtn.type = "button";
        clearBtn.className = "ld-thumb-clear";
        clearBtn.textContent = "✖";
        clearBtn.dataset.i18nTitle = "clearTitle";
        clearBtn.title = t(node, "clearTitle");
        const fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = "image/*";
        fileInput.style.display = "none";
        thumb.append(ph, imgEl, pickBtn, clearBtn, fileInput);
        const nameEl = document.createElement("div");
        nameEl.className = "ld-thumb-name";
        root.append(label, hint, warn, thumb, nameEl);

        const setArchivo = (info) => {
            const w = widgetByName(node, "archivo");
            if (w) w.value = info ? serializeArchivo(info) : "";
            node.graph?.setDirtyCanvas?.(true, true);
            refreshThumb();
        };
        const refreshThumb = () => {
            const info = parseArchivo(widgetValue(node, "archivo", ""));
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
                ph.style.display = "block";
                nameEl.textContent = "";
            }
        };
        const pickFile = () => fileInput.click();
        thumb.addEventListener("click", (ev) => {
            if (ev.target === pickBtn || ev.target === clearBtn) return;
            pickFile();
        });
        thumb.addEventListener("dragover", (ev) => {
            ev.preventDefault();
            thumb.classList.add("drag");
        });
        thumb.addEventListener("dragleave", () => thumb.classList.remove("drag"));
        thumb.addEventListener("drop", async (ev) => {
            ev.preventDefault();
            thumb.classList.remove("drag");
            const file = ev.dataTransfer?.files?.[0];
            if (!file) return;
            try {
                setArchivo(await uploadInputImage(file));
            } catch (err) {
                nameEl.textContent = String(err?.message || err || t(node, "uploadFail"));
            }
        });
        fileInput.addEventListener("change", async () => {
            const file = fileInput.files?.[0];
            fileInput.value = "";
            if (!file) return;
            try {
                setArchivo(await uploadInputImage(file));
            } catch (err) {
                nameEl.textContent = String(err?.message || err || t(node, "uploadFail"));
            }
        });
        pickBtn.addEventListener("click", (ev) => {
            ev.stopPropagation();
            showImagePicker(pickBtn, async (picked) => {
                if (picked?.upload) {
                    pickFile();
                    return;
                }
                if (picked?.filename) setArchivo(picked);
            });
        });
        clearBtn.addEventListener("click", (ev) => {
            ev.stopPropagation();
            setArchivo(null);
        });

        const dom = node.addDOMWidget("ld_i2i_thumb", "div", root, { serialize: false, hideOnZoom: false });
        if (dom) {
            dom.serialize = false;
            dom.computeSize = (width) => [width || 200, 290];
        }
        node._ldRefreshI18n = () => {
            label.textContent = t(node, "i2iLabel");
            hint.textContent = t(node, "i2iHint");
            warn.textContent = t(node, "i2iWarn");
            ph.textContent = t(node, "thumbPh");
            pickBtn.title = t(node, "pickTitle");
            clearBtn.title = t(node, "clearTitle");
            const d = widgetByName(node, "denoise");
            if (d && d.label !== undefined) d.label = t(node, "denoise");
            const s = widgetByName(node, "steps_krea2");
            if (s && s.label !== undefined) s.label = t(node, "stepsKrea2");
        };
        node._ldI2iUi = true;
        refreshThumb();
    };

    installSafeHook(nodeType, "onNodeCreated", function () {
        ensureUi(this);
        if (!this.size || this.size[0] < 300) {
            if (typeof this.setSize === "function") this.setSize([400, 400]);
            else this.size = [400, 400];
        }
        setTimeout(() => growConfigToFit(this), 0);
    });
    installSafeHook(nodeType, "onConfigure", function (info) {
        repairNodeWidgets(this);
        ensureUi(this);
        // Saved size stays; only grow the height if the warning doesn't fit.
        setTimeout(() => growConfigToFit(this), 0);
    });
}

function isWriterNode(node) {
    const typ = String(node?.type || node?.comfyClass || "");
    return typ === "LD_LMStudioPromptWriterV2" || typ === "LD_LMStudioPromptWriter";
}

function syncWriterPanelToWidgets(node) {
    if (!node) return;
    const panel = node._ldPanel;
    panel?.syncToWidgets?.();
    if (!panel) return;
    const pw = widgetByName(node, "prompt_generado");
    const nw = widgetByName(node, "negativo_generado");
    const iw = widgetByName(node, "idea");
    if (panel.pos && pw) pw.value = panel.pos.value;
    if (panel.neg && nw) nw.value = panel.neg.value;
    if (panel.ideaArea && iw) iw.value = panel.ideaArea.value;
    if (Array.isArray(node.widgets) && Array.isArray(node.widgets_values)) {
        node.widgets.forEach((w, i) => {
            if (!w || w.serialize === false) return;
            if (i < node.widgets_values.length && (w.name === "prompt_generado" || w.name === "negativo_generado" || w.name === "idea")) {
                node.widgets_values[i] = w.value;
            }
        });
    }
}

function syncAllWriterPanelsToWidgets() {
    const nodes = app.graph?._nodes || app.graph?.nodes || [];
    for (const n of nodes) {
        if (isWriterNode(n)) syncWriterPanelToWidgets(n);
    }
}

function hookWriterSerialize(node) {
    if (!node || node._ldSerializeHooked) return;
    node._ldSerializeHooked = true;
    for (const name of ["prompt_generado", "negativo_generado", "idea"]) {
        const w = widgetByName(node, name);
        if (!w) continue;
        w.serialize = true;
        const orig = w.serializeValue?.bind(w);
        w.serializeValue = async function (n, index) {
            const target = n || node;
            const panel = target?._ldPanel;
            if (name === "prompt_generado" && panel?.pos) return String(panel.pos.value ?? "");
            if (name === "negativo_generado" && panel?.neg) return String(panel.neg.value ?? "");
            if (name === "idea" && panel?.ideaArea) return String(panel.ideaArea.value ?? "");
            if (typeof orig === "function") return await orig(n, index);
            return this.value;
        };
    }
}

function injectWriterPromptsIntoGraphPrompt(result) {
    if (!result) return result;
    const output = result.output || result;
    if (!output || typeof output !== "object") return result;
    const nodes = app.graph?._nodes || app.graph?.nodes || [];
    for (const n of nodes) {
        if (!isWriterNode(n)) continue;
        const entry = output[n.id] || output[String(n.id)];
        if (!entry || typeof entry !== "object") continue;
        if (!entry.inputs || typeof entry.inputs !== "object") entry.inputs = entry.inputs || {};
        const panel = n._ldPanel;
        const pos = panel?.pos ? String(panel.pos.value ?? "") : String(widgetValue(n, "prompt_generado", "") || "");
        const neg = panel?.neg ? String(panel.neg.value ?? "") : String(widgetValue(n, "negativo_generado", "") || "");
        const idea = panel?.ideaArea ? String(panel.ideaArea.value ?? "") : String(widgetValue(n, "idea", "") || "");
        entry.inputs.prompt_generado = pos;
        entry.inputs.negativo_generado = neg;
        if (panel?.ideaArea || widgetByName(n, "idea")) entry.inputs.idea = idea;
        if (pos.trim()) entry.inputs.usar_prompt_generado = true;
        for (let i = 1; i <= N_IMAGES; i++) {
            const dw = widgetByName(n, `desc_imagen_${i}`);
            const col = (panel?.cols || []).find((c) => c.index === i);
            const desc = String((col?.desc?.value ?? dw?.value) || "");
            if (desc) entry.inputs[`desc_imagen_${i}`] = desc;
            const sig = aspectSignature(n, i);
            if (sig) entry.inputs[`desc_aspects_${i}`] = sig;
        }
    }
    return result;
}

async function prepareAllWritersForQueue() {
    const nodes = app.graph?._nodes || app.graph?.nodes || [];
    for (const n of nodes) {
        if (!isWriterNode(n)) continue;
        const setStatus = n._ldPanel?.setStatus || n._ldSetStatus;
        await ensureEnglishFromSpanish(n, { setStatus });
        const pos = String(n._ldPanel?.pos?.value || widgetValue(n, "prompt_generado", "") || "").trim();
        if (!pos) await ensureImageDescriptions(n, { setStatus });
    }
}

app.registerExtension({
    name: "LD.LMStudioPromptWriter",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        const name = nodeData.name;
        if (name === CONFIG_NODE) {
            setupConfigNode(nodeType);
        } else if (name === "LD_ModeloGen") {
            setupModeloGen(nodeType);
        } else if (name === WRITER_V2) {
            setupWriterV2(nodeType);
        } else if (name === "LD_Tamano") {
            setupTamano(nodeType);
        } else if (name === "LD_EmbeddingsNegativos") {
            setupEmbeddings(nodeType);
        } else if (name === "LD_GuardarImagen") {
            setupGuardarImagen(nodeType);
        } else if (name === "LD_ImagenBaseI2I") {
            setupImagenBaseI2I(nodeType);
        } else if (name === OLD_WRITER) {
            setupOldWriter(nodeType);
        }
    },
    loadedGraphNode(node) {
        try {
            repairNodeWidgets(node);
        } catch (err) {
            console.warn("[LD-PromptWriter] loadedGraphNode repair:", err);
        }
        try {
            const typ = String(node?.type || node?.comfyClass || "");
            if (typ === "LD_LMStudioPromptWriterV2") applyWriterChrome(node);
        } catch (err) {
            console.warn("[LD-PromptWriter] loadedGraphNode chrome:", err);
        }
    },
    async setup() {
        if (app._ldRepairQueueHooked) return;
        app._ldRepairQueueHooked = true;
        const orig = app.queuePrompt?.bind(app);
        if (orig) {
            app.queuePrompt = async function (...args) {
                repairAllGraphWidgets(app.graph);
                await prepareAllWritersForQueue();
                syncAllWriterPanelsToWidgets();
                return orig(...args);
            };
        }
        if (!app._ldGraphToPromptHooked && typeof app.graphToPrompt === "function") {
            app._ldGraphToPromptHooked = true;
            const origGTP = app.graphToPrompt.bind(app);
            app.graphToPrompt = async function (...args) {
                syncAllWriterPanelsToWidgets();
                const result = await origGTP(...args);
                return injectWriterPromptsIntoGraphPrompt(result);
            };
        }
    },
});
