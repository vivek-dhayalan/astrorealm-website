"""MatchAPI — Indian astrology marriage matching.

Run:  uvicorn app.main:app --reload
Site: http://127.0.0.1:8000/        Docs: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Body, FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from . import service
from .examples import CHART_EXAMPLES, IMAGE_EXAMPLES, MATCH_EXAMPLES
from .core.ephemeris import get_engine
from .core.ephemeris.base import DEFAULT_POSITION_MODE
from .core.timeutil import InputError
from .geo import get_resolver
from .rules import v1 as rules
from .schemas import ChartImageRequest, ChartRequest, MatchRequest
from .web.routes import router as web_router

app = FastAPI(
    title="MatchAPI",
    version="0.1.0",
    description=(
        "Marriage matching using Ashtakoota, Dasa Porutham, Mangal dosha and KP 7th-cusp sub-lord. "
        "Each method returns its own result; there is no combined verdict.\n\n"
        "Place data © GeoNames (geonames.org), CC BY 4.0. Fallback geocoding © OpenStreetMap contributors."
    ),
)


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "web" / "static"), name="static")
app.include_router(web_router)


@app.exception_handler(InputError)
async def _input_error(_: Request, exc: InputError):
    status = 503 if exc.code == "GEO_DATA_MISSING" else 422
    return JSONResponse(status_code=status, content={"error": exc.code, "message": exc.message, **exc.extra})


@app.get("/health")
def health():
    r = get_resolver()
    return {
        "status": "ok",
        "engine": get_engine().name,
        "positions": DEFAULT_POSITION_MODE.value,
        "rulesVersion": rules.VERSION,
        "geoData": r.store.count() if r.store else None,
    }


@app.post("/v1/match")
def match(req: Annotated[MatchRequest, Body(openapi_examples=MATCH_EXAMPLES)]):
    return service.run_match(req)


@app.post("/v1/chart")
def chart(req: Annotated[ChartRequest, Body(openapi_examples=CHART_EXAMPLES)]):
    return service.run_chart(req)


@app.post("/v1/chart/image", response_class=Response,
          responses={200: {"content": {"image/svg+xml": {}}, "description": "SVG chart image"}})
def chart_image(req: Annotated[ChartImageRequest, Body(openapi_examples=IMAGE_EXAMPLES)]):
    """Returns one SVG image containing the South Indian Rasi chart, the Navamsa chart and the
    KP planet and cusp tables (choose which with `include`; labels via `lang`).

    In Swagger, click **Download file** after executing and open the downloaded `.svg` in a browser.
    In a web page, use the endpoint's output as the source of an `img` element."""
    return Response(content=service.run_chart_image(req), media_type="image/svg+xml")


@app.get("/v1/places")
def places(q: str = Query(..., min_length=2), limit: int = Query(5, ge=1, le=20)):
    return {"query": q, "candidates": service.search_places(q, limit)}
