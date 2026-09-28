import json
from typing import Any, List

from src.database import RedisConnection
from src.interfaces.repository import ICacheRepository


class RedisRepository(ICacheRepository):
    def __init__(self, redis_conn: RedisConnection) -> None:
        self.redis_conn = redis_conn

    async def insert(self, key: str, value: Any) -> None:
        await self.redis_conn.execute(
            {
                "command": "SET",
                "key": key,
            },
            {
                "value": json.dumps(value, default=str),
            },
        )

    async def get(self, key: str) -> List[dict] | str | None:
        response = await self.redis_conn.execute(
            {
                "command": "GET",
                "key": key,
            }
        )
        if response:
            try:
                return json.loads(response)
            except json.decoder.JSONDecodeError:
                return response
        return response

    async def delete(self, *keys: str) -> None:
        for key in keys:
            if "*" in key:
                cursor = await self.redis_conn.execute(
                    {
                        "command": "SCAN_ITER",
                        "pattern": key,
                    }
                )
                async for cache_key in cursor:
                    await self.redis_conn.execute(
                        {
                            "command": "DELETE",
                            "key": cache_key,
                        }
                    )
            else:
                await self.redis_conn.execute(
                    {
                        "command": "DELETE",
                        "key": key,
                    }
                )