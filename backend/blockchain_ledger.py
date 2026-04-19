

"""
Blockchain Ledger — ResilienceChain AI
========================================
Immutable SHA-256 linked ledger for SOS alerts and AI interactions.
Every block contains: index, timestamp, data, previous_hash, hash.
"""

import hashlib
import json
import os
import time
from typing import Optional


LEDGER_PATH = "data/ledger.json"


class BlockchainLedger:
    def __init__(self):
        self.chain = []
        self._load_or_create()

    # ──────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────

    def add_block(self, query: str, response: str, sources: list) -> dict:
        """Add a chat interaction block to the chain."""
        data = {
            "type": "CHAT",
            "query": query[:500],           # truncate for storage
            "response": response[:1000],
            "sources_count": len(sources),
            "rag_active": len(sources) > 0,
        }
        return self._append(data)

    def add_sos_block(self, location: str, details: str) -> dict:
        """Add an SOS alert block — highest priority record."""
        data = {
            "type": "SOS_ALERT",
            "location": location,
            "details": details[:500],
            "priority": "CRITICAL",
            "emergency_contacts": {
                "national_emergency": "112",
                "ndrf_helpline": "1078",
                "disaster_management": "1070",
                "ambulance": "108",
            },
        }
        return self._append(data)

    def add_community_activity_block(self, activity_type: str, group_name: str, user_id: str, details: str, activity_data: dict = None) -> dict:
        """Add a community resilience building activity block."""
        data = {
            "type": "COMMUNITY_ACTIVITY",
            "activity_type": activity_type,
            "group": group_name,
            "user_id": user_id,
            "details": details[:500],
            "activity_data": activity_data or {},
        }
        return self._append(data)

    def is_valid(self) -> bool:
        """Verify the full chain integrity."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Verify current block hash
            if current["hash"] != self._compute_hash(current):
                return False

            # Verify chain linkage
            if current["previous_hash"] != previous["hash"]:
                return False

        return True

    def get_sos_alerts(self) -> list:
        """Return all SOS alert blocks."""
        return [b for b in self.chain if b["data"].get("type") == "SOS_ALERT"]

    # ──────────────────────────────────────────
    # INTERNAL
    # ──────────────────────────────────────────

    def _genesis(self) -> dict:
        """Create the genesis (first) block."""
        block = {
            "index": 0,
            "timestamp": time.time(),
            "timestamp_readable": time.strftime("%Y-%m-%d %Human:%M:%S UTC", time.gmtime()),
            "data": {
                "type": "GENESIS",
                "message": "ResilienceChain AI Ledger initialized",
                "version": "1.0.0",
                "team": "CodeChain Hackers",
            },
            "previous_hash": "0" * 64,
            "hash": "",
        }
        block["hash"] = self._compute_hash(block)
        return block

    def _append(self, data: dict) -> dict:
        previous_block = self.chain[-1]
        block = {
            "index": len(self.chain),
            "timestamp": time.time(),
            "timestamp_readable": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "data": data,
            "previous_hash": previous_block["hash"],
            "hash": "",
        }
        block["hash"] = self._compute_hash(block)
        self.chain.append(block)
        self._save()
        print(f"⛓  Block #{block['index']} sealed | Hash: {block['hash'][:16]}...")
        return block

    def _compute_hash(self, block: dict) -> str:
        """SHA-256 hash of block content (excluding the hash field itself)."""
        block_copy = {k: v for k, v in block.items() if k != "hash"}
        block_string = json.dumps(block_copy, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def _load_or_create(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(LEDGER_PATH):
            with open(LEDGER_PATH, "r") as f:
                self.chain = json.load(f)
            print(f"⛓  Ledger loaded: {len(self.chain)} blocks | Valid: {self.is_valid()}")
        else:
            self.chain = [self._genesis()]
            self._save()
            print("⛓  New blockchain initialized with genesis block")

    def _save(self):
        with open(LEDGER_PATH, "w") as f:
            json.dump(self.chain, f, indent=2)
