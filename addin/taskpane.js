// addin/taskpane.js
// Hosted API (no key needed)
const API_URL = "https://phishgurd-ai.onrender.com/predict";

Office.onReady(() => {
    const scanBtn = document.getElementById("scanBtn");
    if (scanBtn) scanBtn.addEventListener("click", run);

    // Optional: auto-scan when pane opens
    run().catch(() => { });
});

async function run() {
    const item = Office.context?.mailbox?.item;
    if (!item) return renderError("No email selected.");

    setScanning();

    // Collect data
    const subject = item.subject || "";
    const from =
        item.from?.emailAddress ||
        (item.sender && item.sender.emailAddress) ||
        "";
    const bodyText = await getBodyText(item); // plain text
    const payload = {
        subject,
        from,
        body: (bodyText || "").slice(0, 10000), // cap to 10KB
    };

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const msg = await safeErr(res);
            return renderError(
                `API ${res.status} ${res.statusText}${msg ? ` – ${msg}` : ""}`
            );
        }

        const data = await res.json();
        renderBadge(data);
        renderLinksFromBody(bodyText, data?.severity || "safe");
    } catch (e) {
        renderError(e?.message || String(e));
    }
}

function getBodyText(item) {
    return new Promise((resolve) => {
        item.body.getAsync(Office.CoercionType.Text, (r) => {
            if (r.status === Office.AsyncResultStatus.Succeeded) {
                resolve(r.value || "");
            } else {
                resolve("");
            }
        });
    });
}

/* ---------- UI helpers ---------- */

function setScanning() {
    const el = byId("result");
    if (!el) return;
    el.innerHTML = `
    <div class="bar" style="border-left-color:#0ea5e9;background:#eaf6ff">
      Scanning…
    </div>`;
}

function renderBadge({ severity = "safe", score = 0, reasons = [] }) {
    const el = byId("result");
    if (!el) return;

    const sev = (severity || "safe").toLowerCase(); // safe|low|medium|high
    const reasonsStr =
        reasons && reasons.length ? reasons.join(", ") : "—";

    // Works with your older taskpane.html styles (.bar, .high/.medium/.low)
    // and with the newer .pg-badge styles if you added the CSS.
    el.innerHTML = `
    <div class="pg-badge ${sev}">
      <div class="pg-title">Risk: ${sev.toUpperCase()} (${Number(score).toFixed(3)})</div>
      <div class="pg-sub">Reasons: ${escapeHtml(reasonsStr)}</div>
    </div>`;
}

function renderError(msg) {
    const el = byId("result");
    if (!el) return;
    el.innerHTML = `
    <div class="bar" style="border-left-color:#6b7280;background:#f1f5f9">
      <div style="font-weight:700;margin-bottom:2px">Error</div>
      <div class="meta" style="color:#111827">${escapeHtml(
        msg || "Unknown error"
    )}</div>
    </div>`;
}

/* ---------- Links section (optional container) ---------- */

function renderLinksFromBody(bodyText, severity) {
    const linksEl = byId("links");
    if (!linksEl) return; // your older HTML may not have this container

    const links = extractUrls(bodyText);
    if (!links.length) {
        linksEl.innerHTML = `<div class="pg-sub">No links found in this message.</div>`;
        return;
    }

    const list = links
        .slice(0, 20)
        .map((u, i) => {
            const esc = escapeHtml(u);
            return `
        <div class="pg-link">
          <div class="pg-sub">Link ${i + 1}</div>
          <div><a href="${esc}" target="_blank" rel="noreferrer noopener">${esc}</a></div>
        </div>`;
        })
        .join("");

    linksEl.innerHTML = list;
}

// Very lightweight URL extractor for plain text
function extractUrls(text) {
    if (!text) return [];
    const regex =
        /\bhttps?:\/\/[^\s<>"')]+/gi;
    const set = new Set();
    let m;
    while ((m = regex.exec(text))) {
        set.add(m[0]);
    }
    return Array.from(set);
}

/* ---------- utils ---------- */

function byId(id) {
    return document.getElementById(id);
}

function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, (m) => {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;",
        }[m];
    });
}

async function safeErr(r) {
    try {
        const j = await r.json();
        return j?.error || "";
    } catch {
        return "";
    }
}
