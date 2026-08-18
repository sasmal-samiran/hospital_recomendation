import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import os

logger = logging.getLogger(__name__)

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/app.db")

class Database:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they do not exist and seed initial demo/admin users."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    blood_group TEXT,
                    emergency_contact TEXT,
                    phone_number TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            # Recommendation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    timestamp TEXT NOT NULL,
                    origin_lat REAL NOT NULL,
                    origin_lon REAL NOT NULL,
                    radius_meters REAL NOT NULL,
                    recommended_hospital_name TEXT NOT NULL,
                    recommended_hospital_distance_km REAL,
                    recommended_hospital_duration_min REAL,
                    composite_score REAL NOT NULL,
                    weather_condition TEXT,
                    road_condition_label TEXT,
                    total_evaluated INTEGER NOT NULL,
                    raw_result_json TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            conn.commit()

        # Seed initial default users
        self._seed_default_users()

    def _seed_default_users(self):
        from app.core.security import hash_password
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Seed Admin
            cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@emergency.com",))
            if not cursor.fetchone():
                admin_pw_hash = hash_password("Admin@123")
                cursor.execute("""
                    INSERT INTO users (email, password_hash, full_name, role, blood_group, emergency_contact, phone_number, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (
                    "admin@emergency.com",
                    admin_pw_hash,
                    "System Administrator",
                    "admin",
                    "O+",
                    "+1-800-EMERGENCY",
                    "+1-800-999-0000",
                    datetime.now(timezone.utc).isoformat()
                ))

            # Seed Demo User
            cursor.execute("SELECT id FROM users WHERE email = ?", ("user@emergency.com",))
            if not cursor.fetchone():
                user_pw_hash = hash_password("User@123")
                cursor.execute("""
                    INSERT INTO users (email, password_hash, full_name, role, blood_group, emergency_contact, phone_number, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (
                    "user@emergency.com",
                    user_pw_hash,
                    "Alex Mercer (Demo User)",
                    "user",
                    "A+",
                    "+1-555-911-HELP",
                    "+1-555-019-2834",
                    datetime.now(timezone.utc).isoformat()
                ))
            
            conn.commit()
            logger.info("Database initialized with seed users.")

    # ------------------- USER OPERATIONS -------------------

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        role: str = "user",
        blood_group: Optional[str] = None,
        emergency_contact: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, role, blood_group, emergency_contact, phone_number, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (email.strip().lower(), password_hash, full_name.strip(), role, blood_group, emergency_contact, phone_number, now))
            conn.commit()
            new_id = cursor.lastrowid
            return self.get_user_by_id(new_id)

    def update_user_profile(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        blood_group: Optional[str] = None,
        emergency_contact: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            values = []
            if full_name is not None:
                updates.append("full_name = ?")
                values.append(full_name.strip())
            if blood_group is not None:
                updates.append("blood_group = ?")
                values.append(blood_group.strip())
            if emergency_contact is not None:
                updates.append("emergency_contact = ?")
                values.append(emergency_contact.strip())
            if phone_number is not None:
                updates.append("phone_number = ?")
                values.append(phone_number.strip())

            if not updates:
                return self.get_user_by_id(user_id)

            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, tuple(values))
            conn.commit()
            return self.get_user_by_id(user_id)

    def update_user_password(self, user_id: int, password_hash: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_user_role(self, user_id: int, role: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            conn.commit()
            return self.get_user_by_id(user_id)

    def list_all_users(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, full_name, role, blood_group, emergency_contact, phone_number, is_active, created_at FROM users ORDER BY id ASC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # ------------------- HISTORY OPERATIONS -------------------

    def save_history_record(
        self,
        user_id: Optional[int],
        origin_lat: float,
        origin_lon: float,
        radius_meters: float,
        recommended_hospital_name: str,
        recommended_hospital_distance_km: float,
        recommended_hospital_duration_min: float,
        composite_score: float,
        weather_condition: str,
        road_condition_label: str,
        total_evaluated: int,
        raw_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            raw_json_str = json.dumps(raw_result)
            cursor.execute("""
                INSERT INTO recommendation_history (
                    user_id, timestamp, origin_lat, origin_lon, radius_meters,
                    recommended_hospital_name, recommended_hospital_distance_km,
                    recommended_hospital_duration_min, composite_score,
                    weather_condition, road_condition_label, total_evaluated, raw_result_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, now, origin_lat, origin_lon, radius_meters,
                recommended_hospital_name, recommended_hospital_distance_km,
                recommended_hospital_duration_min, composite_score,
                weather_condition, road_condition_label, total_evaluated, raw_json_str
            ))
            conn.commit()
            rec_id = cursor.lastrowid
            return self.get_history_record_by_id(rec_id)

    def get_history_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recommendation_history WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["raw_result"] = json.loads(res.get("raw_result_json", "{}"))
            except Exception:
                res["raw_result"] = {}
            return res

    def get_user_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, timestamp, origin_lat, origin_lon, radius_meters,
                       recommended_hospital_name, recommended_hospital_distance_km,
                       recommended_hospital_duration_min, composite_score,
                       weather_condition, road_condition_label, total_evaluated, raw_result_json
                FROM recommendation_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["raw_result"] = json.loads(item.get("raw_result_json", "{}"))
                except Exception:
                    item["raw_result"] = {}
                results.append(item)
            return results

    def delete_user_history_record(self, record_id: int, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recommendation_history WHERE id = ? AND user_id = ?", (record_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    # ------------------- ADMIN OPERATIONS -------------------

    def get_all_history_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT h.id, h.user_id, u.email as user_email, u.full_name as user_name,
                       h.timestamp, h.origin_lat, h.origin_lon, h.radius_meters,
                       h.recommended_hospital_name, h.recommended_hospital_distance_km,
                       h.recommended_hospital_duration_min, h.composite_score,
                       h.weather_condition, h.road_condition_label, h.total_evaluated
                FROM recommendation_history h
                LEFT JOIN users u ON h.user_id = u.id
                ORDER BY h.id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_admin_metrics(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            total_users = cursor.fetchone()["total_users"]

            cursor.execute("SELECT COUNT(*) as total_admins FROM users WHERE role = 'admin'")
            total_admins = cursor.fetchone()["total_admins"]

            cursor.execute("SELECT COUNT(*) as total_recommendations FROM recommendation_history")
            total_recommendations = cursor.fetchone()["total_recommendations"]

            cursor.execute("SELECT AVG(composite_score) as avg_score FROM recommendation_history")
            avg_row = cursor.fetchone()
            avg_score = round(float(avg_row["avg_score"]), 2) if avg_row and avg_row["avg_score"] is not None else 0.0

            cursor.execute("SELECT AVG(recommended_hospital_duration_min) as avg_eta FROM recommendation_history")
            eta_row = cursor.fetchone()
            avg_eta = round(float(eta_row["avg_eta"]), 2) if eta_row and eta_row["avg_eta"] is not None else 0.0

            return {
                "total_users": total_users,
                "total_admins": total_admins,
                "total_recommendations": total_recommendations,
                "average_composite_score": avg_score,
                "average_arrival_duration_min": avg_eta,
                "database_engine": "SQLite3 (Self-contained)",
                "system_status": "All Systems Operational"
            }

db = Database()
