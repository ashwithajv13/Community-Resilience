"""
Community Resilience Database
==============================
SQLite-based models for community groups, knowledge sharing, resources, training, recovery.
"""

import os
import json
import sqlite3
import time
from datetime import datetime
from typing import List, Optional, Dict

DB_PATH = "data/community.db"


class CommunityDB:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Create all tables if they don't exist."""
        cursor = self.conn.cursor()

        # Community Groups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_groups (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                description TEXT,
                leader_id TEXT NOT NULL,
                members_count INTEGER DEFAULT 1,
                created_at REAL,
                created_at_readable TEXT
            )
        """)

        # Community Members
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_members (
                id INTEGER PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                location TEXT,
                skills TEXT,
                created_at REAL
            )
        """)

        # Group Membership
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY,
                group_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at REAL,
                FOREIGN KEY (group_id) REFERENCES community_groups(id)
            )
        """)

        # Knowledge Sharing (Tips & Lessons)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_tips (
                id INTEGER PRIMARY KEY,
                group_id INTEGER,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                validation_status TEXT DEFAULT 'pending',
                upvotes INTEGER DEFAULT 0,
                created_at REAL,
                validated_by TEXT,
                validation_notes TEXT
            )
        """)

        # Resource Registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY,
                group_id INTEGER,
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                description TEXT NOT NULL,
                quantity INTEGER,
                location TEXT,
                availability TEXT DEFAULT 'available',
                created_at REAL,
                FOREIGN KEY (group_id) REFERENCES community_groups(id)
            )
        """)

        # Training & Drills
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_sessions (
                id INTEGER PRIMARY KEY,
                group_id INTEGER NOT NULL,
                organizer_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                scheduled_date TEXT,
                status TEXT DEFAULT 'scheduled',
                participants INTEGER DEFAULT 0,
                created_at REAL,
                FOREIGN KEY (group_id) REFERENCES community_groups(id)
            )
        """)

        # Training Completion
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_completions (
                id INTEGER PRIMARY KEY,
                session_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                completed_at REAL,
                certificate_issued INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES training_sessions(id)
            )
        """)

        # Recovery Support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recovery_requests (
                id INTEGER PRIMARY KEY,
                group_id INTEGER,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                created_at REAL,
                resolved_at REAL,
                FOREIGN KEY (group_id) REFERENCES community_groups(id)
            )
        """)

        # Community Activity Log (for blockchain)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY,
                activity_type TEXT NOT NULL,
                group_id INTEGER,
                user_id TEXT,
                details TEXT,
                created_at REAL
            )
        """)

        self.conn.commit()

    # ─────────────────────────────────────────────
    # COMMUNITY GROUPS
    # ─────────────────────────────────────────────

    def create_group(self, name: str, location: str, description: str, leader_id: str) -> Dict:
        cursor = self.conn.cursor()
        now = time.time()
        readable = datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S UTC")
        try:
            cursor.execute("""
                INSERT INTO community_groups (name, location, description, leader_id, created_at, created_at_readable)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, location, description, leader_id, now, readable))
            group_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO group_members (group_id, user_id, role, joined_at)
                VALUES (?, ?, ?, ?)
            """, (group_id, leader_id, 'organizer', now))
            self.conn.commit()
            self._log_activity('group_created', group_id, leader_id, f'Group "{name}" created in {location}')
            return {'id': group_id, 'name': name, 'status': 'created'}
        except sqlite3.IntegrityError:
            return {'error': f'Group "{name}" already exists'}

    def get_groups(self, location: Optional[str] = None) -> List[Dict]:
        cursor = self.conn.cursor()
        if location:
            cursor.execute("SELECT * FROM community_groups WHERE location = ?", (location,))
        else:
            cursor.execute("SELECT * FROM community_groups")
        return [dict(row) for row in cursor.fetchall()]

    def get_group_members(self, group_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT cm.*, gm.role, gm.joined_at
            FROM community_members cm
            JOIN group_members gm ON cm.user_id = gm.user_id
            WHERE gm.group_id = ?
        """, (group_id,))
        return [dict(row) for row in cursor.fetchall()]

    def add_member_to_group(self, group_id: int, user_id: str, name: str, email: str = None, phone: str = None, location: str = None) -> Dict:
        cursor = self.conn.cursor()
        now = time.time()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO community_members (user_id, name, email, phone, location, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, name, email, phone, location, now))
            cursor.execute("""
                INSERT INTO group_members (group_id, user_id, role, joined_at)
                VALUES (?, ?, ?, ?)
            """, (group_id, user_id, 'member', now))
            cursor.execute("UPDATE community_groups SET members_count = members_count + 1 WHERE id = ?", (group_id,))
            self.conn.commit()
            self._log_activity('member_joined', group_id, user_id, f'User {name} joined group')
            return {'status': 'joined', 'group_id': group_id}
        except Exception as e:
            return {'error': str(e)}

    # ─────────────────────────────────────────────
    # KNOWLEDGE SHARING
    # ─────────────────────────────────────────────

    def post_tip(self, group_id: int, user_id: str, category: str, title: str, content: str) -> Dict:
        cursor = self.conn.cursor()
        now = time.time()
        cursor.execute("""
            INSERT INTO knowledge_tips (group_id, user_id, category, title, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (group_id, user_id, category, title, content, now))
        tip_id = cursor.lastrowid
        self.conn.commit()
        self._log_activity('tip_posted', group_id, user_id, f'Tip: {title}')
        return {'id': tip_id, 'status': 'posted', 'validation_status': 'pending'}

    def get_tips_by_category(self, category: str, validated_only: bool = False) -> List[Dict]:
        cursor = self.conn.cursor()
        if validated_only:
            cursor.execute("""
                SELECT * FROM knowledge_tips 
                WHERE category = ? AND validation_status = 'verified'
                ORDER BY upvotes DESC
            """, (category,))
        else:
            cursor.execute("""
                SELECT * FROM knowledge_tips 
                WHERE category = ?
                ORDER BY upvotes DESC
            """, (category,))
        return [dict(row) for row in cursor.fetchall()]

    def validate_tip(self, tip_id: int, validated_by: str, is_valid: bool, notes: str = "") -> Dict:
        cursor = self.conn.cursor()
        status = 'verified' if is_valid else 'rejected'
        cursor.execute("""
            UPDATE knowledge_tips 
            SET validation_status = ?, validated_by = ?, validation_notes = ?
            WHERE id = ?
        """, (status, validated_by, notes, tip_id))
        self.conn.commit()
        self._log_activity('tip_validated', None, validated_by, f'Tip {tip_id} {status}')
        return {'tip_id': tip_id, 'validation_status': status}

    def upvote_tip(self, tip_id: int) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE knowledge_tips SET upvotes = upvotes + 1 WHERE id = ?", (tip_id,))
        self.conn.commit()
        return {'tip_id': tip_id, 'status': 'upvoted'}

    # ─────────────────────────────────────────────
    # RESOURCE COORDINATOR
    # ─────────────────────────────────────────────

    def register_resource(self, group_id: int, user_id: str, resource_type: str, description: str, quantity: int, location: str) -> Dict:
        cursor = self.conn.cursor()
        now = time.time()
        cursor.execute("""
            INSERT INTO resources (group_id, user_id, resource_type, description, quantity, location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (group_id, user_id, resource_type, description, quantity, location, now))
        resource_id = cursor.lastrowid
        self.conn.commit()
        self._log_activity('resource_registered', group_id, user_id, f'{resource_type}: {description}')
        return {'id': resource_id, 'status': 'registered'}

    def get_available_resources(self, group_id: int = None) -> List[Dict]:
        cursor = self.conn.cursor()
        if group_id:
            cursor.execute("""
                SELECT * FROM resources 
                WHERE availability = 'available' AND group_id = ?
                ORDER BY created_at DESC
            """, (group_id,))
        else:
            cursor.execute("""
                SELECT * FROM resources 
                WHERE availability = 'available'
                ORDER BY created_at DESC
            """)
        return [dict(row) for row in cursor.fetchall()]

    def request_resource(self, resource_id: int, requester_id: str) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE resources SET availability = 'reserved' WHERE id = ?", (resource_id,))
        self.conn.commit()
        self._log_activity('resource_requested', None, requester_id, f'Resource {resource_id} requested')
        return {'resource_id': resource_id, 'status': 'reserved'}

    # ─────────────────────────────────────────────
    # PREPAREDNESS TRAINING
    # ─────────────────────────────────────────────

    def schedule_training(self, group_id: int, organizer_id: str, title: str, category: str, description: str, scheduled_date: str) -> Dict:
        cursor = self.conn.cursor()
        now = time.time()
        cursor.execute("""
            INSERT INTO training_sessions (group_id, organizer_id, title, category, description, scheduled_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (group_id, organizer_id, title, category, description, scheduled_date, now))
        session_id = cursor.lastrowid
        self.conn.commit()
        self._log_activity('training_scheduled', group_id, organizer_id, f'Training: {title}')
        return {'id': session_id, 'status': 'scheduled'}

    def record_training_completion(self, session_id: int, user_id: str) -> Dict:
        cursor = self.conn.cursor()
        now = time.time()
        cursor.execute("""
            INSERT INTO training_completions (session_id, user_id, completed_at)
            VALUES (?, ?, ?)
        """, (session_id, user_id, now))
        cursor.execute("UPDATE training_sessions SET participants = participants + 1 WHERE id = ?", (session_id,))
        self.conn.commit()
        self._log_activity('training_completed', None, user_id, f'User completed training session {session_id}')
        return {'session_id': session_id, 'user_id': user_id, 'status': 'completed'}

    def get_training_progress(self, group_id: int) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*) as sessions, SUM(participants) as total_participants
            FROM training_sessions
            WHERE group_id = ? AND status = 'completed'
            GROUP BY category
        """, (group_id,))
        rows = cursor.fetchall()
        return {row['category']: {'sessions': row['sessions'], 'participants': row['total_participants']} for row in rows}

    # ─────────────────────────────────────────────
    # RECOVERY SUPPORT
    # ─────────────────────────────────────────────

    def post_recovery_request(self, group_id: int, user_id: str, category: str, description: str, priority: str = 'normal') -> Dict:
        cursor = self.conn.cursor()
        now = time.time()
        cursor.execute("""
            INSERT INTO recovery_requests (group_id, user_id, category, description, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (group_id, user_id, category, description, priority, now))
        request_id = cursor.lastrowid
        self.conn.commit()
        self._log_activity('recovery_request', group_id, user_id, f'{category}: {description[:50]}...')
        return {'id': request_id, 'status': 'open'}

    def get_open_recovery_requests(self, group_id: int = None) -> List[Dict]:
        cursor = self.conn.cursor()
        if group_id:
            cursor.execute("""
                SELECT * FROM recovery_requests
                WHERE status = 'open' AND group_id = ?
                ORDER BY priority DESC, created_at
            """, (group_id,))
        else:
            cursor.execute("""
                SELECT * FROM recovery_requests
                WHERE status = 'open'
                ORDER BY priority DESC, created_at
            """)
        return [dict(row) for row in cursor.fetchall()]

    def resolve_recovery_request(self, request_id: int, resolution_notes: str = "") -> Dict:
        cursor = self.conn.cursor()
        now = time.time()
        cursor.execute("""
            UPDATE recovery_requests 
            SET status = 'resolved', resolved_at = ?
            WHERE id = ?
        """, (now, request_id))
        self.conn.commit()
        self._log_activity('recovery_resolved', None, None, f'Request {request_id} resolved')
        return {'request_id': request_id, 'status': 'resolved'}

    # ─────────────────────────────────────────────
    # ACTIVITY LOG
    # ─────────────────────────────────────────────

    def _log_activity(self, activity_type: str, group_id: int = None, user_id: str = None, details: str = ""):
        cursor = self.conn.cursor()
        now = time.time()
        cursor.execute("""
            INSERT INTO activity_log (activity_type, group_id, user_id, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (activity_type, group_id, user_id, details, now))
        self.conn.commit()

    def get_group_activity(self, group_id: int, limit: int = 50) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM activity_log
            WHERE group_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (group_id, limit))
        return [dict(row) for row in cursor.fetchall()]

    def get_all_activity(self, limit: int = 100) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM activity_log
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
