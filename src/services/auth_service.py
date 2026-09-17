import os
from datetime import datetime, timedelta, timezone
from http import HTTPStatus

from jwt import InvalidTokenError, decode, encode

from src.interfaces.repository import IChefRepository
from src.repositories.redis_repository import RedisRepository
from src.models.auth import FormData
from src.exceptions import AuthenticationError, CredentialsError
from src.utils import verify_password


class AuthService:
    def __init__(self, chef_repository: IChefRepository, redis_repository: RedisRepository) -> None:
        self.chef_repository = chef_repository
        self.redis_repository = redis_repository

    async def check_authentication(self, form_data: FormData):
        chef = await self.chef_repository.get_by_email(email=form_data.username)
        if not chef or not verify_password(form_data.password, chef["password_hash"]):
            raise AuthenticationError(
                message="Incorrect username or password!",
                status_code=HTTPStatus.FORBIDDEN,
            )

    @staticmethod
    async def create_access_token(form_data: FormData):
        to_encode = {"sub": form_data.username}
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
        )
        to_encode.update({"exp": expire})
        encoded_jwt = encode(
            to_encode,
            os.getenv("SECRET_KEY"),
            algorithm=os.getenv("ALGORITHM"),
        )
        return encoded_jwt

    async def decode_token(self, token: str) -> dict:
        credentials_exception = CredentialsError(
            message = "Could not validate credentials",
            status_code = HTTPStatus.UNAUTHORIZED
        )
        try:
            payload: dict = decode(
                token,
                os.getenv("SECRET_KEY"),
                algorithms=[os.getenv("ALGORITHM")],
            )
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
        except InvalidTokenError:
            raise credentials_exception
        cache = await self.redis_repository.get(f"chef:{email}")
        if cache:
            return cache
        else:
            chef = await self.chef_repository.get_by_email(email=email)
            if not chef:
                raise credentials_exception
            await self.redis_repository.insert(f"chef:{email}",chef)
            return chef