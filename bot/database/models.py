"""
Database models and operations for DefectMaster Bot
"""
import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any
import config


class Database:
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
                    user_id INTEGER,
                    photo_id TEXT,
                    context_object TEXT,
                    defects_found INTEGER,
                    is_relevant BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        """Log photo analysis to history"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO analysis_history
                   (user_id, photo_id, context_object, defects_found, is_relevant)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, photo_id, context, defects_found, is_relevant)
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
