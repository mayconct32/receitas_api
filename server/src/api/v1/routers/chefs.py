from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Request, HTTPException

from ....dependencies import (
    AuthRequestForm,
    AuthServiceDep,
    ChefServiceDep,
    CurrentChef,
)
from ....models.auth import Token
from ....models.chef import Chef, ResponseChef, UpdateChef
from ....rate_limiter import limiter
from ....exceptions import *


app = APIRouter(tags=["chefs"], prefix="/v1/chefs")


@app.get("/me", status_code=HTTPStatus.OK,response_model=ResponseChef)
@limiter.limit("30/minute")
async def get_myself(request: Request, current_chef: CurrentChef):
    return current_chef


@app.get("/", status_code=HTTPStatus.OK, response_model=List[ResponseChef])
@limiter.limit("30/minute")
async def get_chefs(
    request: Request, offset: int, limit: int, chef_service: ChefServiceDep
):
    return await chef_service.get_all_the_chefs(
        offset=offset, 
        limit=limit
    )


@app.get(
    "/{chef_id}",
    status_code=HTTPStatus.OK,
    response_model=ResponseChef | None,
)
@limiter.limit("30/minute")
async def get_chef(
    request: Request, chef_id: str, chef_service: ChefServiceDep
):
    return await chef_service.get_chef(chef_id)


@app.post("/", status_code=HTTPStatus.CREATED, response_model=ResponseChef)
@limiter.limit("15/minute")
async def add_chef(
    request: Request, chef: Chef, chef_service: ChefServiceDep
):
    return await chef_service.add_chef(chef)


@app.post("/auth", status_code=HTTPStatus.CREATED, response_model=Token)
@limiter.limit("20/minute")
async def auth_chef(
    request: Request, form_data: AuthRequestForm, auth_service: AuthServiceDep
):
    chef = await auth_service.check_authentication(form_data)
    token = await auth_service.create_access_token(form_data.username, chef_id=chef["chef_id"])
    return {"access_token": token, "token_type": "bearer"}


@app.delete("/{chef_id}", status_code=HTTPStatus.OK)
@limiter.limit("15/minute")
async def delete_chef(
    request: Request,
    chef_id: str,
    chef_service: ChefServiceDep,
    current_chef: CurrentChef,
):
    return await chef_service.delete_chef(chef_id, current_chef)
    

@app.put("/{chef_id}", status_code=HTTPStatus.OK, response_model=ResponseChef)
@limiter.limit("15/minute")
async def update_chef(
    request: Request,
    updated_chef: UpdateChef,
    chef_id: str,
    chef_service: ChefServiceDep,
    current_chef: CurrentChef,
):
    return await chef_service.update_chef(updated_chef, chef_id, current_chef)
