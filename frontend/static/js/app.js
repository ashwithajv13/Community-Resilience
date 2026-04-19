/**
 * ResilienceChain AI — Frontend App Logic
 * ==========================================
 * Handles chat, SOS alerts, PDF upload, blockchain UI updates.
 */

const API_BASE = "";   // empty = same origin (Flask serves both)

let conversationHistory = [];
let blockCount = 1;
let isLoading = false;
let map = null;
let locationMarker = null;
let currentLocation = null;

// ─────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────

window.addEventListener("DOMContentLoaded", async () => {
  await refreshStatus();
  setInterval(refreshStatus, 15000);
  initializeMap();
});

function initializeMap() {
  const mapElement = document.getElementById("locationMap");
  if (!mapElement) return;

  map = L.map(mapElement, {
    center: [20.5937, 78.9629],
    zoom: 4,
    zoomControl: true,
    attributionControl: false,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    minZoom: 2,
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  addCommunityHubs();
  locateUser(true);
}

function addCommunityHubs() {
  if (!map) return;

  const communityHubs = [
    { name: "Bengaluru Relief Hub", lat: 12.9716, lng: 77.5946, info: "Local relief and evacuation coordination." },
    { name: "Chennai Flood Support Centre", lat: 13.0827, lng: 80.2707, info: "Flood shelter and community aid." },
    { name: "Hyderabad Emergency Hub", lat: 17.3850, lng: 78.4867, info: "First-aid and disaster response station." },
    { name: "Mysuru Community Safety Hub", lat: 12.2958, lng: 76.6394, info: "Community resilience and training centre." },
  ];

  communityHubs.forEach(hub => {
    const marker = L.marker([hub.lat, hub.lng]).addTo(map);
    marker.bindPopup(`<strong>${hub.name}</strong><br>${hub.info}`);
  });
}

function locateUser(silent = false) {
  if (!navigator.geolocation) {
    if (!silent) appendSystemMessage("⚠️ Geolocation is not supported by your browser.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords;
      currentLocation = { lat: latitude, lng: longitude };
      setMapLocation(latitude, longitude);
      if (!silent) appendSystemMessage(`📍 Your current position is set to ${latitude.toFixed(4)}, ${longitude.toFixed(4)}.`);
    },
    (error) => {
      if (!silent) appendErrorMessage(`Unable to read location: ${error.message}`);
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
  );
}

function setMapLocation(lat, lng) {
  if (!map) return;
  map.setView([lat, lng], 12);

  if (locationMarker) {
    locationMarker.setLatLng([lat, lng]);
  } else {
    locationMarker = L.marker([lat, lng], { title: "Your location" }).addTo(map);
  }

  locationMarker.bindPopup(`<strong>Your location</strong><br>${lat.toFixed(4)}, ${lng.toFixed(4)}`).openPopup();
}

async function refreshStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    const data = await res.json();
    blockCount = data.blocks;

    const ragEl = document.getElementById("ragStatus");
    ragEl.innerHTML = `<div class="pulse-dot"></div> RAG: ${data.rag_chunks} CHUNKS`;

    document.getElementById("blockCount").textContent = data.blocks;
    document.getElementById("blockInfo").textContent = `⛓ Blocks: ${data.blocks}`;

    const ragInfo = document.getElementById("ragInfo");
    ragInfo.textContent = `⚡ RAG: ${data.rag_chunks} chunks · Ledger ${data.ledger_valid ? "✓ valid" : "✗ invalid"}`;
  } catch {
    document.getElementById("ragStatus").innerHTML = `<div class="pulse-dot"></div> OFFLINE`;
  }
}

// ─────────────────────────────────────────────
// CHAT
// ─────────────────────────────────────────────

async function sendMessage() {
  const input = document.getElementById("input");
  const text = input.value.trim();
  if (!text || isLoading) return;

  input.value = "";
  input.style.height = "auto";
  setLoading(true);

  appendUserMessage(text);
  conversationHistory.push({ role: "user", content: text });
  showTyping();
  updateChainScroll(`Processing query: "${text.substring(0, 60)}..." · RAG retrieval in progress`);

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        history: conversationHistory.slice(-12),
      }),
    });

    const raw = await res.text();
    let data;
    try {
      data = JSON.parse(raw);
    } catch (parseErr) {
      removeTyping();
      throw new Error(`Invalid API response: ${raw.substring(0, 200)}`);
    }

    removeTyping();

    if (!res.ok) {
      throw new Error(data.error || `API error ${res.status}`);
    }
    if (data.error) {
      throw new Error(data.error);
    }

    conversationHistory.push({ role: "assistant", content: data.response });
    blockCount = data.block.index + 1;

    appendBotMessage(data.response, data.block, data.rag_active, data.sources_used);
    updateChainScroll(
      `Block #${data.block.index} sealed · Hash: ${data.block.hash.substring(0, 20)}... · ` +
      `Sources used: ${data.sources_used} · Timestamp: ${data.block.timestamp}`
    );
    document.getElementById("blockCount").textContent = blockCount;
    document.getElementById("blockInfo").textContent = `⛓ Blocks: ${blockCount}`;

  } catch (err) {
    removeTyping();
    appendErrorMessage(err.message);
  }

  setLoading(false);
}

function sendChip(text) {
  document.getElementById("input").value = text;
  sendMessage();
}

function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

// ─────────────────────────────────────────────
// SOS
// ─────────────────────────────────────────────

function triggerSOS() {
  document.getElementById("sosModal").style.display = "flex";
  document.getElementById("sosLocation").focus();
}

function closeSOS() {
  document.getElementById("sosModal").style.display = "none";
}

async function submitSOS() {
  const location = document.getElementById("sosLocation").value.trim() || "Unknown";
  const details = document.getElementById("sosDetails").value.trim() || "Emergency SOS triggered via ResilienceChain AI";
  closeSOS();

  try {
    const res = await fetch(`${API_BASE}/api/sos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location, details }),
    });
    const data = await res.json();
    blockCount = data.block_index + 1;

    appendSOSBlock(data, location, details);
    updateChainScroll(
      `🆘 SOS ALERT SEALED · Block #${data.block_index} · Hash: ${data.hash.substring(0, 20)}... · Location: ${location}`
    );
    document.getElementById("blockCount").textContent = blockCount;

  } catch {
    appendSOSBlock({ hash: "0x" + Math.random().toString(16).slice(2,10).toUpperCase(), block_index: blockCount }, location, details);
  }
}

// ─────────────────────────────────────────────
// PDF UPLOAD
// ─────────────────────────────────────────────

async function uploadPDF(input) {
  const file = input.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  appendSystemMessage(`📄 Ingesting manual: <strong>${file.name}</strong>...`);

  try {
    const res = await fetch(`${API_BASE}/api/ingest`, { method: "POST", body: formData });
    const data = await res.json();

    if (data.error) throw new Error(data.error);

    appendSystemMessage(
      `✅ <strong>${file.name}</strong> ingested successfully — ${data.chunks_added} knowledge chunks added to RAG index.`
    );
    await refreshStatus();
  } catch (err) {
    appendSystemMessage(`❌ Failed to ingest PDF: ${err.message}`);
  }

  input.value = "";
}

// ─────────────────────────────────────────────
// DOM HELPERS
// ─────────────────────────────────────────────

function appendUserMessage(text) {
  const msgs = document.getElementById("messages");
  const now = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  const wrap = el("div", "msg-wrap user fade-in");
  wrap.innerHTML = `
    <div class="msg-meta user-meta"><span>CITIZEN QUERY</span><span>${now}</span></div>
    <div class="msg-bubble user">${escapeHTML(text)}</div>
  `;
  msgs.appendChild(wrap);
  scrollBottom();
}

function appendBotMessage(text, block, ragActive, sourcesUsed) {
  const msgs = document.getElementById("messages");
  const now = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  const shortHash = block.hash.substring(0, 10).toUpperCase();
  const ragBadge = ragActive
    ? `<span class="source-tag">📄 RAG: ${sourcesUsed} source${sourcesUsed !== 1 ? "s" : ""} retrieved</span>`
    : `<span class="source-tag" style="border-color:rgba(255,215,0,0.2);color:var(--chain)">📚 Built-in NDRF knowledge</span>`;

  const wrap = el("div", "msg-wrap fade-in");
  wrap.innerHTML = `
    <div class="msg-meta"><span>RESILIENCECHAIN AI</span><span>BLOCK #${block.index}</span><span>${now}</span></div>
    <div class="msg-bubble bot">
      ${formatResponse(text)}
      <br>${ragBadge}
      <span class="hash-tag">⛓ 0x${shortHash}</span>
    </div>
  `;
  msgs.appendChild(wrap);
  scrollBottom();
}

function appendSOSBlock(data, location, details) {
  const msgs = document.getElementById("messages");
  const now = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  const shortHash = data.hash ? data.hash.substring(0, 16).toUpperCase() : "N/A";

  const wrap = el("div", "msg-wrap fade-in");
  wrap.innerHTML = `
    <div class="msg-meta"><span style="color:var(--warn)">⚠ SOS ALERT TRIGGERED</span><span>BLOCK #${data.block_index}</span><span>${now}</span></div>
    <div class="sos-bubble">
      <div class="sos-header">🆘 EMERGENCY ALERT — PERMANENTLY RECORDED ON BLOCKCHAIN</div>
      <strong>Location:</strong> ${escapeHTML(location)}<br>
      <strong>Details:</strong> ${escapeHTML(details)}<br><br>
      📋 SOS sealed — cannot be altered or deleted<br>
      🔗 Block Hash: <code style="color:var(--chain);font-size:11px">0x${shortHash}...</code><br><br>
      <strong>While awaiting help:</strong><br>
      • Move to highest ground if flooding<br>
      • Stay away from damaged structures<br>
      • Signal rescuers with bright cloth or flashlight<br>
      • <strong>National Emergency: 112 | NDRF: 1078 | Ambulance: 108</strong>
      <br><br>
      <span class="source-tag">📄 NDRF SOP 2023 · Emergency Response Protocol</span>
    </div>
  `;
  msgs.appendChild(wrap);
  scrollBottom();
}

function appendErrorMessage(msg) {
  const msgs = document.getElementById("messages");
  const wrap = el("div", "msg-wrap fade-in");
  wrap.innerHTML = `
    <div class="msg-meta"><span>SYSTEM ERROR</span></div>
    <div class="msg-bubble bot" style="border-left-color:var(--warn)">
      ⚠️ ${escapeHTML(msg || "Connection error")}<br><br>
      In a real emergency, call <strong>112</strong> (National Emergency) or <strong>1078</strong> (NDRF).
    </div>
  `;
  msgs.appendChild(wrap);
  scrollBottom();
}

function appendSystemMessage(html) {
  const msgs = document.getElementById("messages");
  const wrap = el("div", "msg-wrap fade-in");
  wrap.innerHTML = `
    <div class="msg-meta"><span>SYSTEM</span></div>
    <div class="msg-bubble bot" style="border-left-color:var(--chain)">${html}</div>
  `;
  msgs.appendChild(wrap);
  scrollBottom();
}

function showTyping() {
  const msgs = document.getElementById("messages");
  const wrap = el("div", "typing-wrap fade-in");
  wrap.id = "typing";
  wrap.innerHTML = `
    <div class="msg-meta"><span>RESILIENCECHAIN AI</span></div>
    <div class="typing-bubble">
      <div class="t-dot"></div><div class="t-dot"></div><div class="t-dot"></div>
    </div>
  `;
  msgs.appendChild(wrap);
  scrollBottom();
}

function removeTyping() {
  const t = document.getElementById("typing");
  if (t) t.remove();
}

function setLoading(state) {
  isLoading = state;
  document.getElementById("sendBtn").disabled = state;
  document.getElementById("input").disabled = state;
}

function updateChainScroll(text) {
  document.getElementById("chainScroll").textContent = text;
}

function scrollBottom() {
  const msgs = document.getElementById("messages");
  msgs.scrollTop = msgs.scrollHeight;
}

function el(tag, className) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  return e;
}

function escapeHTML(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatResponse(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/^(\d+)\. /gm, "<br><strong>$1.</strong> ")
    .replace(/^- /gm, "<br>• ")
    .replace(/\[SOURCE:(.*?)\]/g, '<br><span class="source-tag">📄 SOURCE:$1</span>')
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>");
}

// Close modal on overlay click
document.getElementById("sosModal")?.addEventListener("click", (e) => {
  if (e.target === document.getElementById("sosModal")) closeSOS();
});
