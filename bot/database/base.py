"""
Database abstraction layer for DefectMaster Bot
Provides interface for different database backends (SQLite, PostgreSQL, etc.)
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class DatabaseInterface(ABC):
    """Abstract interface for database operations"""

    @abstractmethod
    async def init_db(self):
        """Initialize database with required tables"""
        pass

    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def create_user(self, user_id: int, username: str = None, referred_by: int = None) -> bool:
        """Create new user"""
        pass

    @abstractmethod
    async def get_referrer(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the user who referred this user"""
        pass

    @abstractmethod
    async def mark_referral_bonus_given(self, user_id: int) -> bool:
        """Mark that referral bonus has been given"""
        pass

    @abstractmethod
    async def is_referral_bonus_given(self, user_id: int) -> bool:
        """Check if referral bonus has been given"""
        pass

    @abstractmethod
    async def update_balance(self, user_id: int, amount: int) -> bool:
        """Update user balance"""
        pass

    @abstractmethod
    async def set_context(self, user_id: int, context: str) -> bool:
        """Set current object context for user"""
        pass

    @abstractmethod
    async def set_spreadsheet(self, user_id: int, spreadsheet_id: str) -> bool:
        """Save user's Google Spreadsheet ID"""
        pass

    @abstractmethod
    async def create_payment(self, order_id: str, user_id: int, amount: int, credits: int) -> bool:
        """Create payment record"""
        pass

    @abstractmethod
    async def update_payment_status(self, order_id: str, status: str) -> bool:
        """Update payment status"""
        pass

    @abstractmethod
    async def get_payment(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by order ID"""
        pass

    @abstractmethod
    async def log_analysis(self, user_id: int, photo_id: str, context: str,
                          defects_found: int, is_relevant: bool) -> bool:
        """Log photo analysis to history (legacy method)"""
        pass

    @abstractmethod
    async def save_analysis(self, analysis_uuid: str, user_id: int, photo_id: str,
                           photo_url: str, context: str, defects_found: int,
                           is_relevant: bool) -> bool:
        """Save photo analysis with UUID and photo URL"""
        pass

    @abstractmethod
    async def get_analysis(self, analysis_uuid: str) -> Optional[Dict[str, Any]]:
        """Get analysis by UUID"""
        pass

    @abstractmethod
    async def save_defect(self, defect_uuid: str, analysis_uuid: str, user_id: int,
                         defect_index: int, defect_name: str, location: str,
                         criticality: str, cause: str, norm_violation: str,
                         recommendation: str, telegram_message_id: int = None) -> bool:
        """Save defect to database"""
        pass

    @abstractmethod
    async def get_defect(self, defect_uuid: str) -> Optional[Dict[str, Any]]:
        """Get defect by UUID"""
        pass

    @abstractmethod
    async def get_defects_by_analysis(self, analysis_uuid: str) -> list:
        """Get all defects for a specific analysis"""
        pass

    @abstractmethod
    async def get_defects_by_user(self, user_id: int, limit: int = 100) -> list:
        """Get recent defects for a user"""
        pass

    @abstractmethod
    async def update_defect_status(self, defect_uuid: str, status: str) -> bool:
        """Update defect status"""
        pass

    @abstractmethod
    async def update_defect_telegram_message(self, defect_uuid: str,
                                             telegram_message_id: int) -> bool:
        """Update telegram message ID for defect"""
        pass

    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """Delete user and all related data"""
        pass

    @abstractmethod
    async def log_event(self, user_id: int, event_type: str) -> bool:
        """Log user lifecycle event"""
        pass
