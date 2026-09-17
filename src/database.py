import os

from dotenv import load_dotenv
from mysql.connector import pooling
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from redis import asyncio

from src.interfaces.connection_db import IDBConnection


load_dotenv(override=True)


class MysqlDBConnection(IDBConnection):
    def __init__(self):
        self._host = os.getenv("MYSQL_HOST")
        self._port = int(os.getenv("MYSQL_PORT", "3306"))
        self._user = os.getenv("MYSQL_USER")
        self._password = os.getenv("MYSQL_PASSWORD")
        self._database = os.getenv("MYSQL_DATABASE")
        self._pool_name = os.getenv("MYSQL_POOL_NAME")
        self._pool_size = int(os.getenv("MYSQL_POOL_SIZE"))
        self._pool = pooling.MySQLConnectionPool(
            pool_name=self._pool_name,
            pool_size=self._pool_size,
            pool_reset_session=True,
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database,
        )

    def _connection(self):
        return self._pool.get_connection()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        return None

    async def execute(self, command, data=None):
        connection = self._connection()
        try:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(command, data)
                command_name = str(command).strip().split(maxsplit=1)[0].upper()
                if command_name in {"UPDATE", "INSERT", "DELETE"}:
                    connection.commit()
                response = cursor.fetchall() if cursor.with_rows else []
            finally:
                cursor.close()
            return response
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


class MongoDBConnection(IDBConnection):
    def __init__(self) -> None:
        self.__connection_string = (
            "mongodb://{}:{}@{}:{}/?authSource=admin".format(
                os.getenv("MONGO_INITDB_ROOT_USERNAME"),
                os.getenv("MONGO_INITDB_ROOT_PASSWORD"),
                os.getenv("MONGO_HOST"),
                os.getenv("PORT_MONGO")
            )
        )
        self.__database_name = os.getenv("MONGO_INITDB_DATABASE")
        self.__min_pool_size = int(os.getenv("MONGO_MIN_POOL_SIZE"))
        self.__max_pool_size = int(os.getenv("MONGO_MAX_POOL_SIZE"))
        self.__client = None
        self.__db_connection = None

    def __connection_to_db(self) -> None:
        if self.__client is not None:
            return
        self.__client = AsyncMongoClient(
            self.__connection_string,
            minPoolSize=self.__min_pool_size,
            maxPoolSize=self.__max_pool_size,
        )
        self.__db_connection = self.__client[self.__database_name]

    def __get_db_connection(self) -> AsyncDatabase:
        if self.__db_connection is None:
            self.__connection_to_db()
        return self.__db_connection

    async def execute(self, command, data=None):
        if not isinstance(command, dict):
            raise TypeError("MongoDBConnection.execute expects a BSON-like command dictionary")

        payload = dict(command)

        if data is not None:
            if not isinstance(data, dict):
                raise TypeError("MongoDBConnection.execute data must be a dictionary")
            payload.update(data)

        db = self.__get_db_connection()
        return await db.command(payload)

    async def close(self):
        if self.__client is not None:
            await self.__client.close()
            self.__client = None
            self.__db_connection = None

    async def __aenter__(self):
        self.__connection_to_db()
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        await self.close()


# In-memory database used for caching.
class RedisConnection(IDBConnection):
    def __init__(self) -> None:
        self.host = os.getenv("REDIS_HOST")
        self.port = os.getenv("REDIS_PORT")
        self.db = os.getenv("REDIS_DB")
        self.max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS"))
        self.__connection = None

    def __connect(self) -> None:
        self.__connection = asyncio.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=True,
            max_connections=self.max_connections,
        )

    def __get_connection(self) -> asyncio.Redis:
        if self.__connection is None:
            self.__connect()
        return self.__connection

    async def execute(self, command, data=None):
        if not isinstance(command, dict):
            raise TypeError("RedisConnection.execute expects a raw command dictionary")

        payload = dict(command)
        if data is not None:
            if not isinstance(data, dict):
                raise TypeError("RedisConnection.execute data must be a dictionary")
            payload.update(data)

        command_name = payload.pop("command", payload.pop("operation", None))
        if command_name is None:
            raise ValueError("Redis command must define 'command' or 'operation'")

        command_name = str(command_name).upper()

        if command_name == "DELETE":
            command_name = "DEL"

        if command_name in {"SCAN", "SCAN_ITER"}:
            pattern = payload.get("pattern") or payload.get("match")
            return self.__get_connection().scan_iter(match=pattern)

        args = []
        for field in ("key", "value", "pattern", "match"):
            if field in payload:
                args.append(payload.pop(field))

        args.extend(payload.values())

        return await self.__get_connection().execute_command(command_name, *args)

    async def close(self):
        if self.__connection is not None:
            await self.__connection.aclose()
            self.__connection = None

    async def __aenter__(self):
        self.__connect()
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        await self.close()