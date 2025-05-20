import os
from datetime import datetime
from os import getenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.exceptions import DBConnectionError
from src.routes.web import web
from src.routes.api import api
from src.models import AllianceModel, MinisterModel, MinisterTypeModel, StateModel

app = FastAPI()

origins = [
    "http://localhost:8000",
    "https://wosplanning.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)

app.mount("/static", StaticFiles(directory="/frontend/static"), name="static")


@app.on_event("startup")
async def startup_event():
    await Tortoise.init(
        db_url=getenv("DATABASE_URL"),
        modules={
            "models": [
                "src.models",
                "aerich.models",
            ],
        },
        use_tz=False,
        timezone="UTC",
    )

    await Tortoise.generate_schemas()

    tags = ["MAD", "DUF", "PAD", "MVP", "BTA", "SNY", "PaP"]
    alliances = []

    for tag in tags:
        alliance, _ = await AllianceModel.get_or_create(tag=tag)

        alliances.append(alliance)

    state, _ = await StateModel.get_or_create(id=750)

    await state.alliances.add(*alliances)

    vp_types = ["Construction", "Research"]
    edu_types = ["Training"]

    vp_type_objs = []

    for t in vp_types:
        obj, _ = await MinisterTypeModel.get_or_create(name=t)

        vp_type_objs.append(obj)

    edu_type_objs = []

    for t in edu_types:
        obj, _ = await MinisterTypeModel.get_or_create(name=t)

        edu_type_objs.append(obj)

    vp, _ = await MinisterModel.get_or_create(name="Vice President")
    edu, _ = await MinisterModel.get_or_create(name="Education")

    await vp.types.add(*vp_type_objs)
    await edu.types.add(*edu_type_objs)


@app.on_event("shutdown")
async def shutdown_event():
    await Tortoise.close_connections()


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    response = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    try:
        await Tortoise.get_connection("default").execute_query("SELECT 1")

        response["services"]["database"] = "healthy"
    except DBConnectionError:
        response["services"]["database"] = "unhealthy"
        response["status"] = "degraded"

    if response["status"] != "healthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response
        )

    return response


@app.exception_handler(HTTPException)
async def error_handler(_: Request, error: HTTPException):
    return JSONResponse(
        status_code=error.status_code,
        content={
            "status": "error",
            "code": error.status_code,
            "message": error.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Validation error",
            "errors": exc.errors(),
        },
    )


app.include_router(web)
app.include_router(api)

