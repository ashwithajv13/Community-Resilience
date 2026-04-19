"""
RAG Engine — ResilienceChain AI
=================================
Retrieval-Augmented Generation using:
  - PyMuPDF for PDF parsing
  - FAISS for vector similarity search
  - sentence-transformers for embeddings
  - Anthropic Claude for generation
"""

import os
import json
import pickle
import re
from typing import List

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except (ImportError, SyntaxError):
    anthropic = None
    ANTHROPIC_AVAILABLE = False
    print("WARNING: Anthropic SDK not available. External AI disabled.")

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    print("WARNING: PyMuPDF not available. PDF ingestion disabled.")
import numpy as np

# Try to import FAISS and sentence-transformers (optional at startup)
try:
    # import faiss
    # from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = False
    print("WARNING: FAISS/sentence-transformers not imported.")
except ImportError:
    FAISS_AVAILABLE = False
    print("WARNING: FAISS/sentence-transformers not installed. Using keyword fallback.")


EMBED_MODEL = "all-MiniLM-L6-v2"
INDEX_PATH = "data/faiss.index"
CHUNKS_PATH = "data/chunks.pkl"
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 100    # overlap between chunks


class RAGEngine:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if ANTHROPIC_AVAILABLE and api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None
            if not ANTHROPIC_AVAILABLE:
                print("WARNING: Anthropic SDK unavailable. Using local synthesis only.")
            else:
                print("WARNING: ANTHROPIC_API_KEY not set. Using local synthesis only.")
        self.chunks: List[str] = []
        self.index = None
        self.embedder = None

        if FAISS_AVAILABLE:
            # self._load_embedder()  # lazy load
            self._load_chunks_only()
        else:
            self._load_chunks_only()

        # Seed with built-in NDRF knowledge if no manuals uploaded yet
        if not self.chunks:
            self._seed_builtin_knowledge()

    # ──────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve top-k relevant chunks for a query."""
        if not self.chunks:
            return []

        if FAISS_AVAILABLE and self.index is not None:
            return self._faiss_retrieve(query, top_k)
        else:
            return self._keyword_retrieve(query, top_k)

    def generate(self, system_prompt: str, history: list, user_message: str) -> str:
        """Generate a response from RAG knowledge base without external AI."""
        if not self.chunks:
            return "No knowledge base available. Please upload disaster management manuals."
        
        # Retrieve top-5 most relevant chunks for better synthesis
        context_chunks = self.retrieve(user_message, top_k=5)
        
        if not context_chunks:
            return "I couldn't find relevant information about your query. Please contact NDRF: 1078 for accurate assistance."
        
        # Synthesize response from multiple chunks
        response = self._synthesize_response(user_message, context_chunks)
        return response
    
    def _synthesize_response(self, query: str, chunks: List[str]) -> str:
        """Synthesize a coherent answer from multiple knowledge chunks."""
        query_lower = query.lower()
        category = self._detect_category(query_lower)
        query_terms = {w for w in re.findall(r"\w+", query_lower) if w not in self.STOPWORDS}

        if category != 'general':
            filtered_chunks = [chunk for chunk in chunks if any(term in chunk.lower() for term in self.CATEGORY_KEYWORDS.get(category, set()))]
            if filtered_chunks:
                chunks = filtered_chunks

        response = f"**Response Based on NDRF/SDMA Protocols**\n\n"
        if category != 'general':
            response += f"**Category:** {category.upper()}\n\n"
        response += "**Key Actions:**\n"

        actions = []
        for chunk in chunks[:4]:
            sentences = [s.strip() for s in chunk.replace('•', '.').split('.') if s.strip()]
            for sentence in sentences:
                if len(sentence) < 15:
                    continue
                sentence_lower = sentence.lower()
                words = set(re.findall(r"\w+", sentence_lower))
                is_actionable = any(term in sentence_lower for term in ['should', 'must', 'always', 'never', 'do', 'avoid', 'stay', 'move', 'keep', 'evacuate', 'call', 'turn', 'disconnect', 'monitor'])
                is_relevant = bool(query_terms & words) or bool(self.CATEGORY_KEYWORDS.get(category, set()) & words)
                if is_actionable or is_relevant:
                    actions.append(f"{len(actions)+1}. {sentence.strip()}")

        seen = set()
        unique_actions = []
        for action in actions:
            action_text = action.lower()
            if action_text not in seen:
                seen.add(action_text)
                unique_actions.append(action)

        if unique_actions:
            response += "\n".join(unique_actions[:8])
        else:
            for i, chunk in enumerate(chunks[:3], 1):
                snippet = chunk.replace('\n', ' ')[:220].strip()
                response += f"\n{i}. {snippet}..."

        response += "\n\n**Emergency Contacts:**\n"
        response += "- National Emergency: **112**\n"
        response += "- NDRF Helpline: **1078**\n"
        response += "- Ambulance: **108**\n"
        response += "- Disaster Management: **1070**\n"
        response += "\n[SOURCE: NDRF/SDMA Official Protocols]"
        return response

    def ingest_pdf(self, pdf_path: str) -> int:
        """Parse a PDF and add its chunks to the index."""
        try:
            text = self._extract_pdf_text(pdf_path)
        except ImportError:
            print(f"ERROR: PDF ingestion failed: PyMuPDF not available")
            return 0
        new_chunks = self._split_text(text)
        self.chunks.extend(new_chunks)

        if FAISS_AVAILABLE:
            self._rebuild_index()
        self._save_chunks()

        print(f"INFO: Ingested {len(new_chunks)} chunks from {pdf_path}")
        return len(new_chunks)

    def chunk_count(self) -> int:
        return len(self.chunks)

    # ──────────────────────────────────────────
    # RETRIEVAL STRATEGIES
    # ──────────────────────────────────────────

    def _faiss_retrieve(self, query: str, top_k: int) -> List[str]:
        q_vec = self.embedder.encode([query]).astype("float32")
        faiss.normalize_L2(q_vec)
        k = min(top_k, len(self.chunks))
        _, indices = self.index.search(q_vec, k)
        return [self.chunks[i] for i in indices[0] if i < len(self.chunks)]

    STOPWORDS = {
        'the', 'and', 'or', 'but', 'if', 'to', 'of', 'a', 'an', 'in', 'on', 'for',
        'with', 'without', 'at', 'by', 'from', 'is', 'are', 'was', 'were', 'be',
        'do', 'does', 'did', 'how', 'what', 'when', 'where', 'why', 'can', 'should',
        'will', 'would', 'could', 'as', 'it', 'that', 'this', 'your', 'you', 'i',
        'my', 'we', 'our', 'the', 'then', 'than', 'so', 'when', 'there', 'been',
        'have', 'has', 'had', 'about', 'isn', 'aren', 'don', 'doesn', 'didn',
        'during', 'before', 'after', 'while', 'through', 'between', 'within', 'until'
    }

    CATEGORY_KEYWORDS = {
        'flood': {'flood', 'water', 'rain', 'overflowing', 'drainage', 'submerge', 'levee', 'river'},
        'earthquake': {'earthquake', 'quake', 'tremor', 'shaking', 'aftershock', 'epicenter', 'seismic'},
        'cyclone': {'cyclone', 'typhoon', 'hurricane', 'storm', 'wind', 'gust', 'rainband'},
        'landslide': {'landslide', 'slide', 'collapse', 'mudflow', 'slope', 'debris'},
        'heatwave': {'heatwave', 'temperature', 'heat', 'sunstroke', 'dehydration'},
        'firstaid': {'first aid', 'injury', 'bleeding', 'burn', 'drown', 'cpr', 'resuscitation', 'wound'},
        'mentalhealth': {'mental', 'stress', 'trauma', 'psychological', 'anxiety', 'panic'},
        'kit': {'kit', 'prepare', 'ready', 'supply', 'equipment', 'torch', 'battery', 'water bottle'},
        'evacuation': {'evacuate', 'escape', 'leave', 'move', 'route', 'assembly', 'shelter'},
        'tsunami': {'tsunami', 'wave', 'coast', 'sea', 'inundation', 'shore'},
        'wildfire': {'wildfire', 'fire', 'smoke', 'embers', 'burning', 'forest'},
        'pandemic': {'pandemic', 'virus', 'disease', 'infection', 'quarantine', 'vaccination'},
    }

    def _keyword_retrieve(self, query: str, top_k: int) -> List[str]:
        """Enhanced keyword-overlap retrieval with better ranking."""
        normalized_query = query.lower()
        query_tokens = [w for w in re.findall(r"\w+", normalized_query) if w not in self.STOPWORDS]
        query_bigrams = self._get_bigrams(' '.join(query_tokens))
        query_phrases = [' '.join(query_tokens[i:i+2]) for i in range(len(query_tokens)-1)]
        category = self._detect_category(normalized_query)
        category_terms = self.CATEGORY_KEYWORDS.get(category, set()) if category != 'general' else set()

        scored = []
        for chunk in self.chunks:
            chunk_lower = chunk.lower()
            chunk_tokens = [w for w in re.findall(r"\w+", chunk_lower)]
            chunk_core = {w for w in chunk_tokens if w not in self.STOPWORDS}
            chunk_bigrams = self._get_bigrams(' '.join(chunk_tokens))

            word_score = len(set(query_tokens) & chunk_core)
            bigram_score = len(query_bigrams & chunk_bigrams) * 4
            phrase_score = sum(6 for phrase in query_phrases if phrase in chunk_lower)
            category_boost = len(category_terms & chunk_core) * 8
            consecutive_bonus = 0
            if len(query_tokens) >= 2:
                query_pair = ' '.join(query_tokens[:2])
                if query_pair in chunk_lower:
                    consecutive_bonus = 6

            total_score = word_score * 3 + bigram_score + phrase_score + category_boost + consecutive_bonus
            if total_score > 0:
                scored.append((total_score, chunk))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def _get_bigrams(self, text: str) -> set:
        """Extract bigrams (2-word sequences) from text."""
        words = text.split()
        return {' '.join(words[i:i+2]) for i in range(len(words)-1)}

    def _detect_category(self, query: str) -> str:
        """Detect the disaster category from the user query."""
        normalized_query = query.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(term in normalized_query for term in keywords):
                return category
        return 'general'

    # ──────────────────────────────────────────
    # PDF PROCESSING
    # ──────────────────────────────────────────

    def _extract_pdf_text(self, path: str) -> str:
        if not FITZ_AVAILABLE:
            raise ImportError("PyMuPDF not available")
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def _split_text(self, text: str) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return chunks

    # ──────────────────────────────────────────
    # INDEX MANAGEMENT
    # ──────────────────────────────────────────

    def _load_embedder(self):
        print(f"📦 Loading embedding model: {EMBED_MODEL}")
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("FAISS and sentence-transformers not available")
        self.embedder = SentenceTransformer(EMBED_MODEL)

    def _load_index(self):
        try:
            import faiss
        except ImportError:
            return
        if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
            self.index = faiss.read_index(INDEX_PATH)
            with open(CHUNKS_PATH, "rb") as f:
                self.chunks = pickle.load(f)
            print(f"INFO: FAISS index loaded: {len(self.chunks)} chunks")
        else:
            print("ℹ️  No FAISS index found. Will build on first ingest.")

    def _load_chunks_only(self):
        if os.path.exists(CHUNKS_PATH):
            with open(CHUNKS_PATH, "rb") as f:
                self.chunks = pickle.load(f)

    def _rebuild_index(self):
        try:
            import faiss
        except ImportError:
            return
        vectors = self.embedder.encode(self.chunks).astype("float32")
        faiss.normalize_L2(vectors)
        dim = vectors.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(vectors)
        os.makedirs("data", exist_ok=True)
        faiss.write_index(self.index, INDEX_PATH)
        print(f"⛓  FAISS index rebuilt: {len(self.chunks)} chunks")

    def _save_chunks(self):
        os.makedirs("data", exist_ok=True)
        with open(CHUNKS_PATH, "wb") as f:
            pickle.dump(self.chunks, f)

    # ──────────────────────────────────────────
    # BUILT-IN SEED KNOWLEDGE
    # ──────────────────────────────────────────

    def _seed_builtin_knowledge(self):
        """Seed the system with comprehensive NDRF/SDMA disaster protocols."""
        self.chunks = [
            # Emergency Contact Reference
            "NDRF EMERGENCY CONTACTS: National Emergency: 112 | NDRF Helpline: 1078 | Ambulance: 108 | Disaster Management: 1070 | For life-threatening situations call 112 immediately. NDRF (National Disaster Response Force) operates 24/7. State Disaster Management Authority (SDMA) coordinates local response.",
            
            # Flood Protocol
            "FLOOD PROTOCOL (NDRF SOP 2023): Immediately move to higher ground when floods are imminent. Do not walk through moving water — 6 inches can knock you down, 2 feet will sweep away vehicles. Turn off utilities at main switches. Disconnect electrical appliances to prevent fire. Avoid all floodwater — it may be contaminated with sewage and chemicals. Evacuate only if told by authorities. Use designated evacuation routes only. Listen to local radio for updates. Stay on high ground until water recedes and authorities declare area safe.",
            
            # Earthquake Protocol
            "EARTHQUAKE PROTOCOL (NDRF SOP 2023): During earthquake: DROP, COVER, HOLD immediately. Drop to hands and knees. Get under a sturdy desk, table, or against interior wall. Stay away from windows, exterior walls, and heavy objects that could fall. Do not run outside during shaking — risk of falling debris. After shaking stops: exit carefully through stairs only. Check for gas leaks and turn off gas supply at meter. Do not use elevators. Inspect building for structural damage. Expect aftershocks — keep emergency kit accessible. Listen for emergency broadcasts.",
            
            # Cyclone Protocol
            "CYCLONE PROTOCOL (SDMA 2022): Monitor India Meteorological Department (IMD) cyclone warnings continuously. Secure all loose objects outdoors — they become dangerous projectiles. Reinforce doors and windows, keep storm shutters ready. Stock water, food, medicines, and fuel. Move to an identified cyclone shelter if in coastal areas. Keep emergency kit ready: water (4L per person/day), food, torch, radio, medicines, first aid. Stay indoors during the storm — do not venture outside for any reason. Do not venture near sea or beach during storm surge. After cyclone: check for injuries and structural damage before leaving shelter.",
            
            # Landslide Protocol
            "LANDSLIDE PROTOCOL (SDMA 2022): Evacuate immediately if you hear rumbling sounds or notice fresh cracks in walls, ground, or roads. Move away from the slide path — horizontal movement to the side is safer than downslope. Avoid river valleys and low-lying areas after heavy rain. Watch for secondary floods that may follow landslides. After a landslide: check area for injured and trapped persons. Report hazards to authorities. Do not cross landslide debris — ground may still be unstable. Mark danger zones to prevent others from entering.",
            
            # First Aid Protocol
            "FIRST AID IN DISASTERS (NDRF Medical Protocol): Always prioritize: 1) Airway - check breathing, 2) Breathing - start rescue breathing if needed, 3) Circulation - check pulse, do CPR if no pulse. Control bleeding with direct pressure using clean cloth. Keep injured person warm and calm. NEVER move injured persons unless immediate danger exists. For drowning: start CPR immediately even if person appears dead. For burns: cool with clean water for 10-20 minutes — do NOT use ice or oil. For fractures: immobilize the injured part. Call 108 for ambulance. Document injuries for medical records.",
            
            # CPR Instructions
            "CPR (CARDIOPULMONARY RESUSCITATION): Place person on firm, flat surface. Position heel of one hand on chest center, place other hand on top. Push hard and fast at least 100 compressions/minute, pressing down 5-6 cm. After 30 compressions, give 2 rescue breaths. Continue CPR until emergency services arrive or person shows signs of life. For choking: perform Heimlich maneuver — stand behind person, place fist above navel, quick upward thrusts. If person becomes unconscious: start CPR immediately.",
            
            # Emergency Kit
            "EMERGENCY KIT ESSENTIALS (NDRF Guidelines): Water (1 litre per person per day for 3 days minimum). Non-perishable food (3-day supply): canned goods, dry fruits, biscuits. First aid kit with bandages, antiseptic, pain relievers, prescription medicines. Flashlight and extra batteries (check monthly). Whistle (3 blasts = distress signal). N95 dust mask (3 pieces per person). Plastic sheeting and duct tape (seal windows). Moist towelettes for hygiene. Wrench or pliers to turn off utilities. Manual can opener. Local emergency contact numbers written on paper. Cell phone with chargers and power bank. Important documents in waterproof container. Local maps.",
            
            # Evacuation Procedure
            "EVACUATION PROCEDURE (NDRF SOP 2023): Follow official evacuation orders immediately — do not delay. Use only designated evacuation routes (do not take shortcuts). Take emergency kit. Inform neighbors, especially elderly and disabled. Help vulnerable community members evacuate first. Lock home and turn off utilities (electricity, gas, water). Leave a note with your destination. Listen to official emergency broadcasts for updates. Do not return home until authorities declare area safe. Register at local relief camp. Keep family together and maintain contact information. Do not re-enter damaged areas.",
            
            # Community Resilience
            "COMMUNITY RESILIENCE (NDRF Community Guidelines): Form neighborhood emergency response committees with trained volunteers. Conduct regular mock drills (every 3-6 months). Identify vulnerable members: elderly, disabled, children, pregnant women. Create community resource map: water sources, food supplies, medical facilities, shelters. Establish communication tree for quick information dissemination. Designate community assembly point away from hazards. Train at least 2 persons per household in first aid. Share emergency contact numbers via paper list. Build social cohesion through preparedness activities. Coordinate with local administration for resources.",
            
            # Heatwave Protocol  
            "HEATWAVE PROTOCOL (SDMA Heat Action Plan 2023): Stay indoors between 12 PM–3 PM (peak heat hours). Drink water every 30 minutes even if not thirsty — avoid alcohol and caffeine. Wear light, loose, cotton clothing and wide-brimmed hat if going outside. Never leave children or elderly in parked vehicles (fatal within minutes). Use ORS solution (oral rehydration salts) for early heat exhaustion. Heat exhaustion symptoms: dizziness, nausea, excessive sweating — cool immediately. Heat stroke symptoms: body temperature above 104°F, confusion, no sweating — THIS IS LIFE-THREATENING. Cool immediately: cold water immersion, ice packs on neck/groin. Call 108 for ambulance immediately. Vulnerable: elderly, outdoor workers, homeless.",
            
            # Mental Health
            "POST-DISASTER MENTAL HEALTH (NDRF Psychosocial Support): Normal reactions include shock, grief, anxiety, disorientation — these are expected. Talk to trusted family members and friends about your experience. Maintain daily routines — sleep, meals, hygiene help normalize. Avoid excessive news and social media consumption — can increase anxiety. Help others — volunteering aids recovery and builds community. Community support groups are vital — don't isolate. Seek professional mental health help if symptoms persist beyond 2-3 weeks. NIMHANS Helpline: 080-46110007. Signs to watch: persistent nightmares, social withdrawal, substance use, self-harm thoughts.",
            
            # Tsunami Protocol
            "TSUNAMI PROTOCOL (SDMA Coastal Guidelines): If you feel earthquake near coast (lasting more than 1 minute), move to high ground immediately even without tsunami warning. Do not go to beach to watch or photo tsunami. Tsunami waves can arrive in minutes. Move to higher ground or inland at least 1 km from shore. Stay away until official all-clear is given. Listen to emergency broadcasts for safety information. If caught in tsunami: climb to roof, grab floating objects, avoid debris. After tsunami: check for injuries, boil water before use, avoid floodwater, be aware of aftershocks.",
            
            # Wildfire Protocol
            "WILDFIRE PROTOCOL (Forest Fire Guidelines): Evacuate immediately when ordered. Close all windows and doors. Wear N95 mask, light-colored long sleeves, pants, gloves, hat. Drive with headlights on to improve visibility in smoke. If trapped, stay in car — better protection than outdoors. Move away from dead trees and avoid running uphill. If on foot, move downhill and away from smoke. In home: close all windows, remove curtains, fill sinks with water, stay in interior room away from windows. After fire: watch for hot spots, avoid ash and debris, listen for warnings.",
            
            # Storm/High Wind Protocol
            "STORM AND HIGH WIND PROTOCOL (SDMA Weather Safety): Take shelter indoors before storm arrives. Stay away from windows and doors. Do not use phone except for emergencies. Unplug electrical appliances to prevent surge damage. If outdoors: avoid tall trees, metal structures, power lines. Do not touch downed power lines. Get to low-lying ground (not under trees). If caught in vehicle: stay inside with seatbelt on. Do not try to drive through flooded areas. After storm: check home for damage, clear debris from roads, avoid standing water, use bottled water if mains are unsafe.",
            
            # Pandemic/Disease Protocol
            "PANDEMIC AND DISEASE RESPONSE (Health Ministry Guidelines): Follow government health advisories strictly. Maintain physical distance (2 meters) from sick persons. Wear masks, practice respiratory hygiene (cover cough/sneeze with elbow). Wash hands frequently with soap and water (20+ seconds). Avoid touching face, eyes, nose. Quarantine if exposed for recommended period. Seek medical help for symptoms: fever, cough, breathing difficulty. Call health helpline (1075 for COVID) before visiting hospital. Follow vaccination schedules. Maintain social connections safely (video calls, phone). Mental health support available through toll-free numbers.",
        ]
        
        if FAISS_AVAILABLE and self.embedder:
            self._rebuild_index()
        self._save_chunks()
        print(f"🌱 Seeded {len(self.chunks)} comprehensive NDRF/SDMA knowledge chunks")
