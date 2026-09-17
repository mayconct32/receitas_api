import json
from http import HTTPStatus
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from tests.helpers import (
    auth_headers,
    create_authenticated_chef,
    create_chef,
    create_recipe,
    recipe_payload,
    unique_email,
)


class TestRecipeEndpoints:
    def test_add_recipe_with_image(self, client: TestClient):
        email = unique_email("chef-recipe")
        create_chef(client, email=email)
        headers = auth_headers(client, email=email)

        response = client.post(
            "/v1/recipes/",
            data={
                "recipe_data": json.dumps(recipe_payload(name="Homemade bread")),
            },
            files={
                "image": (
                    "bread.jpg",
                    BytesIO(b"fake-image"),
                    "image/jpeg",
                )
            },
            headers=headers,
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["recipe_name"] == "Homemade bread"
        assert response.json()["image_url"].startswith(
            "http://fake-storage.local/recipes/"
        )

    def test_get_recipes_lists_all(self, client: TestClient):
        email = unique_email("chef-recipes-list")
        create_chef(client, email=email)
        headers = auth_headers(client, email=email)
        create_recipe(client, headers, name="Risotto")

        response = client.get("/v1/recipes/?offset=0&limit=10")

        assert response.status_code == HTTPStatus.OK
        assert any(item["recipe_name"] == "Risotto" for item in response.json())

    def test_get_recipes_returns_not_found_when_empty(self, client: TestClient):
        response = client.get("/v1/recipes/?offset=0&limit=10")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["detail"] == "recipes not found"

    def test_get_my_recipes_returns_only_owner_recipes(self, client: TestClient):
        email = unique_email("chef-my-recipes")
        _, headers = create_authenticated_chef(client, email=email)
        created = create_recipe(client, headers, name="Risotto")

        response = client.get(
            "/v1/recipes/my_recipes?offset=0&limit=10",
            headers=headers,
        )

        assert response.status_code == HTTPStatus.OK
        assert any(item["recipe_id"] == created["recipe_id"] for item in response.json())

    def test_get_my_recipes_returns_not_found_when_empty(self, client: TestClient):
        email = unique_email("chef-my-recipes-empty")
        _, headers = create_authenticated_chef(client, email=email)

        response = client.get(
            "/v1/recipes/my_recipes?offset=0&limit=10",
            headers=headers,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["detail"] == "recipes not found"

    def test_create_recipe_without_image_succeeds(self, client: TestClient):
        email = unique_email("chef-recipe-no-image")
        _, headers = create_authenticated_chef(client, email=email)

        response = client.post(
            "/v1/recipes/",
            data={
                "recipe_data": json.dumps(recipe_payload(name="Pie without image")),
            },
            headers=headers,
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["recipe_name"] == "Pie without image"

    def test_create_recipe_requires_authentication(self, client: TestClient):
        response = client.post(
            "/v1/recipes/",
            data={
                "recipe_data": json.dumps(recipe_payload(name="No authentication")),
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert "Not authenticated" in response.json()["detail"]

    def test_get_recipe_by_id_returns_record(self, client: TestClient):
        email = unique_email("chef-get-recipe")
        _, headers = create_authenticated_chef(client, email=email)
        created = create_recipe(client, headers, name="Cake")

        response = client.get(f"/v1/recipes/{created['recipe_id']}")

        assert response.status_code == HTTPStatus.OK
        assert response.json()["recipe_id"] == created["recipe_id"]

    @pytest.mark.parametrize(
        "raw_payload",
        [
            "{not valid json}",
            "[]",
            "null",
        ],
    )
    def test_invalid_recipe_payload_returns_422(
        self,
        client: TestClient,
        raw_payload: str,
    ):
        email = unique_email("chef-invalid-recipe")
        _, headers = create_authenticated_chef(client, email=email)

        response = client.post(
            "/v1/recipes/",
            data={"recipe_data": raw_payload},
            headers=headers,
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
        assert "recipe_data" in response.json()["detail"]

    def test_recipe_not_found_returns_404(self, client: TestClient):
        email = unique_email("chef-missing-recipe")
        _, headers = create_authenticated_chef(client, email=email)

        response = client.get("/v1/recipes/does-not-exist", headers=headers)

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["detail"] == "recipe not found"

    def test_update_recipe_returns_updated_values(self, client: TestClient):
        email = unique_email("chef-update-recipe")
        _, headers = create_authenticated_chef(client, email=email)
        created = create_recipe(client, headers, name="Cake")

        response = client.put(
            f"/v1/recipes/{created['recipe_id']}",
            headers=headers,
            data={
                "recipe_data": json.dumps(
                    recipe_payload(name="Carrot cake")
                ),
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["recipe_name"] == "Carrot cake"

    def test_update_recipe_without_image_keeps_existing_image(self, client: TestClient):
        email = unique_email("chef-update-recipe-no-image")
        _, headers = create_authenticated_chef(client, email=email)
        created = create_recipe(client, headers, name="Cake with frosting")

        response = client.put(
            f"/v1/recipes/{created['recipe_id']}",
            headers=headers,
            data={
                "recipe_data": json.dumps(
                    recipe_payload(name="Updated cake with frosting")
                ),
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["recipe_name"] == "Updated cake with frosting"
        assert response.json()["image_url"] == created["image_url"]

    def test_delete_recipe_removes_recipe(self, client: TestClient):
        email = unique_email("chef-delete-recipe")
        _, headers = create_authenticated_chef(client, email=email)
        created = create_recipe(client, headers, name="Pie")

        response = client.delete(
            f"/v1/recipes/{created['recipe_id']}",
            headers=headers,
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["message"] == "Recipe successfully excluded"

    def test_update_recipe_requires_owner(self, client: TestClient):
        owner_email = unique_email("chef-owner-recipe-update")
        other_email = unique_email("chef-other-recipe-update")
        create_chef(client, email=owner_email)
        create_chef(client, email=other_email)
        owner_headers = auth_headers(client, email=owner_email)
        other_headers = auth_headers(client, email=other_email)
        created = create_recipe(client, owner_headers, name="Pizza")

        response = client.put(
            f"/v1/recipes/{created['recipe_id']}",
            headers=other_headers,
            data={
                "recipe_data": json.dumps(
                    recipe_payload(name="Pepperoni pizza")
                ),
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json()["detail"] == "unauthorized request"

    def test_recipe_delete_requires_owner(self, client: TestClient):
        owner_email = unique_email("chef-owner-recipe")
        other_email = unique_email("chef-other-recipe")
        create_chef(client, email=owner_email)
        create_chef(client, email=other_email)
        owner_headers = auth_headers(client, email=owner_email)
        other_headers = auth_headers(client, email=other_email)
        created = create_recipe(client, owner_headers, name="Pizza")

        response = client.delete(
            f"/v1/recipes/{created['recipe_id']}",
            headers=other_headers,
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json()["detail"] == "unauthorized request"
