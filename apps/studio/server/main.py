"""SceneSmith Studio FastAPI transport over the shared artifact service.

Run:
    uvicorn main:app --port 8321 --reload
Env:
    SIM_LINK_DATA_ROOT  live checkout (default /Users/kelly/Developer/sim-link)
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from studio_service import StudioServiceError, service


app = FastAPI(title="SceneSmith Studio", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Result = TypeVar("Result")


def _http_call(operation: Callable[..., Result], *args: Any) -> Result:
    try:
        return operation(*args)
    except StudioServiceError as error:
        raise HTTPException(error.status_code, error.detail) from error


@app.get("/api/status")
def status() -> dict[str, Any]:
    return _http_call(service.status)


@app.get("/api/episodes")
def episodes() -> dict[str, Any]:
    return _http_call(service.episodes)


# Registered before episode_detail because its {episode_id:path} converter is greedy.
@app.get("/api/episodes/{episode_id:path}/frame/{index}/{view}")
def episode_frame(episode_id: str, index: int, view: str) -> Response:
    return Response(
        content=_http_call(service.episode_frame, episode_id, index, view),
        media_type="image/png",
    )


@app.get("/api/episodes/{episode_id:path}")
def episode_detail(episode_id: str) -> dict[str, Any]:
    return _http_call(service.episode_detail, episode_id)


@app.get("/api/workcells")
def workcells() -> dict[str, Any]:
    return _http_call(service.workcells)


@app.get("/api/tasks")
def tasks() -> dict[str, Any]:
    return _http_call(service.tasks)


@app.get("/api/robot")
def robot() -> dict[str, Any]:
    return _http_call(service.robot)


@app.get("/api/documents/{kind}/{filename}")
def document(kind: str, filename: str) -> dict[str, str]:
    return _http_call(service.document, kind, filename)


@app.get("/api/media")
def media(path: str) -> FileResponse:
    return FileResponse(_http_call(service.media_path, path))


@app.post("/api/actions/build-workcell")
def build_workcell(spec: dict[str, Any]) -> dict[str, Any]:
    return _http_call(service.build_workcell, spec)


@app.post("/api/actions/render-mirror")
def render_mirror(body: dict[str, Any]) -> dict[str, Any]:
    return _http_call(service.render_mirror, body)
