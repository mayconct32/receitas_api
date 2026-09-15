from typing import List
from http import HTTPStatus

from fastapi import APIRouter, File, Form, Request, UploadFile, HTTPException

from src.dependencies import CurrentChef, RecipeServiceDep
from src.models.recipe import Recipe, ResponseRecipe
from src.rate_limiter import limiter


app = APIRouter(tags=["recipes"], prefix="/v1/recipes")


@app.get("/", response_model=List[ResponseRecipe])
@limiter.limit("5/minute")
async def get_recipes(
    request: Request,
    recipe_service: RecipeServiceDep,
    offset: int,
    limit: int,
):
    return await recipe_service.get_recipes(offset, limit)


@app.get("/my_recipes", response_model=List[ResponseRecipe])
@limiter.limit("5/minute")
async def get_my_recipes(
    request: Request,
    recipe_service: RecipeServiceDep,
    current_chef: CurrentChef,
    offset: int,
    limit: int,
):
    return await recipe_service.get_my_recipes(
        current_chef["chef_id"], offset, limit
    )


@app.get("/{recipe_id}", response_model=ResponseRecipe)
@limiter.limit("5/minute")
async def get_recipe(
    request: Request, recipe_service: RecipeServiceDep, recipe_id: str
):
    return await recipe_service.get_recipe(recipe_id)


@app.post("/", response_model=ResponseRecipe)
@limiter.limit("3/minute")
async def add_recipe(
    request: Request,
    current_chef: CurrentChef,
    recipe_service: RecipeServiceDep,
    recipe_data: str = Form(...),
    image: UploadFile | None = File(default=None),
):
    try:
        recipe = Recipe.from_json(recipe_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_CONTENT, 
            detail=str(exc)
        ) from exc

    return await recipe_service.add_recipe(
        recipe, current_chef["chef_id"], image=image
    )


@app.delete("/{recipe_id}")
@limiter.limit("3/minute")
async def delete_recipe(
    request: Request,
    recipe_service: RecipeServiceDep,
    current_chef: CurrentChef,
    recipe_id: str,
):
    return await recipe_service.delete_recipe(
        current_chef["chef_id"], recipe_id
    )


@app.put("/{recipe_id}")
@limiter.limit("3/minute")
async def update_recipe(
    request: Request,
    recipe_service: RecipeServiceDep,
    current_chef: CurrentChef,
    recipe_id: str,
    recipe_data: str = Form(...),
    image: UploadFile | None = File(default=None),
):
    try:
        recipe = Recipe.from_json(recipe_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_CONTENT, 
            detail=str(exc)
        ) from exc

    return await recipe_service.update_recipe(
        current_chef["chef_id"], recipe_id, recipe, image=image
    )

