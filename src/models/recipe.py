import json
from datetime import datetime
from typing import List

from pydantic import BaseModel, ValidationError


class Instruction(BaseModel):
    step_number: int
    description: str


class Ingredient(BaseModel):
    ingredient_name: str
    quantity: str


class Recipe(BaseModel):
    recipe_name: str
    description: str
    prep_time: str  # "11:12:00"
    instructions: List[Instruction]
    ingredients: List[Ingredient]
    image_url: str | None = None

    @classmethod
    def from_json(cls, raw_recipe_data: str | None) -> "Recipe":
        if raw_recipe_data is None or raw_recipe_data == "":
            raise ValueError(
                "recipe_data is required in multipart form data"
            )

        try:
            payload = json.loads(raw_recipe_data)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "recipe_data must be a valid JSON object"
            ) from exc

        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(
                "recipe_data does not match the Recipe schema"
            ) from exc


class DBRecipe(BaseModel):
    recipe_id: str
    chef_id: str
    posted_at: datetime
    updated_at: datetime


class ResponseRecipe(Recipe, DBRecipe): ...

