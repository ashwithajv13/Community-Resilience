"""
ResilienceChain AI - Flask Backend
===================================
RAG-powered disaster intelligence with blockchain audit trail.
Team: CodeChain Hackers | Lead: Ashwitha J V
"""

import os
import sys
sys.path.append('backend')
import json
import logging
from functools import wraps
from time import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from rag_engine import RAGEngine
from blockchain_ledger import BlockchainLedger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration constants
MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_LENGTH = 20
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
RATE_LIMIT_INTERVAL = 60  # seconds
RATE_LIMIT_REQUESTS = 30  # requests per interval

# Rate limiting store
rate_limit_store = {}

def ensure_data_directories():
    """Create necessary data directories."""
    os.makedirs("data/manuals", exist_ok=True)
    logger.info("Data directories initialized")

def rate_limit(max_requests=RATE_LIMIT_REQUESTS, interval=RATE_LIMIT_INTERVAL):
    """Simple rate limiter decorator."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            ip = request.remote_addr
            now = time()
            key = f"{ip}:{f.__name__}"
            
            if key not in rate_limit_store:
                rate_limit_store[key] = []
            
            requests = [t for t in rate_limit_store[key] if now - t < interval]
            if len(requests) >= max_requests:
                logger.warning(f"Rate limit exceeded for {ip}")
                return jsonify({"error": "Too many requests. Please try again later."}), 429
            
            requests.append(now)
            rate_limit_store[key] = requests
            return f(*args, **kwargs)
        return decorated
    return decorator

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# Initialize core systems
ensure_data_directories()
try:
    rag = RAGEngine()
    ledger = BlockchainLedger()
    logger.info("Core systems initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize core systems: {e}")
    raise

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/api/chat", methods=["POST"])
@rate_limit(max_requests=RATE_LIMIT_REQUESTS, interval=RATE_LIMIT_INTERVAL)
def chat():
    """Main chat endpoint: RAG retrieval → AI response → blockchain log."""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' field"}), 400

        user_message = data["message"].strip()
        conversation_history = data.get("history", [])

        # Input validation
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if len(user_message) > MAX_MESSAGE_LENGTH:
            return jsonify({"error": f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"}), 413
        
        if len(conversation_history) > MAX_HISTORY_LENGTH:
            conversation_history = conversation_history[-MAX_HISTORY_LENGTH:]

        logger.info(f"Processing chat: {user_message[:50]}...")

        # 1. RAG: retrieve relevant context from official manuals
        context_chunks = rag.retrieve(user_message, top_k=3)
        context_text = "\n\n".join(context_chunks) if context_chunks else ""

        # 2. Build augmented prompt
        system_prompt = build_system_prompt(context_text)

        # 3. Get AI response via Anthropic with fallback
        try:
            ai_response = rag.generate(
                system_prompt=system_prompt,
                history=conversation_history,
                user_message=user_message,
            )
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            if context_chunks:
                ai_response = f"**Based on NDRF/SDMA Protocols:**\n\n{context_text}\n\n[Emergency: NDRF 1078, Call 112]"
            else:
                ai_response = "Unable to find relevant information. Contact NDRF: 1078 or Emergency: 112"

        # 4. Log to blockchain ledger
        try:
            block = ledger.add_block(
                query=user_message,
                response=ai_response,
                sources=context_chunks,
            )
        except Exception as e:
            logger.error(f"Blockchain logging error: {e}")
            block = {"index": 0, "hash": "error", "timestamp": "N/A"}

        return jsonify({
            "response": ai_response,
            "block": {
                "index": block["index"],
                "hash": block["hash"],
                "timestamp": block["timestamp"],
            },
            "sources_used": len(context_chunks),
            "rag_active": len(context_chunks) > 0,
        })
        
    except Exception as e:
        logger.error(f"Unhandled error in chat endpoint: {e}")
        return jsonify({"error": "Internal server error. Please try again."}), 500


@app.route("/api/sos", methods=["POST"])
@rate_limit(max_requests=10, interval=60)
def sos():
    """Log an SOS alert immutably to the blockchain."""
    try:
        data = request.get_json() or {}
        location = data.get("location", "Unknown").strip()[:100]
        details = data.get("details", "Emergency SOS triggered").strip()[:500]

        logger.critical(f"🚨 SOS ALERT: Location={location}, Details={details[:50]}...")

        block = ledger.add_sos_block(location=location, details=details)

        return jsonify({
            "status": "SOS_LOGGED",
            "block_index": block["index"],
            "hash": block["hash"],
            "timestamp": block["timestamp"],
            "message": "🚨 Your SOS has been permanently recorded. Contact NDRF: 1078 | Emergency: 112",
            "emergency_contacts": {
                "national_emergency": "112",
                "ndrf_helpline": "1078",
                "ambulance": "108",
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Critical error in SOS endpoint: {e}")
        return jsonify({"error": "Failed to log SOS. Please contact emergency services directly."}), 500


@app.route("/api/ledger", methods=["GET"])
def get_ledger():
    """Return the full blockchain ledger."""
    return jsonify({
        "chain": ledger.chain,
        "length": len(ledger.chain),
        "valid": ledger.is_valid(),
    })


@app.route("/api/ingest", methods=["POST"])
@rate_limit(max_requests=5, interval=300)
def ingest_pdf():
    """Upload and ingest a PDF manual into the RAG knowledge base."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        
        # Validate filename
        if not file.filename:
            return jsonify({"error": "Invalid filename"}), 400
            
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files accepted. Received: " + file.filename.split('.')[-1]}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"}), 413
        
        if file_size == 0:
            return jsonify({"error": "Empty file uploaded"}), 400

        # Sanitize filename to prevent directory traversal
        filename = os.path.basename(file.filename)
        os.makedirs("data/manuals", exist_ok=True)
        save_path = os.path.join("data/manuals", filename)
        
        logger.info(f"🔄 Ingesting PDF: {filename} ({file_size} bytes)")
        file.save(save_path)

        chunks = rag.ingest_pdf(save_path)
        logger.info(f"✅ Successfully ingested {filename}: {chunks} chunks")
        
        return jsonify({
            "status": "ingested",
            "file": filename,
            "chunks_added": chunks,
            "file_size_bytes": file_size,
        }), 200
        
    except Exception as e:
        logger.error(f"Error ingesting PDF: {e}")
        return jsonify({"error": "Failed to ingest PDF. Please try again."}), 500


@app.route("/api/status", methods=["GET"])
def status():
    """System status endpoint."""
    try:
        return jsonify({
            "status": "online",
            "rag_chunks": rag.chunk_count(),
            "blocks": len(ledger.chain),
            "ledger_valid": ledger.is_valid(),
            "ai_available": bool(rag.client),
            "limits": {
                "max_message_length": MAX_MESSAGE_LENGTH,
                "max_history_length": MAX_HISTORY_LENGTH,
                "max_file_size_mb": MAX_FILE_SIZE // (1024*1024),
            }
        }), 200
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return jsonify({"status": "degraded", "error": "Unable to retrieve status"}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors gracefully."""
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors gracefully."""
    logger.error(f"500 Internal Error: {error}")
    return jsonify({"error": "Internal server error"}), 500


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def build_system_prompt(context: str) -> str:
    base = """You are ResilienceChain AI, a zero-hallucination disaster intelligence system.
You are grounded STRICTLY in verified NDRF (National Disaster Response Force) and SDMA
(State Disaster Management Authority) protocols.

RULES:
1. Only use information from the provided context. If context is empty, use general NDRF guidelines.
2. Never fabricate statistics, contact numbers, or protocols.
3. Structure responses with clear numbered steps.
4. Always end with: [SOURCE: <document name>]
5. Prioritize life-safety above all else.
6. Keep responses under 200 words — optimized for low-bandwidth.
7. Include community-level coordination advice where relevant.

EMERGENCY CONTACTS (always accurate):
- National Emergency: 112
- NDRF Helpline: 1078
- Disaster Management: 1070
- Ambulance: 108
"""
    if context:
        base += f"\n\nVERIFIED CONTEXT FROM OFFICIAL MANUALS:\n{context}"
    else:
        base += "\n\nNo specific manual context retrieved. Use standard NDRF protocols."
    return base


if __name__ == "__main__":
    print("🚀 ResilienceChain AI starting...")
    print(f"📚 RAG chunks loaded: {rag.chunk_count()}")
    print(f"⛓  Blockchain blocks: {len(ledger.chain)}")
    print(f"🔐 Rate limiting: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_INTERVAL}s")
    print(f"📝 Max message length: {MAX_MESSAGE_LENGTH} chars")
    print(f"📦 Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    logger.info("Starting ResilienceChain AI server with enhanced security and error handling...")
    app.run(debug=True, host="0.0.0.0", port=5000)