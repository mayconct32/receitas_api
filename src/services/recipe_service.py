import inspect
from http import HTTPStatus
from uuid import uuid4

from fastapi import UploadFile

from src.exceptions import AuthorizationError, RecipeErrorNotFound
from src.interfaces.repository import IRecipeRepository
from src.interfaces.storage import IStorage
from src.models.recipe import Recipe
from src.repositories.redis_repository import RedisRepository


class RecipeService:
    def __init__(
        self,
        recipe_repository: IRecipeRepository,
        redis_repository: RedisRepository,
        image_storage: IStorage | None = None,
    ) -> None:
        self.recipe_repository = recipe_repository
        self.redis_repository = redis_repository
        self.image_storage = image_storage

    async def get_recipes(self, offset: int, limit: int):
        cache = await self.redis_repository.get(f"recipes:{offset}&{limit}")
        if cache:
            return cache
        recipes = await self.recipe_repository.get_all(offset, limit)
        if not recipes:
            raise RecipeErrorNotFound(
                message="recipes not found",
                status_code=HTTPStatus.NOT_FOUND,
            )
        await self.redis_repository.insert(
            f"recipes:{offset}&{limit}", recipes
        )
        return recipes

    async def get_recipe(self, id: str):
        cache = await self.redis_repository.get(f"recipe:{id}")
        if cache:
            return cache
        recipe = await self.recipe_repository.get(id)
        if not recipe:
            raise RecipeErrorNotFound(
                message="recipe not found",
                status_code=HTTPStatus.NOT_FOUND,
            )
        await self.redis_repository.insert(f"recipe:{id}", recipe)
        return recipe

    async def get_my_recipes(
        self, current_chef_id: str, offset: int, limit: int
    ):
        cache = await self.redis_repository.get(
            f"my_recipes:{current_chef_id}:{offset}&{limit}"
        )
        if cache:
            return cache
        recipes = await self.recipe_repository.get_recipes_from_chef(
            current_chef_id, offset, limit
        )
        if not recipes:
            raise RecipeErrorNotFound(
                message="recipes not found",
                status_code=HTTPStatus.NOT_FOUND,
            )
        await self.redis_repository.insert(
            f"my_recipes:{current_chef_id}:{offset}&{limit}", recipes
        )
        return recipes

    @staticmethod
    def _extract_file_name(image_url: str | None) -> str | None:
        if not image_url:
            return None
        return image_url.split("/")[-1]

    async def _upload_recipe_image(
        self, image: UploadFile | None
    ) -> str | None:
        if image is None or not getattr(image, "filename", None):
            return None

        if self.image_storage is None:
            raise ValueError("Image storage not configured")

        seek = getattr(image, "seek", None)
        if seek is not None:
            if inspect.iscoroutinefunction(seek):
                await seek(0)
            else:
                seek(0)

        read = getattr(image, "read")
        if inspect.iscoroutinefunction(read):
            file_bytes = await read()
        else:
            file_bytes = read()

        file_name = f"{uuid4()}-{image.filename}"
        content_type = (
            getattr(image, "content_type", None)
            or "application/octet-stream"
        )

        image_url = await self.image_storage.upload(
            file_name=file_name,
            file_bytes=file_bytes,
            content_type=content_type,
        )
        return image_url

    async def add_recipe(
        self,
        recipe: Recipe,
        current_chef_id: str,
        image: UploadFile | None = None,
    ):
        image_url = await self._upload_recipe_image(image)
        if image_url:
            recipe.image_url = image_url

        db_recipe = await self.recipe_repository.add(recipe, current_chef_id)
        await self.redis_repository.delete(
            f"my_recipes:{current_chef_id}:*",
            "recipes:*",
        )
        return db_recipe

    async def verify_authorization(
        self, current_chef_id: str, recipe_id: str
    ):
        recipe = await self.recipe_repository.get(recipe_id)
        if not recipe:
            raise RecipeErrorNotFound(
                message="recipe not found",
                status_code=HTTPStatus.NOT_FOUND,
            )
        if recipe["chef_id"] != current_chef_id:
            raise AuthorizationError(
                message="unauthorized request",
                status_code=HTTPStatus.UNAUTHORIZED,
            )

    async def delete_recipe(self, current_chef_id: str, recipe_id: str):
        await self.verify_authorization(current_chef_id, recipe_id)
        current_recipe = await self.recipe_repository.get(recipe_id)
        if current_recipe and current_recipe.get("image_url"):
            file_name = self._extract_file_name(current_recipe["image_url"])
            if file_name and self.image_storage is not None:
                await self.image_storage.delete(file_name=file_name)

        await self.recipe_repository.delete(recipe_id)
        await self.redis_repository.delete(
            f"my_recipes:{current_chef_id}:*",
            "recipes:*",
            f"recipe:{recipe_id}",
        )
        return {"message": "Recipe successfully excluded"}

    async def update_recipe(
        self,
        current_chef_id: str,
        recipe_id: str,
        recipe: Recipe,
        image: UploadFile | None = None,
    ):
        await self.verify_authorization(current_chef_id, recipe_id)

        current_recipe = await self.recipe_repository.get(recipe_id)
        new_image_url = await self._upload_recipe_image(image)

        if new_image_url:
            if current_recipe and current_recipe.get("image_url"):
                old_file_name = self._extract_file_name(current_recipe["image_url"])
                if old_file_name and self.image_storage is not None:
                    await self.image_storage.delete(file_name=old_file_name)
            recipe.image_url = new_image_url
        elif current_recipe and current_recipe.get("image_url"):
            recipe.image_url = current_recipe["image_url"]

        await self.recipe_repository.update(recipe_id, recipe)
        await self.redis_repository.delete(
            f"my_recipes:{current_chef_id}:*",
            "recipes:*",
            f"recipe:{recipe_id}",
        )
        return recipe
