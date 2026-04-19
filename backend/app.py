"""
ResilienceChain AI - Flask Backend
===================================
RAG-powered disaster intelligence with blockchain audit trail.
Team: CodeChain Hackers | Lead: Ashwitha J V
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from rag_engine import RAGEngine
from blockchain_ledger import BlockchainLedger
from community_db import CommunityDB

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
MANUALS_DIR = os.path.join(DATA_DIR, "manuals")
os.makedirs(MANUALS_DIR, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="/static")
CORS(app)

# Initialize core systems
rag = RAGEngine()
ledger = BlockchainLedger()
community = CommunityDB()

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "community.html")

@app.route("/community")
def community_page():
    return send_from_directory(FRONTEND_DIR, "community.html")

@app.route("/chat")
def chat_interface():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/resources")
def resources_page():
    return send_from_directory(FRONTEND_DIR, "resources.html")

@app.route("/training")
def training_page():
    return send_from_directory(FRONTEND_DIR, "training.html")

@app.route("/recovery")
def recovery_page():
    return send_from_directory(FRONTEND_DIR, "recovery.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "static"), filename)


@app.route("/api/chat", methods=["POST"])
def chat():
    """Main chat endpoint: RAG retrieval → AI response → blockchain log."""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message = data["message"].strip()
    conversation_history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # 1. RAG: retrieve relevant context from official manuals
    context_chunks = rag.retrieve(user_message, top_k=3)
    context_text = "\n\n".join(context_chunks) if context_chunks else ""

    # 2. Build augmented prompt
    system_prompt = build_system_prompt(context_text)

    # 3. Get AI response via Groq if configured, otherwise local synthesis
    ai_response = rag.generate(
        system_prompt=system_prompt,
        history=conversation_history,
        user_message=user_message,
    )

    # 4. Log to blockchain ledger
    block = ledger.add_block(
        query=user_message,
        response=ai_response,
        sources=context_chunks,
    )

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


@app.route("/api/sos", methods=["POST"])
def sos():
    """Log an SOS alert immutably to the blockchain."""
    data = request.get_json() or {}
    location = data.get("location", "Unknown")
    details = data.get("details", "Emergency SOS triggered")

    block = ledger.add_sos_block(location=location, details=details)

    return jsonify({
        "status": "SOS_LOGGED",
        "block_index": block["index"],
        "hash": block["hash"],
        "timestamp": block["timestamp"],
        "message": "Your SOS has been permanently recorded. Contact NDRF: 1078 | Emergency: 112",
    })


@app.route("/api/ledger", methods=["GET"])
def get_ledger():
    """Return the full blockchain ledger."""
    return jsonify({
        "chain": ledger.chain,
        "length": len(ledger.chain),
        "valid": ledger.is_valid(),
    })


@app.route("/api/ingest", methods=["POST"])
def ingest_pdf():
    """Upload and ingest a PDF manual into the RAG knowledge base."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files accepted"}), 400

    save_path = os.path.join("data/manuals", file.filename)
    file.save(save_path)

    chunks = rag.ingest_pdf(save_path)
    return jsonify({
        "status": "ingested",
        "file": file.filename,
        "chunks_added": chunks,
    })


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "status": "online",
        "rag_chunks": rag.chunk_count(),
        "blocks": len(ledger.chain),
        "ledger_valid": ledger.is_valid(),
    })


# ─────────────────────────────────────────────
# COMMUNITY RESILIENCE FEATURES
# ─────────────────────────────────────────────

# Community Groups
@app.route("/api/community/groups", methods=["POST"])
def create_community_group():
    data = request.get_json()
    result = community.create_group(
        name=data.get("name"),
        location=data.get("location"),
        description=data.get("description"),
        leader_id=data.get("leader_id", "anonymous")
    )
    if "error" not in result:
        ledger.add_community_activity_block("group_created", data.get("name"), data.get("leader_id"), f"Group created in {data.get('location')}")
    return jsonify(result)

@app.route("/api/community/groups", methods=["GET"])
def get_community_groups():
    location = request.args.get("location")
    groups = community.get_groups(location)
    return jsonify({"groups": groups, "count": len(groups)})

@app.route("/api/community/groups/<int:group_id>/members", methods=["GET"])
def get_group_members(group_id):
    members = community.get_group_members(group_id)
    return jsonify({"group_id": group_id, "members": members, "count": len(members)})

@app.route("/api/community/groups/<int:group_id>/members", methods=["POST"])
def add_group_member(group_id):
    data = request.get_json()
    result = community.add_member_to_group(
        group_id, data.get("user_id"), data.get("name"),
        data.get("email"), data.get("phone"), data.get("location")
    )
    if "error" not in result:
        ledger.add_community_activity_block("member_joined", str(group_id), data.get("user_id"), f"{data.get('name')} joined")
    return jsonify(result)

# Knowledge Sharing
@app.route("/api/community/knowledge", methods=["POST"])
def post_knowledge():
    data = request.get_json()
    tip = community.post_tip(
        data.get("group_id"), data.get("user_id"),
        data.get("category"), data.get("title"), data.get("content")
    )
    if "error" not in tip:
        context_chunks = rag.retrieve(data.get("content"), top_k=3)
        validation = "checked against NDRF protocols" if context_chunks else "pending validation"
        ledger.add_community_activity_block("tip_shared", str(data.get("group_id")), data.get("user_id"), data.get("title"))
    return jsonify(tip)

@app.route("/api/community/knowledge/<category>", methods=["GET"])
def get_knowledge(category):
    validated = request.args.get("validated", "false").lower() == "true"
    tips = community.get_tips_by_category(category, validated)
    return jsonify({"category": category, "tips": tips, "count": len(tips)})

@app.route("/api/community/knowledge/<int:tip_id>/validate", methods=["POST"])
def validate_knowledge(tip_id):
    data = request.get_json()
    result = community.validate_tip(
        tip_id, data.get("validated_by"), data.get("is_valid", False),
        data.get("notes", "")
    )
    return jsonify(result)

@app.route("/api/community/knowledge/<int:tip_id>/upvote", methods=["POST"])
def upvote_knowledge(tip_id):
    result = community.upvote_tip(tip_id)
    return jsonify(result)

# Resources
@app.route("/api/community/resources", methods=["POST"])
def register_resource():
    data = request.get_json()
    resource = community.register_resource(
        data.get("group_id"), data.get("user_id"),
        data.get("resource_type"), data.get("description"),
        data.get("quantity", 1), data.get("location")
    )
    if "error" not in resource:
        ledger.add_community_activity_block("resource_shared", str(data.get("group_id")), data.get("user_id"), data.get("description"))
    return jsonify(resource)

@app.route("/api/community/resources", methods=["GET"])
def get_resources():
    group_id = request.args.get("group_id", type=int)
    resources = community.get_available_resources(group_id)
    return jsonify({"resources": resources, "count": len(resources)})

@app.route("/api/community/resources/<int:resource_id>/request", methods=["POST"])
def request_community_resource(resource_id):
    data = request.get_json()
    result = community.request_resource(resource_id, data.get("requester_id"))
    if "error" not in result:
        ledger.add_community_activity_block("resource_requested", None, data.get("requester_id"), f"Resource {resource_id} requested")
    return jsonify(result)

# Training & Drills
@app.route("/api/community/training", methods=["POST"])
def schedule_training():
    data = request.get_json()
    training = community.schedule_training(
        data.get("group_id"), data.get("organizer_id"),
        data.get("title"), data.get("category"),
        data.get("description"), data.get("scheduled_date")
    )
    if "error" not in training:
        ledger.add_community_activity_block("training_scheduled", str(data.get("group_id")), data.get("organizer_id"), data.get("title"))
    return jsonify(training)

@app.route("/api/community/training/<int:session_id>/complete", methods=["POST"])
def complete_training(session_id):
    data = request.get_json()
    result = community.record_training_completion(session_id, data.get("user_id"))
    if "error" not in result:
        ledger.add_community_activity_block("training_completed", None, data.get("user_id"), f"Training session {session_id} completed")
    return jsonify(result)

@app.route("/api/community/groups/<int:group_id>/training-progress", methods=["GET"])
def get_training_progress(group_id):
    progress = community.get_training_progress(group_id)
    return jsonify({"group_id": group_id, "progress": progress})

# Recovery Support
@app.route("/api/community/recovery", methods=["POST"])
def post_recovery_request():
    data = request.get_json()
    request_obj = community.post_recovery_request(
        data.get("group_id"), data.get("user_id"),
        data.get("category"), data.get("description"),
        data.get("priority", "normal")
    )
    if "error" not in request_obj:
        ledger.add_community_activity_block("recovery_support", str(data.get("group_id")), data.get("user_id"), data.get("description"))
    return jsonify(request_obj)

@app.route("/api/community/recovery", methods=["GET"])
def get_recovery_requests():
    group_id = request.args.get("group_id", type=int)
    requests_list = community.get_open_recovery_requests(group_id)
    return jsonify({"recovery_requests": requests_list, "count": len(requests_list)})

@app.route("/api/community/recovery/<int:request_id>/resolve", methods=["POST"])
def resolve_recovery(request_id):
    result = community.resolve_recovery_request(request_id)
    if "error" not in result:
        ledger.add_community_activity_block("recovery_resolved", None, None, f"Recovery request {request_id} resolved")
    return jsonify(result)

# Activity Feed
@app.route("/api/community/groups/<int:group_id>/activity", methods=["GET"])
def get_group_activity(group_id):
    activity = community.get_group_activity(group_id)
    return jsonify({"group_id": group_id, "activity": activity})

@app.route("/api/community/activity", methods=["GET"])
def get_all_community_activity():
    activity = community.get_all_activity(100)
    return jsonify({"activity": activity})


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
    print("██████████████████████████████████████████")
    print("  ResilienceChain Community Platform")
    print("  Building Local Resilience Together")
    print("██████████████████████████████████████████")
    print(f"📚 RAG chunks loaded: {rag.chunk_count()}")
    print(f"⛓  Blockchain blocks: {len(ledger.chain)}")
    print(f"🏘️  Community Groups DB initialized")
    print(f"🌐 Serving Community Hub at http://localhost:5000")
    print(f"💬 Chat interface at http://localhost:5000/chat")
    print("Starting server...")
    app.run(debug=True, host="0.0.0.0", port=5000)
