// Hardcode your hosted API (no API key required)
const API_URL = "https://phishgurd-ai.onrender.com/predict";

Office.onReady(async () => {
    const scanBtn = document.getElementById("scanBtn");
    scanBtn.addEventListener("click", run);
    // Optional: auto-scan on open
    // run();
});

async function run() {
    const item = Office.context?.mailbox?.item;
    if (!item) return renderError("No email selected.");

    const subject = item.subject || "";
    const from = item.from?.emailAddress || "";
    const body = await getBodyText(item);
    const payload = { subject, from, body: (body || "").slice(0, 10000) }; // cap to 10KB

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const msg = await safeErr(res);
            return renderError(`API ${res.status} ${res.statusText}${msg ? ` – ${msg}` : ""}`);
        }
        const data = await res.json();
        renderBadge(data);
    } catch (e) {
        renderError(e?.message || String(e));
    }
}

function getBodyText(item) {
    return new Promise((resolve) => {
        item.body.getAsync("text", (r) => {
            if (r.status === Office.AsyncResultStatus.Succeeded) resolve(r.value || "");
            else resolve("");
        });
    });
}

function renderBadge({ severity, score, reasons }) {
    const el = document.getElementById("result");
    const sev = (severity || "safe").toLowerCase();
    const klass = ["high", "medium", "low"].includes(sev) ? sev : "";
    const s = (typeof score === "number") ? score.toFixed(3) : "—";
    const why = Array.isArray(reasons) && reasons.length ? reasons.join(", ") : "—";

    el.innerHTML = `
    <div class="bar ${klass}">
      <div style="font-weight:700; margin-bottom:2px">Risk: ${sev.toUpperCase()} (${s})</div>
      <div class="meta">Reasons: ${escapeHtml(why)}</div>
    </div>
  `;
}

function renderError(msg) {
    const el = document.getElementById("result");
    el.innerHTML = `
    <div class="bar" style="border-left-color:#6b7280;background:#f1f5f9">
      <div style="font-weight:700;margin-bottom:2px">Error</div>
      <div class="meta" style="color:#111827">${escapeHtml(msg || "Unknown error")}</div>
    </div>`;
}

function escapeHtml(s) { return (s || "").replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[m])) }
async function safeErr(r) { try { const j = await r.json(); return j?.error; } catch { return ""; } }
