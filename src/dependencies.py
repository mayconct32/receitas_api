from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.database import MongoDBConnection, MysqlDBConnection, RedisConnection
from src.interfaces.connection_db import IDBConnection
from src.interfaces.repository import IChefRepository, IRecipeRepository, ICacheRepository
from src.interfaces.storage import IStorage
from src.repositories.chef_repository import ChefRepository
from src.repositories.recipe_repository import RecipeRepository
from src.repositories.redis_repository import RedisRepository
from src.services.auth_service import AuthService
from src.services.cache_service import CacheService
from src.services.chef_service import ChefService
from src.services.recipe_service import RecipeService
from src.services.storage_service import LocalstackS3Storage, RecipeImageService


def get_redis_repository() -> ICacheRepository:
    return RedisRepository(RedisConnection())


def get_cache_service(
    cache_repository: ICacheRepository = Depends(get_redis_repository),
) -> CacheService:
    return CacheService(cache_repository)


def get_mysql_connection() -> IDBConnection:
    return MysqlDBConnection()


def get_mongodb_connection() -> IDBConnection:
    return MongoDBConnection()


def get_storage_service() -> IStorage:
    return LocalstackS3Storage()


# Chef Dependecies
def get_chef_repository(
    connection: IDBConnection = Depends(get_mysql_connection),
) -> IChefRepository:
    return ChefRepository(connection)


def get_chef_service(
    chef_repository: IChefRepository = Depends(get_chef_repository),
    cache_service: CacheService = Depends(get_cache_service),
) -> ChefService:
    return ChefService(chef_repository, cache_service)


def get_auth_service(
    chef_repository: IChefRepository = Depends(get_chef_repository),
    cache_service: CacheService = Depends(get_cache_service),
) -> AuthService:
    return AuthService(chef_repository, cache_service)


async def get_current_chef(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/v1/chefs/auth")),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    return await auth_service.decode_token(token)


# Recipes Dependencies
def get_recipe_repository(
    connection: IDBConnection = Depends(get_mongodb_connection),
) -> IRecipeRepository:
    return RecipeRepository(connection)


def get_recipe_service(
    repository: IRecipeRepository = Depends(get_recipe_repository),
    cache_service: CacheService = Depends(get_cache_service),
    image_storage: IStorage = Depends(get_storage_service),
) -> RecipeService:
    recipe_image_service = RecipeImageService(image_storage)
    return RecipeService(repository, cache_service, image_handler=recipe_image_service)


ChefServiceDep = Annotated[ChefService, Depends(get_chef_service)]

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

CurrentChef = Annotated[dict, Depends(get_current_chef)]

AuthRequestForm = Annotated[OAuth2PasswordRequestForm, Depends()]

RecipeServiceDep = Annotated[RecipeService, Depends(get_recipe_service)]

RedisCache = Annotated[CacheService, Depends(get_cache_service)]
