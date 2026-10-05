from abc import ABC, abstractmethod


class IStorage(ABC):
    @abstractmethod
    async def upload(
        self,
        *,
        file_name: str,
        file_bytes: bytes,
        content_type: str,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, *, file_name: str) -> None:
        raise NotImplementedError
