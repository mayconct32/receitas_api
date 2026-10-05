from http import HTTPStatus

from ..exceptions import *
from ..interfaces.repository import IChefRepository
from ..models.chef import Chef, ResponseChef, UpdateChef
from .cache_service import CacheService


class ChefService:
    def __init__(self, chef_repository: IChefRepository, cache_service: CacheService) -> None:
        self.chef_repository = chef_repository
        self.cache_service = cache_service

    async def _verify_credentials(
        self,
        chef_name: str | None = None,
        email: str | None = None,
        current_chef_id: str | None = None,
        current_chef_name: str | None = None,
        current_chef_email: str | None = None,
    ):
        if chef_name is not None and chef_name != current_chef_name:
            conflicting_name = await self.chef_repository.get_by_chef_name(chef_name=chef_name)
            if conflicting_name and conflicting_name["chef_id"] != current_chef_id:
                raise ConflictingNameError(
                    message="This name already exists!",
                    status_code=HTTPStatus.CONFLICT,
                )

        if email is not None and email != current_chef_email:
            conflicting_email = await self.chef_repository.get_by_email(email=email)
            if conflicting_email and conflicting_email["chef_id"] != current_chef_id:
                raise ConflictingEmailError(
                    message="This email already exists!",
                    status_code=HTTPStatus.CONFLICT,
                )

    async def _get_chef_or_404(self, chef_id: str):
        chef = await self.chef_repository.get(id=chef_id)
        if not chef:
            raise ChefErrorNotFound(
                message="Chefs not found!",
                status_code=HTTPStatus.NOT_FOUND,
            )
        return chef

    @staticmethod
    def check_authorization(chef_id, authenticated_chef_id):
        if chef_id != authenticated_chef_id:
            raise AuthorizationError(
                message="unauthorized request",
                status_code=HTTPStatus.UNAUTHORIZED,
            )

    async def get_all_the_chefs(self, offset, limit):
        cache_key = f"chefs:{offset}&{limit}"
        cached_chefs = await self.cache_service.get(cache_key)
        if cached_chefs:
            return cached_chefs

        chefs = await self.chef_repository.get_all(offset, limit)
        if not chefs:
            raise ChefErrorNotFound(
                message="Chefs not found!",
                status_code=HTTPStatus.NOT_FOUND,
            )

        await self.cache_service.insert(cache_key, chefs)
        return chefs

    async def get_chef(self, id: str):
        cache_key = f"chef:{id}"
        cached_chef = await self.cache_service.get(cache_key)
        if cached_chef:
            return cached_chef

        chef = await self._get_chef_or_404(id)
        await self.cache_service.insert(cache_key, chef)
        return chef

    async def add_chef(self, chef: Chef):
        await self._verify_credentials(chef_name=chef.chef_name, email=chef.email)
        await self.chef_repository.add(chef)
        await self.cache_service.delete("chefs:*")
        return await self.chef_repository.get_by_email(email=chef.email)

    async def delete_chef(self, chef_id, current_chef):
        self.check_authorization(chef_id, current_chef["chef_id"])
        await self.chef_repository.delete(current_chef["chef_id"])
        await self.cache_service.delete(
            f"chef:{current_chef['chef_id']}", "chefs:*"
        )
        return {"message": "Chef successfully excluded"}

    async def update_chef(self, updated_chef: UpdateChef, chef_id, current_chef) -> ResponseChef:
        self.check_authorization(chef_id, current_chef["chef_id"])
        await self._verify_credentials(
            updated_chef.chef_name,
            updated_chef.email,
            current_chef_id=current_chef["chef_id"],
            current_chef_name=current_chef.get("chef_name"),
            current_chef_email=current_chef.get("email"),
        )
        await self.chef_repository.update(current_chef["chef_id"], updated_chef)
        await self.cache_service.delete(
            f"chef:{current_chef['chef_id']}", "chefs:*"
        )
        return await self.chef_repository.get(id=current_chef["chef_id"])
