"""
Redis connectivity health check.
"""

import logging

from redis.asyncio import Redis

logger = logging.getLogger("equityiq.health")


class RedisHealth:
    """
    Checks the connectivity of the Redis cache/broker server.
    """

    def __init__(self, redis_url: str) -> None:
        """
        Initializes the RedisHealth checker.

        Args:
            redis_url: Connection string for Redis.
        """
        self.redis_url = redis_url

    async def check_health(self) -> bool:
        """
        Pings Redis to verify connectivity.

        Returns:
            True if connection is healthy, otherwise False.
        """
        client = None
        try:
            client = Redis.from_url(self.redis_url, socket_timeout=2.0)
            await client.ping()
            return True
        except Exception as exc:
            logger.error(f"Redis health check failed on {self.redis_url}: {exc}")
            return False
        finally:
            if client is not None:
                await client.close()
        # Closing the client returns the connection back to the pool
