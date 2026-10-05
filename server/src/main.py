import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.routers.chefs import app as chefs
from .api.v1.routers.recipes import app as recipes
from .rate_limiter import limiter
from .exceptions import DomainException


app = FastAPI()


@app.get("/")
@limiter.limit("30/minute")
def hello_world(request: Request):
    return {"message": "hello world!"}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(DomainException)
def validation_Exception_handler(request, exc: DomainException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chefs)
app.include_router(recipes)

# uvicorn src.main:app --reload --host 0.0.0.0
