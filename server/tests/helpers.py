import json
from http import HTTPStatus
from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient


def unique_email(prefix: str = "chef") -> str:
    return f"{prefix}-{uuid4().hex[:8]}@email.com"


def build_chef_payload(
    *,
    chef_name: str | None = None,
    email: str | None = None,
    password: str = "password123",
) -> dict:
    return {
        "chef_name": chef_name or f"Alice-{uuid4().hex[:8]}",
        "email": email or unique_email("chef"),
        "password": password,
    }


def create_chef(
    client: TestClient,
    *,
    email: str | None = None,
    password: str = "password123",
    chef_name: str | None = None,
) -> dict:
    payload = build_chef_payload(
        chef_name=chef_name,
        email=email,
        password=password,
    )
    response = client.post(
        "/v1/chefs/",
        json=payload,
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    return response.json()


def auth_headers(client: TestClient, *, email: str, password: str = "password123") -> dict[str, str]:
    response = client.post(
        "/v1/chefs/auth",
        data={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    token = response.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
    }


def create_authenticated_chef(
    client: TestClient,
    *,
    email: str | None = None,
    password: str = "password123",
    chef_name: str | None = None,
) -> tuple[dict, dict[str, str]]:
    created = create_chef(
        client,
        email=email,
        password=password,
        chef_name=chef_name,
    )
    headers = auth_headers(client, email=created["email"], password=password)
    return created, headers


def build_recipe_payload(
    *,
    name: str = "Homemade bread",
    description: str = "Simple recipe",
    prep_time: str = "00:45:00",
    instructions: list[dict] | None = None,
    ingredients: list[dict] | None = None,
) -> dict:
    return {
        "recipe_name": name,
        "description": description,
        "prep_time": prep_time,
        "instructions": instructions or [
            {
                "step_number": 1,
                "description": "Mix the ingredients",
            }
        ],
        "ingredients": ingredients or [
            {
                "ingredient_name": "flour",
                "quantity": "500g",
            }
        ],
    }


def recipe_payload(*, name: str = "Homemade bread") -> dict:
    return build_recipe_payload(name=name)


def create_recipe(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str = "Homemade bread",
    image_name: str = "bread.jpg",
) -> dict:
    response = client.post(
        "/v1/recipes/",
        data={
            "recipe_data": json.dumps(recipe_payload(name=name)),
        },
        files={
            "image": (
                image_name,
                BytesIO(b"fake-image"),
                "image/jpeg",
            )
        },
        headers=headers,
    )
    assert response.status_code == HTTPStatus.OK
    return response.json()


def create_authenticated_recipe(
    client: TestClient,
    *,
    email: str | None = None,
    name: str = "Homemade bread",
    image_name: str = "bread.jpg",
    password: str = "password123",
) -> tuple[dict, dict, dict[str, str]]:
    chef_email = email or unique_email("chef-recipe")
    created_chef, headers = create_authenticated_chef(
        client,
        email=chef_email,
        password=password,
    )
    created_recipe = create_recipe(
        client,
        headers,
        name=name,
        image_name=image_name,
    )
    return created_chef, created_recipe, headers


