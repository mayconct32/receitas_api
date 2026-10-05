import json

import requests
from requests import RequestException


URL = "http://127.0.0.1:8000/v1/recipes"


def _handle_request_error(error: RequestException):
    if error.response is not None:
        try:
            return error.response.json()
        except ValueError:
            return {"error": error.response.text}
    return {"error": str(error)}


def get_recipes(offset, limit):
    try:
        response = requests.get(f"{URL}/?offset={offset}&limit={limit}")
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def get_my_recipes(offset, limit, token):
    try:
        response = requests.get(
            f"{URL}/my_recipes?offset={offset}&limit={limit}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def get_recipe(recipe_id):
    try:
        response = requests.get(f"{URL}/{recipe_id}")
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def add_recipe(recipe_data, token, image=None):
    try:
        files = None
        payload = {"recipe_data": json.dumps(recipe_data)}

        if image is not None:
            if isinstance(image, tuple):
                files = {"image": image}
            else:
                files = {"image": (image.name, image.getvalue(), image.type)}

        response = requests.post(
            f"{URL}/",
            data=payload,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def delete_recipe(recipe_id, token):
    try:
        response = requests.delete(
            f"{URL}/{recipe_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def update_recipe(recipe_id, recipe_data, token, image=None):
    try:
        files = None
        payload = {"recipe_data": json.dumps(recipe_data)}

        if image is not None:
            if isinstance(image, tuple):
                files = {"image": image}
            else:
                files = {"image": (image.name, image.getvalue(), image.type)}

        response = requests.put(
            f"{URL}/{recipe_id}",
            data=payload,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)
