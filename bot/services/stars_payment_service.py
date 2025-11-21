"""
Telegram Stars payment service for DefectMaster Bot
"""
from typing import Dict, Any
from aiogram.types import LabeledPrice


class StarsPaymentService:
    """Service for handling Telegram Stars payments"""

    def __init__(self):
        # Telegram Stars prices (1 Star ≈ 2-3 рубля в зависимости от региона)
        # Для России примерно: 1 Star ≈ 2.5 рубля
        self.packages = {
            "small": {
                "credits": 20,
                "stars": 80,  # ~200₽
                "title": "20 фото",
                "description": "Пакет 20 анализов фотографий"
            },
            "medium": {
                "credits": 50,
                "stars": 160,  # ~400₽
                "title": "50 фото",
                "description": "Пакет 50 анализов фотографий"
            },
            "large": {
                "credits": 100,
                "stars": 280,  # ~700₽
                "title": "100 фото",
                "description": "Пакет 100 анализов фотографий"
            }
        }

    def get_package(self, package_key: str) -> Dict[str, Any]:
        """Get package info by key"""
        return self.packages.get(package_key)

    def create_invoice_payload(self, user_id: int, package_key: str) -> str:
        """Create unique payload for invoice"""
        return f"{user_id}:{package_key}"

    def parse_invoice_payload(self, payload: str) -> Dict[str, Any]:
        """Parse payload from invoice"""
        try:
            user_id, package_key = payload.split(":")
            return {
                "user_id": int(user_id),
                "package_key": package_key
            }
        except:
            return None

    def get_invoice_params(self, package_key: str, user_id: int) -> Dict[str, Any]:
        """
        Get invoice parameters for Telegram Stars payment

        Returns params for bot.send_invoice()
        """
        package = self.packages.get(package_key)
        if not package:
            return None

        return {
            "title": f"DefectMaster - {package['title']}",
            "description": package['description'],
            "payload": self.create_invoice_payload(user_id, package_key),
            "currency": "XTR",  # Telegram Stars currency code
            "prices": [
                LabeledPrice(label=package['title'], amount=package['stars'])
            ]
        }


# Global Stars payment service instance
stars_payment_service = StarsPaymentService()
