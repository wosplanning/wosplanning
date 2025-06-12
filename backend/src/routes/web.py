from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="/frontend/templates")

templates.env.block_start_string = "<$"
templates.env.block_end_string = "$>"
templates.env.variable_start_string = "{$"
templates.env.variable_end_string = "$}"

web = APIRouter()


@web.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")


@web.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def html_svs(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {
            "request": request,
            "title": "Privacy Policy",
        }
    )


@web.get("/svs", response_class=HTMLResponse, include_in_schema=False)
async def html_svs(request: Request):
    return templates.TemplateResponse(
        "svs/index.html",
        {
            "request": request,
            "title": "SvS Minister Planning",
        }
    )


@web.get("/svs/reservations", response_class=HTMLResponse, include_in_schema=False)
async def html_svs_reservations(request: Request):
    return templates.TemplateResponse(
        "svs/reservations.html",
        {
            "request": request,
            "title": "SvS Minister Reservations",
            "reservations": [],
        }
    )
