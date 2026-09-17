import os
from collections.abc import Generator

import mysql.connector
import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from redis import Redis
from testcontainers.community.mongodb import MongoDbContainer
from testcontainers.community.mysql import MySqlContainer
from testcontainers.community.redis import RedisContainer

from src import dependencies as deps
from src.main import app
from src.rate_limiter import limiter


os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_USER", "test")
os.environ.setdefault("MYSQL_PASSWORD", "test")
os.environ.setdefault("MYSQL_DATABASE", "test")
os.environ.setdefault("MYSQL_POOL_NAME", "test_pool")
os.environ.setdefault("MYSQL_POOL_SIZE", "5")
os.environ.setdefault("MONGO_HOST", "localhost")
os.environ.setdefault("MONGO_INITDB_ROOT_USERNAME", "root")
os.environ.setdefault("MONGO_INITDB_ROOT_PASSWORD", "root")
os.environ.setdefault("MONGO_INITDB_DATABASE", "recipes")
os.environ.setdefault("MONGO_MIN_POOL_SIZE", "1")
os.environ.setdefault("MONGO_MAX_POOL_SIZE", "5")
os.environ.setdefault("PORT_MONGO", "27017")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_MAX_CONNECTIONS", "10")


class FakeStorage:
    async def upload(self, *, file_name: str, file_bytes: bytes, content_type: str) -> str:
        return f"http://fake-storage.local/recipes/{file_name}"

    async def delete(self, *, file_name: str) -> None:
        return None


@pytest.fixture(scope="session")
def test_containers() -> Generator[None, None, None]:
    monkeypatch = pytest.MonkeyPatch()

    with MySqlContainer("mysql:8.4") as mysql, MongoDbContainer("mongo:7.0") as mongo, RedisContainer("redis:7.2-alpine") as redis:
        monkeypatch.setenv("MYSQL_HOST", mysql.get_container_host_ip())
        monkeypatch.setenv("MYSQL_PORT", str(mysql.get_exposed_port(3306)))
        monkeypatch.setenv("MYSQL_USER", mysql.username)
        monkeypatch.setenv("MYSQL_PASSWORD", mysql.password)
        monkeypatch.setenv("MYSQL_DATABASE", mysql.dbname)
        monkeypatch.setenv("MYSQL_POOL_NAME", "test_pool")
        monkeypatch.setenv("MYSQL_POOL_SIZE", "5")

        monkeypatch.setenv("MONGO_HOST", mongo.get_container_host_ip())
        monkeypatch.setenv("PORT_MONGO", str(mongo.get_exposed_port(27017)))
        monkeypatch.setenv("MONGO_INITDB_ROOT_USERNAME", mongo.username)
        monkeypatch.setenv("MONGO_INITDB_ROOT_PASSWORD", mongo.password)
        monkeypatch.setenv("MONGO_INITDB_DATABASE", "recipes")
        monkeypatch.setenv("MONGO_MIN_POOL_SIZE", "1")
        monkeypatch.setenv("MONGO_MAX_POOL_SIZE", "5")

        monkeypatch.setenv("REDIS_HOST", redis.get_container_host_ip())
        monkeypatch.setenv("REDIS_PORT", str(redis.get_exposed_port(6379)))
        monkeypatch.setenv("REDIS_DB", "0")
        monkeypatch.setenv("REDIS_MAX_CONNECTIONS", "10")

        yield

    monkeypatch.undo()


@pytest.fixture(autouse=True)
def reset_state(test_containers):
    limiter.enabled = False

    mysql_conn = mysql.connector.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
    )
    with mysql_conn.cursor() as cursor:
        with open("src/chef_table.sql", encoding="utf-8") as schema_file:
            cursor.execute(schema_file.read())
        cursor.execute("DELETE FROM chef")
    mysql_conn.commit()
    mysql_conn.close()

    mongo_client = MongoClient(
        f"mongodb://{os.environ['MONGO_INITDB_ROOT_USERNAME']}:{os.environ['MONGO_INITDB_ROOT_PASSWORD']}@{os.environ['MONGO_HOST']}:{os.environ['PORT_MONGO']}/?authSource=admin"
    )
    mongo_client[os.environ["MONGO_INITDB_DATABASE"]]["Recipe"].delete_many({})
    mongo_client.close()

    redis_client = Redis(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ["REDIS_PORT"]),
        db=int(os.environ["REDIS_DB"]),
        decode_responses=True,
    )
    redis_client.flushdb()

    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_storage_service] = lambda: FakeStorage()

    yield

    app.dependency_overrides.clear()
    limiter.enabled = True


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
