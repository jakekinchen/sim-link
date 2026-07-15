"""SceneSmith Studio MCP server using the official Python SDK over stdio."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from studio_service import service


mcp = FastMCP(
    "SceneSmith Studio",
    instructions=(
        "Read signed SceneSmith foundry artifacts. The only write tools build "
        "labelled simulation workcell fixtures or render mirrors; neither grants "
        "training, hardware, transfer, or promotion authority."
    ),
    json_response=True,
)


@mcp.tool()
def loop_status() -> dict[str, Any]:
    """Return the live loop window, task, ledger state, briefs, and reviews."""

    return service.status()


@mcp.tool()
def list_episodes() -> dict[str, Any]:
    """List expert episodes and policy traces from the signed artifact stores."""

    return service.episodes()


@mcp.tool()
def get_episode(episode_id: str) -> dict[str, Any]:
    """Get one expert or policy episode by its registry id."""

    return service.episode_detail(episode_id)


@mcp.tool()
def list_tasks() -> dict[str, Any]:
    """List signed task result-gate summaries."""

    return service.tasks()


@mcp.tool()
def list_workcells() -> dict[str, Any]:
    """List compiled simulation workcell manifests and preview paths."""

    return service.workcells()


@mcp.tool()
def build_workcell(spec: dict[str, Any]) -> dict[str, Any]:
    """Build a labelled simulation fixture from a v1 arrangement spec.

    This is a no-authority visualization action. It grants no metric, training,
    transfer, hardware, or promotion authority.
    """

    return service.build_workcell(spec)


@mcp.tool()
def render_mirror(trace: str) -> dict[str, Any]:
    """Render a visualization mirror for one whitelisted policy trace path.

    This is a no-authority visualization action and does not execute a policy.
    """

    return service.render_mirror({"trace": trace})


if __name__ == "__main__":
    mcp.run(transport="stdio")
