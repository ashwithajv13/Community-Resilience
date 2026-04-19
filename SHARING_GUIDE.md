# ResilienceChain AI - Sharing Guide

## Quick Sharing Steps

### Step 1: Upload to Cloud Storage (Recommended)

#### Option A: OneDrive (Windows Native)
```
1. Open File Explorer
2. Right-click resiliencechain-ai folder → Cut
3. Navigate to C:\Users\YOUR_USERNAME\OneDrive
4. Paste folder
5. Wait for sync to complete (green checkmark)
6. On other computer, sign in with same Microsoft account
7. OneDrive will auto-sync the folder
```

#### Option B: Google Drive
```
1. Download Google Drive for Desktop
2. Sign in with your Google account
3. Move resiliencechain-ai folder to Google Drive folder
4. On other computer, install Google Drive and sign in
5. Folder auto-syncs
```

#### Option C: GitHub (Best for Development)
```
1. Create new repository on github.com
2. cd C:\Users\ABHIJITH J V\resiliencechain-ai\resiliencechain-ai
3. git init
4. git add .
5. git commit -m "Initial commit"
6. git remote add origin https://github.com/username/resiliencechain-ai
7. git push -u origin main
8. On other computer: git clone https://github.com/username/resiliencechain-ai
```

---

## Step 2: Network Configuration

### For Same Network Access

#### Computer A (Server): Enable Network Sharing
1. Open `backend/app.py`
2. Confirm this line exists (already set):
   ```python
   app.run(debug=True, host="0.0.0.0", port=5000)
   ```
   - `host="0.0.0.0"` = accessible from any network computer
   - `host="127.0.0.1"` = localhost only (not shareable)

#### Computer B (Client): Update Frontend URLs

Open `frontend/static/js/app.js`, find line with `API_BASE`:
```javascript
const API_BASE = "";  // Current: localhost only
```

Change to Computer A's IP address:
```javascript
const API_BASE = "http://192.168.1.100:5000";  // Replace with Computer A's actual IP
```

Similarly, open `frontend/static/js/community.js`, find:
```javascript
const API_BASE = "/api/community";
```

Change to:
```javascript
const API_BASE = "http://192.168.1.100:5000/api/community";  // Same IP as above
```

---

## Step 3: Find Computer A's IP Address

### Windows Command Line:
```powershell
ipconfig
```
Look for "IPv4 Address" under your network adapter (usually starts with 192.168.x.x or 10.x.x.x)

### Or in Settings:
1. Settings → Network & Internet → Wi-Fi (or Ethernet)
2. "Hardware Properties" or "Properties"
3. Find "IPv4 address"

---

## Step 4: Start Backend on Computer A

```bash
cd C:\path\to\resiliencechain-ai\backend
python app.py
```

Output should show:
```
ResilienceChain Community Platform
Building Local Resilience Together
📚 RAG chunks loaded: 16
⛓  Blockchain blocks: 1
🏘️  Community Groups DB initialized
🌐 Serving Community Hub at http://0.0.0.0:5000  ← Accessible from network
```

---

## Step 5: Access from Computer B

### Via Browser on Computer B:
```
http://192.168.1.100:5000/chat          → Chat interface
http://192.168.1.100:5000/community     → Community hub
http://192.168.1.100:5000/resources     → Resource exchange
http://192.168.1.100:5000/training      → Training coordinator
http://192.168.1.100:5000/recovery      → Recovery support
```

Replace `192.168.1.100` with Computer A's actual IP from Step 3.

---

## Troubleshooting

### "Cannot connect to server"
- Verify Computer A's IP: `ipconfig`
- Check firewall: Windows Defender Firewall → Allow Python through
- Ensure Flask is running on Computer A
- Test locally first on Computer A at http://localhost:5000

### "Requests failing on Computer B"
- Verify `API_BASE` in frontend JS files matches Computer A's IP
- Check browser console: F12 → Console tab
- Ensure both computers on same WiFi/network

### "Database not syncing"
- SQLite databases are not real-time synced
- Restart Flask backend after deploying
- Consider using cloud storage (OneDrive/Google Drive) for auto-sync

---

## Architecture

```
Computer A (Server):
  └─ backend/app.py (running on 0.0.0.0:5000)
     ├─ Serves frontend HTML
     ├─ Processes /api/chat, /api/community/* requests
     └─ Manages SQLite database & blockchain

Computer B (Client):
  └─ Browser (http://192.168.1.100:5000)
     ├─ HTML/CSS/JS (served from Computer A)
     ├─ AJAX requests to /api/* endpoints
     └─ Real-time sync via 15-second polling
```

---

## One-Time Copy (USB/External Drive)

If not using cloud storage:
1. Right-click `resiliencechain-ai` → Send to → USB drive
2. On other computer, copy from USB to desired location
3. Update frontend API URLs as in Step 2
4. Start backend and access as in Steps 4-5

---

## Notes

- **Database**: SQLite creates local file `data/` — no manual sync needed if using cloud storage
- **Secrets**: No API keys in this version (local RAG only) — safe to share
- **Frontend theme**: Light theme applied — verify colors render correctly on both computers
- **Blockchain**: Activity log stored in-memory + pickled file `/data/blockchain.pkl` — included in sync

For questions, check logs in `backend/app.py` output.
