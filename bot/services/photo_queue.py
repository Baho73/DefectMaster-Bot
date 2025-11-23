"""
Photo processing queue with rate limiting for AI service
"""
import asyncio
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PhotoQueue:
    """
    Manages photo processing queue with rate limiting

    - Semaphore limits concurrent processing (default: 1 photo at a time)
    - Rate limiter ensures minimum interval between Gemini Pro requests
    """

    def __init__(self, max_concurrent: int = 1, min_interval_seconds: float = 30.0):
        """
        Initialize photo queue

        Args:
            max_concurrent: Maximum number of photos processing simultaneously
            min_interval_seconds: Minimum seconds between Gemini Pro API calls (for 2 RPM limit)
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.min_interval = min_interval_seconds
        self.last_request_time = 0
        self.lock = asyncio.Lock()
        self.queue_size = 0

        logger.info(f"Photo queue initialized: max_concurrent={max_concurrent}, min_interval={min_interval_seconds}s")

    async def process_photo(self, photo_data: bytes, context: str, ai_service) -> Dict[str, Any]:
        """
        Process photo with rate limiting

        Args:
            photo_data: Photo binary data
            context: User context
            ai_service: AI service instance

        Returns:
            Analysis results
        """
        # Wait for semaphore (queue position)
        async with self.semaphore:
            self.queue_size += 1
            current_position = self.queue_size

            logger.info(f"Photo entered processing queue. Position: {current_position}")

            try:
                # Rate limiting: ensure minimum interval between requests
                async with self.lock:
                    now = time.time()
                    time_since_last = now - self.last_request_time

                    if time_since_last < self.min_interval:
                        wait_time = self.min_interval - time_since_last
                        logger.info(f"Rate limiting: waiting {wait_time:.1f}s before next request")
                        await asyncio.sleep(wait_time)

                    self.last_request_time = time.time()

                # Process photo
                logger.info(f"Starting AI analysis for photo at position {current_position}")
                result = await ai_service.analyze_photo(photo_data, context)
                logger.info(f"AI analysis completed for position {current_position}")

                return result

            finally:
                self.queue_size -= 1

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue_size


# Global photo queue instance
photo_queue = PhotoQueue(max_concurrent=1, min_interval_seconds=30.0)
