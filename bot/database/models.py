"""
Database models and operations for DefectMaster Bot
"""
import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any
import config
from bot.database.base import DatabaseInterface


class Database(DatabaseInterface):
    """Database manager for SQLite"""

    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 0,
                    context_object TEXT,
                    spreadsheet_id TEXT,
                    is_admin BOOLEAN DEFAULT 0,
                    referred_by INTEGER,
                    referral_bonus_given BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migration: add referral columns if they don't exist
            try:
                await db.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
            except:
                pass  # Column already exists
            try:
                await db.execute("ALTER TABLE users ADD COLUMN referral_bonus_given BOOLEAN DEFAULT 0")
            except:
                pass  # Column already exists

            # Payments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE,
                    user_id INTEGER,
                    amount INTEGER,
                    credits INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Analysis history table (optional, for analytics)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_uuid TEXT UNIQUE,
                    user_id INTEGER,
                    photo_id TEXT,
                    photo_url TEXT,
                    context_object TEXT,
                    defects_found INTEGER,
                    is_relevant BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Migration: add analysis_uuid and photo_url if they don't exist
            try:
                await db.execute("ALTER TABLE analysis_history ADD COLUMN analysis_uuid TEXT")
            except:
                pass  # Column already exists
            try:
                await db.execute("ALTER TABLE analysis_history ADD COLUMN photo_url TEXT")
            except:
                pass  # Column already exists

            # Defects table - detailed defect information
            await db.execute("""
                CREATE TABLE IF NOT EXISTS defects (
                    defect_uuid TEXT PRIMARY KEY,
                    analysis_uuid TEXT,
                    user_id INTEGER,
                    defect_index INTEGER,
                    defect_name TEXT,
                    location TEXT,
                    criticality TEXT,
                    cause TEXT,
                    norm_violation TEXT,
                    recommendation TEXT,
                    status TEXT DEFAULT 'open',
                    telegram_message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_uuid) REFERENCES analysis_history(analysis_uuid),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # User lifecycle events (start/blocked tracking)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    event_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def create_user(self, user_id: int, username: str = None, referred_by: int = None) -> bool:
        """Create new user with free credits (+ referral bonus if applicable)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Calculate starting balance
                starting_balance = config.FREE_CREDITS
                if referred_by:
                    starting_balance += config.REFERRAL_BONUS_INVITED

                await db.execute(
                    """INSERT INTO users (user_id, username, balance, is_admin, referred_by)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, username, starting_balance, user_id in config.ADMIN_IDS, referred_by)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_referrer(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the user who referred this user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # First get referred_by
            async with db.execute(
                "SELECT referred_by FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row or not row['referred_by']:
                    return None
                referrer_id = row['referred_by']

            # Then get referrer info
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (referrer_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def mark_referral_bonus_given(self, user_id: int) -> bool:
        """Mark that referral bonus has been given to the inviter for this user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET referral_bonus_given = 1 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
            return True

    async def is_referral_bonus_given(self, user_id: int) -> bool:
        """Check if referral bonus has been given for this user"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT referral_bonus_given FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return bool(row[0]) if row else False

    async def update_balance(self, user_id: int, amount: int) -> bool:
        """Update user balance (can be positive or negative)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (amount, user_id)
            )
            await db.commit()
            return True

    async def set_context(self, user_id: int, context: str) -> bool:
        """Set current object context for user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET context_object = ? WHERE user_id = ?",
                (context, user_id)
            )
            await db.commit()
            return True

    async def set_spreadsheet(self, user_id: int, spreadsheet_id: str) -> bool:
        """Save user's Google Spreadsheet ID"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET spreadsheet_id = ? WHERE user_id = ?",
                (spreadsheet_id, user_id)
            )
            await db.commit()
            return True

    async def create_payment(self, order_id: str, user_id: int, amount: int, credits: int) -> bool:
        """Create payment record"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    """INSERT INTO payments (order_id, user_id, amount, credits, status)
                       VALUES (?, ?, ?, ?, 'pending')""",
                    (order_id, user_id, amount, credits)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def update_payment_status(self, order_id: str, status: str) -> bool:
        """Update payment status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE payments
                   SET status = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE order_id = ?""",
                (status, order_id)
            )
            await db.commit()
            return True

    async def get_payment(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by order ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM payments WHERE order_id = ?", (order_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def log_analysis(self, user_id: int, photo_id: str, context: str,
                          defects_found: int, is_relevant: bool) -> bool:
        """Log photo analysis to history (legacy method, use save_analysis instead)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO analysis_history
                   (user_id, photo_id, context_object, defects_found, is_relevant)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, photo_id, context, defects_found, is_relevant)
            )
            await db.commit()
            return True

    async def save_analysis(self, analysis_uuid: str, user_id: int, photo_id: str,
                           photo_url: str, context: str, defects_found: int,
                           is_relevant: bool) -> bool:
        """Save photo analysis to history with UUID and photo URL"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    """INSERT INTO analysis_history
                       (analysis_uuid, user_id, photo_id, photo_url, context_object,
                        defects_found, is_relevant)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (analysis_uuid, user_id, photo_id, photo_url, context,
                     defects_found, is_relevant)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_analysis(self, analysis_uuid: str) -> Optional[Dict[str, Any]]:
        """Get analysis by UUID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM analysis_history WHERE analysis_uuid = ?",
                (analysis_uuid,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def save_defect(self, defect_uuid: str, analysis_uuid: str, user_id: int,
                         defect_index: int, defect_name: str, location: str,
                         criticality: str, cause: str, norm_violation: str,
                         recommendation: str, telegram_message_id: int = None) -> bool:
        """Save defect to database"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    """INSERT INTO defects
                       (defect_uuid, analysis_uuid, user_id, defect_index,
                        defect_name, location, criticality, cause, norm_violation,
                        recommendation, telegram_message_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (defect_uuid, analysis_uuid, user_id, defect_index,
                     defect_name, location, criticality, cause, norm_violation,
                     recommendation, telegram_message_id)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_defect(self, defect_uuid: str) -> Optional[Dict[str, Any]]:
        """Get defect by UUID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM defects WHERE defect_uuid = ?",
                (defect_uuid,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_defects_by_analysis(self, analysis_uuid: str) -> list:
        """Get all defects for a specific analysis"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM defects WHERE analysis_uuid = ? ORDER BY defect_index",
                (analysis_uuid,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_defects_by_user(self, user_id: int, limit: int = 100) -> list:
        """Get recent defects for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM defects
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_defect_status(self, defect_uuid: str, status: str) -> bool:
        """Update defect status (open/fixed/verified)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE defects SET status = ? WHERE defect_uuid = ?",
                (status, defect_uuid)
            )
            await db.commit()
            return True

    async def update_defect_telegram_message(self, defect_uuid: str,
                                             telegram_message_id: int) -> bool:
        """Update telegram message ID for defect"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE defects SET telegram_message_id = ? WHERE defect_uuid = ?",
                (telegram_message_id, defect_uuid)
            )
            await db.commit()
            return True

    async def delete_user(self, user_id: int) -> bool:
        """Delete user and all related data from database"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Delete from analysis_history
                await db.execute(
                    "DELETE FROM analysis_history WHERE user_id = ?",
                    (user_id,)
                )
                # Delete from payments
                await db.execute(
                    "DELETE FROM payments WHERE user_id = ?",
                    (user_id,)
                )
                # Delete from users
                await db.execute(
                    "DELETE FROM users WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
                return True
            except Exception:
                return False

    async def log_event(self, user_id: int, event_type: str) -> bool:
        """
        Log user lifecycle event (start/blocked)

        Args:
            user_id: User ID
            event_type: Event type ('start' or 'blocked')

        Returns:
            True if logged successfully
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO user_events (user_id, event_type) VALUES (?, ?)",
                    (user_id, event_type)
                )
                await db.commit()
                return True
            except Exception:
                return False

    def get_connection(self):
        """Get database connection context manager"""
        return aiosqlite.connect(self.db_path)


# Global database instance
db = Database()
