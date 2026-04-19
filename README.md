# ⚡ ResilienceChain AI

> **Decentralized Disaster Intelligence**  
> RAG-powered zero-hallucination AI grounded in NDRF/SDMA protocols, with an immutable blockchain audit trail.

**Team:** CodeChain Hackers  
**Lead:** Ashwitha J V | **Members:** Akshitha, Chaithanya

---

## 🏗️ Architecture

```
resiliencechain-ai/
├── backend/
│   ├── app.py               ← Flask API server
│   ├── rag_engine.py        ← RAG: PDF ingestion + FAISS retrieval + Claude generation
│   └── blockchain_ledger.py ← SHA-256 immutable ledger
├── frontend/
│   ├── index.html           ← Main UI
│   └── static/
│       ├── css/style.css    ← Styling
│       └── js/app.js        ← Frontend logic
├── data/                    ← Auto-created at runtime
│   ├── manuals/             ← Uploaded PDFs stored here
│   ├── faiss.index          ← Vector search index
│   ├── chunks.pkl           ← RAG knowledge chunks
│   └── ledger.json          ← Blockchain ledger
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & set up environment

```bash
git clone <your-repo-url>
cd resiliencechain-ai

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API key

```bash
cp .env.example .env
# Edit .env and add your Groq API key:
# GROQ_API_KEY=your_groq_api_key_here
# Optionally override the model:
# GROQ_MODEL=groq/compound-mini
```

Get your API key at → https://www.groq.com

### 3. Run the server

```bash
cd backend
python app.py
```

Open → **http://localhost:5000**

---
## ☁️ Deploy to AWS Elastic Beanstalk

This repository is ready for AWS Elastic Beanstalk deployment using the Python app platform.

1. Install AWS CLI and EB CLI:
   ```bash
   pip install awscli awsebcli
   ```
2. Configure AWS credentials:
   ```bash
   aws configure
   ```
3. Initialize Elastic Beanstalk in the repo root:
   ```bash
   eb init -p python-3.11 community-resilience-master --region us-east-1
   ```
4. Create the environment and deploy:
   ```bash
   eb create community-resilience-master-env
   eb deploy
   ```
5. Open the live app:
   ```bash
   eb open
   ```

Notes:
- `application.py` is the EB WSGI entrypoint and points to `backend/app.py`.
- `Procfile` uses Gunicorn for production hosting.
- Static frontend content is served from `frontend/` by the Flask app.

---
## 🚀 Deploy to Render

The best full-hosting option for the complete app is Render, because it can run the Python backend and serve the frontend together.

1. Create a Render account and connect your GitHub repository.
2. Add `render.yaml` to the project root. This repo already includes `render.yaml`.
3. In Render, create a new Web Service from the repo.
4. Set the build command:
   ```bash
   pip install -r requirements.txt
   ```
5. Set the start command:
   ```bash
   gunicorn application:application --bind 0.0.0.0:$PORT
   ```
6. Add the required environment variable:
   - `GROQ_API_KEY`

Notes:
- This keeps the frontend and backend on the same domain, so `API_BASE = ""` works correctly.
- `render.yaml` makes the deployment configuration reproducible.

---
## 🚀 Deploy to Vercel

This project can deploy as a Vercel Python function for the API and static assets served from the `public/` folder.

Steps:

1. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```
2. Log in and link the project:
   ```bash
   cd <repo-root>
   vercel login
   vercel
   ```
3. Deploy:
   ```bash
   vercel --prod
   ```

Notes:
- The backend uses the `api/app.py` Vercel function.
- Static front-end files are served from `public/`.
- File uploads and local vector data are ephemeral on Vercel, so this deployment is best for demo/testing, not long-term production storage.

---

## �📚 How to Add NDRF/SDMA Manuals

**Option A: Upload via UI**  
Click **📄 UPLOAD MANUAL** in the top-right corner and select any PDF.

**Option B: Drop PDFs into the folder**  
Place PDF files in `data/manuals/`, then POST to ingest:
```bash
curl -X POST http://localhost:5000/api/ingest \
  -F "file=@data/manuals/ndrf_manual.pdf"
```

The RAG engine will chunk, embed, and index the document automatically.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send a message; returns AI response + block info |
| `POST` | `/api/sos` | Log an emergency SOS to the blockchain |
| `GET`  | `/api/ledger` | View the full blockchain ledger |
| `POST` | `/api/ingest` | Upload a PDF manual into the RAG index |
| `GET`  | `/api/status` | System status (RAG chunks, block count) |

### Chat Request Example

```json
POST /api/chat
{
  "message": "What should I do during a flood?",
  "history": []
}
```

### Chat Response Example

```json
{
  "response": "FLOOD PROTOCOL (NDRF SOP 2023):\n1. Move immediately to higher ground...",
  "block": {
    "index": 3,
    "hash": "a1b2c3d4e5f6...",
    "timestamp": 1718000000.0
  },
  "sources_used": 2,
  "rag_active": true
}
```

---

## ⛓️ Blockchain Ledger

Every interaction is permanently recorded:

```json
{
  "index": 1,
  "timestamp": 1718000000.123,
  "timestamp_readable": "2024-06-10 12:00:00 UTC",
  "data": {
    "type": "CHAT",
    "query": "What to do during a flood?",
    "response": "Move to higher ground immediately...",
    "sources_count": 2,
    "rag_active": true
  },
  "previous_hash": "00000000...",
  "hash": "a1b2c3d4e5f6..."
}
```

- **SHA-256** hashing with chain linkage
- **Tamper-evident**: any modification invalidates all subsequent blocks
- **Persistent**: stored in `data/ledger.json`
- **Verifiable**: `GET /api/ledger` returns full chain + validity status

---

## 🤖 RAG Pipeline

```
User Query
    ↓
Sentence Embedding (all-MiniLM-L6-v2)
    ↓
FAISS Vector Search (top-3 relevant chunks)
    ↓
Context Injection into System Prompt
    ↓
Claude claude-sonnet-4-20250514 Generation
    ↓
Response + Blockchain Log
```

**Fallback**: If FAISS/sentence-transformers are not installed, the engine uses keyword-overlap retrieval automatically.

**Built-in knowledge**: 10 core NDRF/SDMA protocols are pre-seeded so the system works immediately without any PDF uploads.

---

## 🛡️ Key Features

| Feature | Implementation |
|---------|---------------|
| Zero-hallucination | RAG restricts AI to verified manual content |
| Immutable audit trail | SHA-256 linked blockchain |
| SOS logging | Permanent, unalterable emergency records |
| Low-bandwidth ready | Lightweight Flask + vanilla JS frontend |
| PDF ingestion | PyMuPDF + FAISS real-time indexing |
| Keyword fallback | Works even without ML dependencies |

---

## 📞 Emergency Contacts (Always Accurate)

| Service | Number |
|---------|--------|
| National Emergency | **112** |
| NDRF Helpline | **1078** |
| Disaster Management | **1070** |
| Ambulance | **108** |

---

## 🔧 VS Code Tips

1. Install **Python** extension for IntelliSense
2. Install **Pylance** for type checking
3. Set interpreter to your venv: `Ctrl+Shift+P` → "Python: Select Interpreter"
4. Use **Thunder Client** extension to test API endpoints
5. Install **Live Server** to preview frontend independently

---

## 📄 License

Built for hackathon purposes. NDRF/SDMA content follows Government of India open data guidelines.
