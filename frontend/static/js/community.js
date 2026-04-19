/**
 * Community Resilience Hub - Frontend Logic
 */

const API_BASE = "/api/community";
let currentUserId = `user_${Math.random().toString(36).substr(2, 9)}`;
let blockCount = 1;

// Initialize
window.addEventListener("DOMContentLoaded", async () => {
  console.log("Community UI loaded - User ID:", currentUserId);
  await updateBlockCount();
  setInterval(updateBlockCount, 10000);
  await initializeCommunityPage();
  setInterval(pollCommunityPage, 15000);
});

async function initializeCommunityPage() {
  if (document.getElementById("groupsList")) {
    await loadGroups();
  }
  if (document.getElementById("tipsList")) {
    await loadTips();
  }
  if (document.getElementById("resourcesList")) {
    await loadResources();
  }
  if (document.getElementById("trainingList")) {
    await loadTrainings();
  }
  if (document.getElementById("recoveryList")) {
    await loadRecoveryRequests();
  }
  if (document.getElementById("activityFeed")) {
    await loadActivityFeed();
  }
}

async function pollCommunityPage() {
  if (document.getElementById("groupsList") || document.getElementById("tipsList") || document.getElementById("resourcesList") || document.getElementById("trainingList") || document.getElementById("recoveryList") || document.getElementById("activityFeed")) {
    await initializeCommunityPage();
  }
}

async function updateBlockCount() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    blockCount = data.blocks;
    document.getElementById("blockCount").textContent = blockCount;
  } catch (e) {
    console.error("Failed to fetch status", e);
  }
}

// ─────────────────────────────────────────────
// COMMUNITY GROUPS
// ─────────────────────────────────────────────

async function createGroup(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById("groupName").value,
    location: document.getElementById("groupLocation").value,
    description: document.getElementById("groupDesc").value,
    leader_id: document.getElementById("groupLeader").value || currentUserId
  };
  
  try {
    const res = await fetch(`${API_BASE}/groups`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    alert("Group created: " + (result.name || result.error));
    e.target.reset();
    loadGroups();
  } catch (e) {
    alert("Error creating group: " + e.message);
  }
}

async function searchGroups() {
  const location = document.getElementById("searchLocation").value;
  try {
    const res = await fetch(`${API_BASE}/groups?location=${encodeURIComponent(location)}`);
    const data = await res.json();
    renderGroupsList(data.groups, "groupsList");
  } catch (e) {
    console.error("Error searching groups", e);
  }
}

async function loadGroups() {
  try {
    const res = await fetch(`${API_BASE}/groups`);
    const data = await res.json();
    const groups = data.groups || [];
    renderGroupsList(groups, "myGroups");
    renderGroupsList(groups, "groupsList");
    console.log("✓ Loaded", groups.length, "groups");
  } catch (e) {
    console.error("Error loading groups", e);
  }
}

function renderGroupsList(groups, containerId) {
  const container = document.getElementById(containerId);
  if (!groups || groups.length === 0) {
    container.innerHTML = "<div style='padding: 20px; text-align: center; color: var(--muted);'>No groups yet. Create one to get started!</div>";
    return;
  }
  
  container.innerHTML = groups.map(g => `
    <div class="list-item">
      <h4 style="color: var(--accent); margin-bottom: 8px;">📍 ${g.name}</h4>
      <p style="margin-bottom: 8px;">${g.description || "No description provided"}</p>
      <div class="list-item-meta">
        <span><strong>Location:</strong> ${g.location}</span>
        <span><strong>Members:</strong> ${g.members_count || 1}</span>
        <span class="badge">Leader: ${g.leader_id}</span>
      </div>
      <div class="list-item-actions">
        <button class="action-btn" onclick="joinGroup(${g.id})">Join Group</button>
        <button class="action-btn" onclick="viewGroupMembers(${g.id})">View Members</button>
      </div>
    </div>
  `).join("");
}

async function joinGroup(groupId) {
  const name = prompt("Your name:");
  if (!name) return;
  
  try {
    const res = await fetch(`${API_BASE}/groups/${groupId}/members`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUserId,
        name: name
      })
    });
    const result = await res.json();
    alert("Joined group! " + (result.status || result.error));
    loadGroups();
  } catch (e) {
    alert("Error joining group: " + e.message);
  }
}

async function viewGroupMembers(groupId) {
  try {
    const res = await fetch(`${API_BASE}/groups/${groupId}/members`);
    const data = await res.json();
    const members = data.members.map(m => `${m.name} (${m.role})`).join(", ");
    alert("Members: " + (members || "None yet"));
  } catch (e) {
    alert("Error fetching members: " + e.message);
  }
}

// ─────────────────────────────────────────────
// KNOWLEDGE SHARING
// ─────────────────────────────────────────────

async function shareTip(e) {
  e.preventDefault();
  const data = {
    group_id: parseInt(document.getElementById("tipGroupId").value) || null,
    user_id: currentUserId,
    category: document.getElementById("tipCategory").value,
    title: document.getElementById("tipTitle").value,
    content: document.getElementById("tipContent").value
  };
  
  try {
    const res = await fetch(`${API_BASE}/knowledge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    alert("Tip shared! ID: " + (result.id || ""));
    e.target.reset();
    loadTips();
  } catch (e) {
    alert("Error sharing tip: " + e.message);
  }
}

async function loadTips() {
  const categories = ["earthquake", "flood", "cyclone", "first_aid", "mental_health", "recovery", "preparedness"];
  let allTips = [];
  
  try {
    for (const cat of categories) {
      const res = await fetch(`${API_BASE}/knowledge/${cat}`);
      const data = await res.json();
      if (data.tips && data.tips.length > 0) {
        allTips = allTips.concat(data.tips);
      }
    }
    renderTips(allTips);
    console.log("✓ Loaded", allTips.length, "tips");
  } catch (e) {
    console.error("Error loading tips", e);
  }
}

function renderTips(tips) {
  const container = document.getElementById("tipsList");
  if (!tips || tips.length === 0) {
    container.innerHTML = "<div style='padding: 20px; text-align: center; color: var(--muted);'>No tips shared yet. Share community wisdom!</div>";
    return;
  }
  
  // Group tips by category
  const byCategory = {};
  tips.forEach(t => {
    if (!byCategory[t.category]) byCategory[t.category] = [];
    byCategory[t.category].push(t);
  });
  
  let html = "";
  for (const [category, categoryTips] of Object.entries(byCategory)) {
    html += `<h3 style="margin-top: 15px; color: var(--accent); margin-bottom: 10px; text-transform: uppercase; font-size: 12px;">📂 ${category}</h3>`;
    html += categoryTips.map(t => `
      <div class="list-item">
        <h4>${t.title}</h4>
        <p>${t.content.substring(0, 150)}${t.content.length > 150 ? "..." : ""}</p>
        <div class="list-item-meta">
          <span class="badge ${t.validation_status === 'verified' ? 'verified' : 'pending'}">
            ${t.validation_status === 'verified' ? '✓' : '⏳'} ${t.validation_status || 'Pending'}
          </span>
          <span>👍 ${t.upvotes || 0} upvotes</span>
          <span>By: ${t.user_id}</span>
        </div>
        <div class="list-item-actions">
          <button class="action-btn" onclick="upvoteTip(${t.id})">Upvote</button>
        </div>
      </div>
    `).join("");
  }
  
  container.innerHTML = html;
}

async function upvoteTip(tipId) {
  try {
    await fetch(`${API_BASE}/knowledge/${tipId}/upvote`, { method: "POST" });
    loadTips();
  } catch (e) {
    alert("Error upvoting tip: " + e.message);
  }
}

// ─────────────────────────────────────────────
// RESOURCES
// ─────────────────────────────────────────────

async function registerResource(e) {
  e.preventDefault();
  const data = {
    group_id: parseInt(document.getElementById("resourceGroupId").value) || null,
    user_id: currentUserId,
    resource_type: document.getElementById("resourceType").value,
    description: document.getElementById("resourceDesc").value,
    quantity: parseInt(document.getElementById("resourceQty").value) || 1,
    location: document.getElementById("resourceLocation").value
  };
  
  try {
    const res = await fetch(`${API_BASE}/resources`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    alert("Resource registered! ID: " + (result.id || ""));
    e.target.reset();
    loadResources();
  } catch (e) {
    alert("Error registering resource: " + e.message);
  }
}

async function loadResources() {
  try {
    const res = await fetch(`${API_BASE}/resources`);
    const data = await res.json();
    renderResourcesList(data.resources);
  } catch (e) {
    console.error("Error loading resources", e);
  }
}

function renderResourcesList(resources) {
  const container = document.getElementById("resourcesList");
  if (!resources || resources.length === 0) {
    container.innerHTML = "<div style='padding: 20px; text-align: center; color: var(--muted);'>No resources shared yet.</div>";
    return;
  }
  
  // Group by type
  const byType = {};
  resources.forEach(r => {
    if (!byType[r.resource_type]) byType[r.resource_type] = [];
    byType[r.resource_type].push(r);
  });
  
  let html = "";
  for (const [type, typeResources] of Object.entries(byType)) {
    html += `<h3 style="margin-top: 15px; color: var(--accent); margin-bottom: 10px; text-transform: uppercase; font-size: 12px;">📦 ${type}</h3>`;
    html += typeResources.map(r => `
      <div class="list-item">
        <h4>${type.toUpperCase()}</h4>
        <p>${r.description}</p>
        <div class="list-item-meta">
          <span>📍 ${r.location}</span>
          <span>📊 Qty: ${r.quantity}</span>
          <span class="badge">${r.availability}</span>
        </div>
        <div class="list-item-actions">
          ${r.availability === 'available' ? `<button class="action-btn" onclick="requestResource(${r.id})">Request</button>` : '<span style="color: var(--warn);">⚠️ Reserved</span>'}
        </div>
      </div>
    `).join("");
  }
  
  container.innerHTML = html;
}

async function requestResource(resourceId) {
  try {
    const res = await fetch(`${API_BASE}/resources/${resourceId}/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ requester_id: currentUserId })
    });
    const result = await res.json();
    alert("Resource requested! " + (result.status || result.error));
    loadResources();
  } catch (e) {
    alert("Error requesting resource: " + e.message);
  }
}

// ─────────────────────────────────────────────
// TRAINING
// ─────────────────────────────────────────────

async function scheduleTraining(e) {
  e.preventDefault();
  const data = {
    group_id: parseInt(document.getElementById("trainingGroupId").value),
    organizer_id: currentUserId,
    title: document.getElementById("trainingTitle").value,
    category: document.getElementById("trainingCategory").value,
    description: document.getElementById("trainingDesc").value,
    scheduled_date: document.getElementById("trainingDate").value
  };
  
  try {
    const res = await fetch(`${API_BASE}/training`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    alert("Training scheduled! ID: " + (result.id || ""));
    e.target.reset();
    loadTrainings();
  } catch (e) {
    alert("Error scheduling training: " + e.message);
  }
}

async function loadTrainings() {
  // Mock training data for now
  const container = document.getElementById("trainingList");
  container.innerHTML = "<p style='color: var(--muted);'>Load trainings to see scheduled sessions</p>";
}

async function completeTraining(e) {
  e.preventDefault();
  const data = {
    session_id: parseInt(document.getElementById("completeSessionId").value),
    user_id: document.getElementById("completeUserId").value
  };
  
  try {
    const res = await fetch(`${API_BASE}/training/${data.session_id}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    alert("Training completed! " + (result.status || result.error));
    e.target.reset();
  } catch (e) {
    alert("Error completing training: " + e.message);
  }
}

// ─────────────────────────────────────────────
// RECOVERY
// ─────────────────────────────────────────────

async function postRecoveryRequest(e) {
  e.preventDefault();
  const data = {
    group_id: parseInt(document.getElementById("recoveryGroupId").value) || null,
    user_id: currentUserId,
    category: document.getElementById("recoveryCategory").value,
    description: document.getElementById("recoveryDesc").value,
    priority: document.getElementById("recoveryPriority").value
  };
  
  try {
    const res = await fetch(`${API_BASE}/recovery`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    alert("Support request posted! ID: " + (result.id || ""));
    e.target.reset();
    loadRecoveryRequests();
  } catch (e) {
    alert("Error posting recovery request: " + e.message);
  }
}

async function loadRecoveryRequests() {
  try {
    const res = await fetch(`${API_BASE}/recovery`);
    const data = await res.json();
    renderRecoveryRequests(data.recovery_requests);
  } catch (e) {
    console.error("Error loading recovery requests", e);
  }
}

function renderRecoveryRequests(requests) {
  const container = document.getElementById("recoveryList");
  if (!requests || requests.length === 0) {
    container.innerHTML = "<div style='padding: 20px; text-align: center; color: var(--muted);'>No support requests yet.</div>";
    return;
  }
  
  container.innerHTML = requests.map(r => `
    <div class="list-item">
      <h4>${r.category}</h4>
      <p>${r.description.substring(0, 200)}${r.description.length > 200 ? "..." : ""}</p>
      <div class="list-item-meta">
        <span class="badge" style="background: ${r.priority === 'critical' ? 'rgba(255,107,53,0.2)' : r.priority === 'high' ? 'rgba(255,165,0,0.2)' : 'rgba(0,255,178,0.1)'};">${r.priority}</span>
        <span class="badge">${r.status}</span>
        <span>Posted by: ${r.user_id}</span>
      </div>
      <div class="list-item-actions">
        ${r.status === 'open' ? `<button class="action-btn" onclick="helpWithRecovery(${r.id})">I Can Help</button>` : '<span style="color: var(--accent2);">✓ Resolved</span>'}
      </div>
    </div>
  `).join("");
}

async function helpWithRecovery(requestId) {
  if (confirm("Do you want to help with this recovery request?")) {
    try {
      const res = await fetch(`${API_BASE}/recovery/${requestId}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const result = await res.json();
      alert("Thank you for helping! Request marked as resolved.");
      await loadAllData();
    } catch (e) {
      alert("Error: " + e.message);
    }
  }
}

async function resolveRecovery(e) {
  e.preventDefault();
  const requestId = parseInt(document.getElementById("resolveRequestId").value);
  
  try {
    const res = await fetch(`${API_BASE}/recovery/${requestId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    const result = await res.json();
    alert("Request resolved! " + (result.status || result.error));
    e.target.reset();
    loadRecoveryRequests();
  } catch (e) {
    alert("Error resolving request: " + e.message);
  }
}

// ─────────────────────────────────────────────
// ACTIVITY FEED
// ─────────────────────────────────────────────

async function loadActivityFeed() {
  try {
    const res = await fetch(`${API_BASE}/activity`);
    const data = await res.json();
    renderActivityFeed(data.activity);
  } catch (e) {
    console.error("Error loading activity", e);
  }
}

function renderActivityFeed(activity) {
  const container = document.getElementById("activityFeed");
  if (!activity || activity.length === 0) {
    container.innerHTML = "<div style='padding: 20px; text-align: center; color: var(--muted);'>No activities logged yet.</div>";
    return;
  }
  
  container.innerHTML = activity.map(a => `
    <div class="list-item">
      <h4>${getActivityIcon(a.activity_type)} ${a.activity_type.replace(/_/g, ' ').toUpperCase()}</h4>
      <p>${a.details || "Activity logged"}</p>
      <div class="list-item-meta">
        <span>By: ${a.user_id || "System"}</span>
        <span>⏰ ${new Date(a.created_at * 1000).toLocaleString()}</span>
      </div>
    </div>
  `).join("");
}

function getActivityIcon(type) {
  const icons = {
    'group_created': '👥',
    'member_joined': '➕',
    'tip_posted': '📝',
    'tip_validated': '✓',
    'resource_registered': '📦',
    'resource_requested': '🤝',
    'training_scheduled': '📅',
    'training_completed': '🏆',
    'recovery_request': '🆘',
    'recovery_resolved': '✓'
  };
  return icons[type] || '📌';
}

// ─────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────

async function loadAllData() {
  loadGroups();
  loadTips();
  loadResources();
  loadActivityFeed();
}
