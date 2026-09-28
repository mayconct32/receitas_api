from abc import ABC, abstractmethod
from typing import List, Any

from src.models.chef import Chef
from src.models.recipe import ResponseRecipe


class IRepository[T](ABC):
    @abstractmethod
    async def get_all(self, offset: int, limit: int) -> List[T]:
        raise NotImplementedError

    @abstractmethod
    async def get(self, id: int) -> T:
        raise NotImplementedError

    @abstractmethod
    async def add(self, data: T) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, id: int, data: T) -> None:
        raise NotImplementedError


class IChefRepository(IRepository[Chef]):
    @abstractmethod
    async def get_by_chef_name(self, chef_name: str) -> Chef:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Chef:
        raise NotImplementedError


class IRecipeRepository(IRepository[ResponseRecipe]):
    pass


class ICacheRepository(ABC):
    @abstractmethod
    async def insert(self, key: str, value: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, *keys: str) -> None:
        raise NotImplementedError
