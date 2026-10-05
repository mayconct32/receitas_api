from http import HTTPStatus

from fastapi import UploadFile

from ..exceptions import AuthorizationError, RecipeErrorNotFound
from ..interfaces.repository import IRecipeRepository
from ..models.recipe import Recipe
from .cache_service import CacheService
from .storage_service import RecipeImageService


class RecipeService:
    def __init__(
        self,
        recipe_repository: IRecipeRepository,
        cache_service: CacheService,
        image_handler: RecipeImageService | None = None,
    ) -> None:
        self.recipe_repository = recipe_repository
        self.cache_service = cache_service
        self.image_handler = image_handler

    async def _upload_recipe_image(self, image: UploadFile | None) -> str | None:
        if self.image_handler is None or image is None:
            return None
        return await self.image_handler.upload(image)

    async def _get_recipe_or_404(self, recipe_id: str):
        recipe = await self.recipe_repository.get(recipe_id)
        if not recipe:
            raise RecipeErrorNotFound(
                message="recipe not found",
                status_code=HTTPStatus.NOT_FOUND,
            )
        return recipe

    async def _authorize_recipe_owner(self, current_chef_id: str, recipe_id: str):
        recipe = await self._get_recipe_or_404(recipe_id)
        if recipe["chef_id"] != current_chef_id:
            raise AuthorizationError(
                message="unauthorized request",
                status_code=HTTPStatus.UNAUTHORIZED,
            )

    async def _replace_recipe_image(self, recipe_id: str, recipe: Recipe, image: UploadFile | None):
        current_recipe = await self._get_recipe_or_404(recipe_id)
        recipe_payload = recipe.model_dump()

        if image is not None:
            new_image_url = await self._upload_recipe_image(image)
            if new_image_url:
                if current_recipe.get("image_url") and self.image_handler is not None:
                    await self.image_handler.delete(current_recipe["image_url"])
                recipe_payload["image_url"] = new_image_url
            elif current_recipe.get("image_url"):
                recipe_payload["image_url"] = current_recipe["image_url"]
        elif current_recipe.get("image_url"):
            recipe_payload["image_url"] = current_recipe["image_url"]

        return recipe_payload

    async def _invalidate_recipe_cache(self, current_chef_id: str, recipe_id: str):
        await self.cache_service.delete(
            f"my_recipes:{current_chef_id}:*",
            "recipes:*",
            f"recipe:{recipe_id}",
        )

    async def get_recipes(self, offset: int, limit: int):
        cache_key = f"recipes:{offset}&{limit}"
        cached_recipes = await self.cache_service.get(cache_key)
        if cached_recipes:
            return cached_recipes

        recipes = await self.recipe_repository.get_all(offset, limit)
        if not recipes:
            raise RecipeErrorNotFound(
                message="recipes not found",
                status_code=HTTPStatus.NOT_FOUND,
            )

        await self.cache_service.insert(cache_key, recipes)
        return recipes

    async def get_recipe(self, id: str):
        cache_key = f"recipe:{id}"
        cached_recipe = await self.cache_service.get(cache_key)
        if cached_recipe:
            return cached_recipe

        recipe = await self._get_recipe_or_404(id)
        await self.cache_service.insert(cache_key, recipe)
        return recipe

    async def get_my_recipes(self, current_chef_id: str, offset: int, limit: int):
        cache_key = f"my_recipes:{current_chef_id}:{offset}&{limit}"
        cached_my_recipes = await self.cache_service.get(cache_key)
        if cached_my_recipes:
            return cached_my_recipes

        recipes = await self.recipe_repository.get_recipes_from_chef(
            current_chef_id, offset, limit
        )
        if not recipes:
            raise RecipeErrorNotFound(
                message="recipes not found",
                status_code=HTTPStatus.NOT_FOUND,
            )

        await self.cache_service.insert(cache_key, recipes)
        return recipes

    async def add_recipe(
        self,
        recipe: Recipe,
        current_chef_id: str,
        image: UploadFile | None = None,
    ):
        recipe_payload = recipe.model_dump()
        if image is not None:
            image_url = await self._upload_recipe_image(image)
            if image_url:
                recipe_payload["image_url"] = image_url

        db_recipe = await self.recipe_repository.add(recipe_payload, current_chef_id)
        await self.cache_service.delete(
            f"my_recipes:{current_chef_id}:*",
            "recipes:*",
        )
        return db_recipe

    async def verify_authorization(self, current_chef_id: str, recipe_id: str):
        await self._authorize_recipe_owner(current_chef_id, recipe_id)

    async def delete_recipe(self, current_chef_id: str, recipe_id: str):
        await self._authorize_recipe_owner(current_chef_id, recipe_id)
        current_recipe = await self._get_recipe_or_404(recipe_id)

        if current_recipe.get("image_url") and self.image_handler is not None:
            await self.image_handler.delete(current_recipe["image_url"])

        await self.recipe_repository.delete(recipe_id)
        await self._invalidate_recipe_cache(current_chef_id, recipe_id)
        return {"message": "Recipe successfully excluded"}

    async def update_recipe(
        self,
        current_chef_id: str,
        recipe_id: str,
        recipe: Recipe,
        image: UploadFile | None = None,
    ):
        await self._authorize_recipe_owner(current_chef_id, recipe_id)
        recipe_payload = await self._replace_recipe_image(recipe_id, recipe, image)
        await self.recipe_repository.update(recipe_id, recipe_payload)
        await self._invalidate_recipe_cache(current_chef_id, recipe_id)
        return recipe_payload
