import os
from datetime import datetime, timedelta, timezone
from http import HTTPStatus

from jwt import InvalidTokenError, decode, encode

from ..exceptions import AuthenticationError, CredentialsError
from ..interfaces.repository import IChefRepository
from ..models.auth import FormData
from ..utils import verify_password


class AuthService:
    def __init__(self, chef_repository: IChefRepository) -> None:
        self.chef_repository = chef_repository

    async def check_authentication(self, form_data: FormData):
        chef = await self.chef_repository.get_by_email(email=form_data.username)
        if not chef or not verify_password(form_data.password, chef["password_hash"]):
            raise AuthenticationError(
                message="Incorrect username or password!",
                status_code=HTTPStatus.FORBIDDEN,
            )
        return chef

    async def create_access_token(self, email: str, chef_id: str):
        to_encode = {"sub": email, "chef_id": chef_id}
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
            chef_id = payload.get("chef_id")
            if chef_id is None:
                raise credentials_exception
        except InvalidTokenError:
            raise credentials_exception

        chef = await self.chef_repository.get(id=chef_id)
        if not chef:
            raise credentials_exception
        return chef