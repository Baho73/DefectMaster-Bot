"""
Payment service for Tinkoff integration
"""
import hashlib
import aiohttp
from typing import Dict, Any, Optional
import config


class PaymentService:
    """Service for handling Tinkoff payments"""

    API_URL = "https://securepay.tinkoff.ru/v2/"

    def __init__(self):
        self.terminal_key = config.TINKOFF_TERMINAL_KEY
        self.secret_key = config.TINKOFF_SECRET_KEY

    def _generate_token(self, params: Dict[str, Any]) -> str:
        """Generate signature token for request"""
        # Add credentials
        token_params = {**params, 'Password': self.secret_key}

        # Remove Receipt and Data fields
        token_params.pop('Receipt', None)
        token_params.pop('DATA', None)

        # Sort and concatenate
        sorted_values = [str(v) for k, v in sorted(token_params.items())]
        concatenated = ''.join(sorted_values)

        # Hash
        return hashlib.sha256(concatenated.encode()).hexdigest()

    async def init_payment(self, order_id: str, amount: int, description: str,
                          user_id: int) -> Optional[Dict[str, Any]]:
        """
        Initialize payment

        Args:
            order_id: Unique order ID
            amount: Amount in kopecks (e.g., 19900 for 199 RUB)
            description: Payment description
            user_id: Telegram user ID

        Returns:
            Payment data with PaymentURL or None on error
        """
        params = {
            'TerminalKey': self.terminal_key,
            'Amount': amount,
            'OrderId': order_id,
            'Description': description,
            'DATA': {
                'user_id': user_id
            }
        }

        params['Token'] = self._generate_token(params)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.API_URL}Init",
                json=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('Success'):
                        return result
                return None

    async def check_payment_status(self, payment_id: str) -> Optional[str]:
        """
        Check payment status

        Args:
            payment_id: Payment ID from Tinkoff

        Returns:
            Payment status or None
        """
        params = {
            'TerminalKey': self.terminal_key,
            'PaymentId': payment_id
        }

        params['Token'] = self._generate_token(params)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.API_URL}GetState",
                json=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('Success'):
                        return result.get('Status')
                return None

    def verify_notification(self, notification: Dict[str, Any]) -> bool:
        """
        Verify notification from Tinkoff

        Args:
            notification: Notification data from webhook

        Returns:
            True if signature is valid
        """
        received_token = notification.get('Token')
        if not received_token:
            return False

        # Remove Token from params
        params = {k: v for k, v in notification.items() if k != 'Token'}

        # Generate expected token
        expected_token = self._generate_token(params)

        return received_token == expected_token


# Global payment service instance
payment_service = PaymentService()
