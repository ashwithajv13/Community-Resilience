/**
 * Environment Configuration
 * =========================
 * Update API_BASE based on your deployment setup:
 * 
 * LOCALHOST (single computer):
 *   API_BASE = "" or "http://localhost:5000"
 * 
 * NETWORK (multiple computers):
 *   API_BASE = "http://<SERVER_IP>:5000"
 *   Replace <SERVER_IP> with actual IP from ipconfig
 * 
 * EXAMPLE:
 *   API_BASE = "http://192.168.1.100:5000"
 */

// ────────────────────────────────────────────
// CONFIGURATION: Change this based on your setup
// ────────────────────────────────────────────

const API_BASE = "";  // Leave empty for localhost, or set to "http://SERVER_IP:5000"

// ────────────────────────────────────────────
// Export for use in other files
// ────────────────────────────────────────────
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { API_BASE };
}
