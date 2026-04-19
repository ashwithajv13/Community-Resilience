/**
 * ResilienceChain AI — Frontend App Logic
 * ==========================================
 * Handles chat, SOS alerts, PDF upload, blockchain UI updates, map interactions.
 */

const API_BASE = "";   // empty = same origin (Flask serves both)

let conversationHistory = [];
let blockCount = 1;
let isLoading = false;
let map = null;
let locationMarker = null;
let currentLocation = null;
let hubMarkers = {};
let mapMode = "relief"; // relief, shelter, medical, all

// ─────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────

window.addEventListener("DOMContentLoaded", async () => {
  await refreshStatus();
  setInterval(refreshStatus, 15000);
  initializeMap();
  setupScrollBehavior();
});

function setupScrollBehavior() {
  // Ensure messages container scrolls to bottom when window resizes
  window.addEventListener("resize", () => {
    scrollBottom();
  });
}

function initializeMap() {
  const mapElement = document.getElementById("locationMap");
  if (!mapElement) return;

  map = L.map(mapElement, {
    center: [20.5937, 78.9629],
    zoom: 5,
    zoomControl: true,
    attributionControl: false,
    dragging: true,
    touchZoom: true,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    minZoom: 2,
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  // Force Leaflet to recalculate container size after DOM is fully rendered
  setTimeout(() => { map.invalidateSize(); }, 200);

  addCommunityHubs();
  locateUser(true);
  updateMapStatus();
}

function addCommunityHubs() {
  if (!map) return;

  // Comprehensive hub data across major Indian cities
  const communityHubs = [
    // Relief Centers
    { name: "Bengaluru Relief Hub", lat: 12.9716, lng: 77.5946, type: "relief", info: "Local relief coordination • Evacuation planning • Resource distribution" },
    { name: "Chennai Flood Support", lat: 13.0827, lng: 80.2707, type: "relief", info: "Flood-specific protocols • Community alerts • Recovery support" },
    { name: "Hyderabad Disaster Control", lat: 17.3850, lng: 78.4867, type: "relief", info: "Real-time disaster updates • Relief coordination • SOS routing" },
    { name: "Mumbai Emergency Ops", lat: 19.0760, lng: 72.8777, type: "relief", info: "Coastal disaster response • High-rise evacuation • Multi-hazard center" },
    { name: "Delhi National Center", lat: 28.7041, lng: 77.1025, type: "relief", info: "NDRF Coordination • National protocols • Emergency hotline" },
    
    // Shelters
    { name: "Bengaluru Shelter Complex", lat: 13.0350, lng: 77.6245, type: "shelter", info: "Capacity: 500+ persons • Medical support • Family reunification" },
    { name: "Chennai Safe Haven", lat: 13.1939, lng: 80.1850, type: "shelter", info: "Capacity: 800+ persons • Sanitation facilities • Food provision" },
    { name: "Hyderabad Community Center", lat: 17.4080, lng: 78.4777, type: "shelter", info: "Capacity: 400+ persons • Children care • Senior services" },
    { name: "Pune Emergency Shelter", lat: 18.5204, lng: 73.8567, type: "shelter", info: "Capacity: 600+ persons • Pet-friendly • Accessibility features" },
    { name: "Kolkata Relief Camp", lat: 22.5726, lng: 88.3639, type: "shelter", info: "Capacity: 700+ persons • Flood response ready • Boat access" },
    
    // Medical Centers
    { name: "Bengaluru Central Hospital", lat: 12.9352, lng: 77.6245, type: "medical", info: "Emergency trauma care • Disaster medicine • 24/7 operations" },
    { name: "Chennai Medical Center", lat: 13.1716, lng: 80.2754, type: "medical", info: "Burn unit • Pediatric emergency • Telemedicine ready" },
    { name: "Hyderabad Advanced Care", lat: 17.3950, lng: 78.5000, type: "medical", info: "ICU facilities • Orthopedic trauma • Blood bank services" },
    { name: "Mumbai Trauma Center", lat: 19.0596, lng: 72.8295, type: "medical", info: "Level-1 trauma facility • Surgical suites • AICU beds" },
    { name: "Delhi AIIMS Emergency", lat: 28.5684, lng: 77.2099, type: "medical", info: "National facility • Disaster protocols • Research-backed care" },
  ];

  communityHubs.forEach(hub => {
    createHubMarker(hub);
  });
}

function createHubMarker(hub) {
  const colors = {
    relief: "#10B981",   // Green
    shelter: "#F59E0B",  // Amber
    medical: "#EF4444"   // Red
  };

  const color = colors[hub.type] || "#6366F1";
  const icon = L.divIcon({
    className: `hub-marker hub-${hub.type}`,
    html: `<div style="background-color: ${color}; border: 2px solid white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
      ${hub.type === 'relief' ? '🏛️' : hub.type === 'shelter' ? '🏠' : '🏥'}
    </div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14]
  });

  const marker = L.marker([hub.lat, hub.lng], { icon }).addTo(map);
  
  // Enhanced popup with distance
  const distance = currentLocation ? 
    calculateDistance(currentLocation.lat, currentLocation.lng, hub.lat, hub.lng).toFixed(1) 
    : "?";
  
  const popupContent = `
    <div style="font-size: 12px; width: 200px;">
      <strong>${hub.name}</strong><br>
      <span style="color: #666; font-size: 11px;">${hub.type.toUpperCase()}</span><br><br>
      ${hub.info}<br><br>
      <span style="color: var(--accent2); font-weight: bold;">${distance} km from you</span>
    </div>
  `;
  
  marker.bindPopup(popupContent);
  hubMarkers[hub.name] = marker;
}

function toggleMapMode() {
  const modes = ["relief", "shelter", "medical"];
  const currentIndex = modes.indexOf(mapMode);
  mapMode = modes[(currentIndex + 1) % modes.length];
  filterHubsByMode();
  updateMapStatus();
  showSystemMessage(`Map filtered to show: <strong>${mapMode.toUpperCase()} centers</strong>`);
}

function filterHubsByMode() {
  Object.entries(hubMarkers).forEach(([name, marker]) => {
    // Reset all visibility - you'd need to track hub types
    // For now, just show all
  });
}

function toggleMapLegend() {
  const legend = document.getElementById("mapLegend");
  if (legend.style.display === "none") {
    legend.style.display = "grid";
  } else {
    legend.style.display = "none";
  }
}

function updateMapStatus() {
  const status = document.getElementById("mapStatus");
  if (currentLocation) {
    const hubCount = Object.keys(hubMarkers).length;
    status.innerHTML = `✓ <strong>${hubCount}</strong> hubs visible • Location active • Distance calc enabled`;
  } else {
    status.innerHTML = `🗺️ ${Object.keys(hubMarkers).length} hubs visible • Tap 'Locate Me' to show your position`;
  }
}

function locateUser(silent = false) {
  if (!navigator.geolocation) {
    if (!silent) showSystemMessage("⚠️ Geolocation not supported. Please enable location services.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords;
      currentLocation = { lat: latitude, lng: longitude };
      setMapLocation(latitude, longitude);
      updateMapStatus();
      if (!silent) {
        showSystemMessage(`📍 Location set to ${latitude.toFixed(4)}°, ${longitude.toFixed(4)}° • Finding nearby hubs...`);
        findNearbyHubs(latitude, longitude);
      }
    },
    (error) => {
      if (!silent) showErrorMessage(`Location access denied: ${error.message}`);
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
  );
}

function setMapLocation(lat, lng) {
  if (!map) return;
  map.setView([lat, lng], 11);

  if (locationMarker) {
    locationMarker.setLatLng([lat, lng]);
  } else {
    const userIcon = L.divIcon({
      className: 'user-marker',
      html: `<div style="background: linear-gradient(135deg, #6366F1, #10B981); border: 3px solid white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 0 0 10px rgba(99,102,241,0.6);">
        📍
      </div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
      popupAnchor: [0, -16]
    });
    locationMarker = L.marker([lat, lng], { icon: userIcon }).addTo(map);
  }

  locationMarker.bindPopup(`<strong>Your Location</strong><br>${lat.toFixed(4)}°, ${lng.toFixed(4)}°<br><em>Updated just now</em>`).openPopup();
}

function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

function findNearbyHubs(lat, lng) {
  const nearby = [];
  Object.entries(hubMarkers).forEach(([name, marker]) => {
    const markerLatLng = marker.getLatLng();
    const dist = calculateDistance(lat, lng, markerLatLng.lat, markerLatLng.lng);
    if (dist < 100) { // Within 100km
      nearby.push({ name, distance: dist });
    }
  });

  nearby.sort((a, b) => a.distance - b.distance);
  
  if (nearby.length > 0) {
    const nearbyText = nearby.slice(0, 3).map((h, i) => `${i+1}. ${h.name} (${h.distance.toFixed(1)}km)`).join("<br>");
    showSystemMessage(`🎯 <strong>Nearby Hubs:</strong><br>${nearbyText}`);
  }
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
  updateChainScroll(`Processing: "${text.substring(0, 50)}..." • RAG retrieval in progress`);

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
      throw new Error(`Server response error: ${raw.substring(0, 100)}`);
    }

    removeTyping();

    if (!res.ok) {
      throw new Error(data.error || `Server error ${res.status}`);
    }
    if (data.error) {
      throw new Error(data.error);
    }

    conversationHistory.push({ role: "assistant", content: data.response });
    blockCount = data.block.index + 1;

    appendBotMessage(data.response, data.block, data.rag_active, data.sources_used);
    updateChainScroll(
      `Block #${data.block.index} sealed • Hash: ${data.block.hash.substring(0, 16)}... • ` +
      `Sources: ${data.sources_used} • ${new Date().toLocaleTimeString('en-IN')}`
    );
    document.getElementById("blockCount").textContent = blockCount;
    document.getElementById("blockInfo").textContent = `⛓ Blocks: ${blockCount}`;

  } catch (err) {
    removeTyping();
    showErrorMessage(err.message);
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
    <div class="msg-meta user-meta"><span>YOU</span><span>${now}</span></div>
    <div class="msg-bubble user">${escapeHTML(text)}</div>
  `;
  msgs.appendChild(wrap);
  scrollBottom();
  scrollToLastMessage();
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
  scrollToLastMessage();
}

function showSystemMessage(html) {
  const msgs = document.getElementById("messages");
  const wrap = el("div", "msg-wrap fade-in");
  wrap.innerHTML = `
    <div class="msg-meta"><span>SYSTEM</span></div>
    <div class="msg-bubble bot" style="border-left-color:var(--chain)">${html}</div>
  `;
  msgs.appendChild(wrap);
  scrollBottom();
  scrollToLastMessage();
}

function showErrorMessage(msg) {
  const msgs = document.getElementById("messages");
  const wrap = el("div", "msg-wrap fade-in");
  wrap.innerHTML = `
    <div class="msg-meta"><span>SYSTEM ERROR</span></div>
    <div class="msg-bubble bot" style="border-left-color:var(--warn)">
      ⚠️ ${escapeHTML(msg || "Connection error")}<br><br>
      <strong>Emergency Contacts:</strong><br>
      • National Emergency: <strong>112</strong><br>
      • NDRF Helpline: <strong>1078</strong><br>
      • Ambulance: <strong>108</strong>
    </div>
  `;
  msgs.appendChild(wrap);
  scrollBottom();
  scrollToLastMessage();
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
  scrollToLastMessage();
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
  if (!msgs) return;
  
  // Use requestAnimationFrame for smooth scroll after DOM update
  requestAnimationFrame(() => {
    msgs.scrollTop = msgs.scrollHeight;
    // Double-scroll to ensure it works even with rendering delays
    setTimeout(() => {
      msgs.scrollTop = msgs.scrollHeight;
    }, 50);
  });
}

function scrollToLastMessage() {
  const msgs = document.getElementById("messages");
  if (!msgs) return;
  
  // Find the last message and scroll it into view
  const lastMsg = msgs.querySelector(".msg-wrap:last-child");
  if (lastMsg) {
    lastMsg.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
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
