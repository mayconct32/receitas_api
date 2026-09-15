from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.database import MongoDBConnection, MysqlDBConnection, RedisConnection
from src.interfaces.connection_db import IDBConnection
from src.interfaces.repository import IChefRepository, IRecipeRepository
from src.interfaces.storage import IStorage
from src.repositories.chef_repository import ChefRepository
from src.repositories.recipe_repository import RecipeRepository
from src.repositories.redis_repository import RedisRepository
from src.services.auth_service import AuthService
from src.services.chef_service import ChefService
from src.services.recipe_service import RecipeService
from src.services.storage_service import LocalstackS3Storage


def get_redis_repository() -> RedisRepository:
    return RedisRepository(RedisConnection())


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
    redis_repository: RedisRepository = Depends(get_redis_repository),
) -> ChefService:
    return ChefService(chef_repository, redis_repository)


def get_auth_service(
    chef_repository: IChefRepository = Depends(get_chef_repository),
    redis_repository: RedisRepository = Depends(get_redis_repository),
) -> AuthService:
    return AuthService(chef_repository, redis_repository)


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
    redis_repository: RedisRepository = Depends(get_redis_repository),
    image_storage: IStorage = Depends(get_storage_service),
) -> RecipeService:
    return RecipeService(repository, redis_repository, image_storage=image_storage)


ChefServiceDep = Annotated[ChefService, Depends(get_chef_service)]

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

CurrentChef = Annotated[dict, Depends(get_current_chef)]

AuthRequestForm = Annotated[OAuth2PasswordRequestForm, Depends()]

RecipeServiceDep = Annotated[RecipeService, Depends(get_recipe_service)]

RedisCache = Annotated[RedisRepository, Depends(get_redis_repository)]
