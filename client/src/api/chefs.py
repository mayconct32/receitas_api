import requests
from requests import RequestException


URL = "http://127.0.0.1:8000/v1/chefs"


def _handle_request_error(error: RequestException):
    if error.response is not None:
        try:
            return error.response.json()
        except ValueError:
            return {"error": error.response.text}
    return {"error": str(error)}


def post_chef(chef_name, email, password):
    try:
        response = requests.post(
            URL,
            json={
                "chef_name": chef_name,
                "email": email,
                "password": password
            }
        )
        response.raise_for_status()
        return {"data": response.json()}
    except RequestException as e:
        return _handle_request_error(e)


def get_chefs(offset, limit):
    try:
        response = requests.get(
            f"{URL}?offset={offset}&limit={limit}"
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def get_chef(chef_id):
    try:
        response = requests.get(
            f"{URL}/{chef_id}",
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def get_myself(token):
    try:
        response = requests.get(
            f"{URL}/me",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def delete_chef(chef_id, token):
    try:
        response = requests.delete(
            f"{URL}/{chef_id}",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def put_chef(chef_name, email, password, chef_id, token):
    try:
        response = requests.put(
            f"{URL}/{chef_id}",
            json={
                "chef_name": chef_name,
                "email": email,
                "password": password
            },
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return _handle_request_error(e)


def auth_chef(email, password):
    try:
        response = requests.post(
            f"{URL}/auth",
            data={
                "username": email,
                "password": password
            }
        )
        response.raise_for_status()
        return {"data": response.json()}
    except RequestException as e:
        return _handle_request_error(e)
