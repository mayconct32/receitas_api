from ..interfaces.repository import ICacheRepository


class CacheService(ICacheRepository):
    def __init__(self, cache_repository: ICacheRepository) -> None:
        self.cache_repository = cache_repository

    async def insert(self, key: str, value) -> None:
        await self.cache_repository.insert(key, value)

    async def get(self, key: str):
        return await self.cache_repository.get(key)

    async def delete(self, *keys: str) -> None:
        await self.cache_repository.delete(*keys)
