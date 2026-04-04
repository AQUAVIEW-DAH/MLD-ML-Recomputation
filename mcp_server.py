import logging
import json
from typing import Any
from dataclasses import asdict
import xarray as xr

# Try importing the official MCP Python SDK
try:
    from mcp.server.stdio import stdio_server
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from mld_pipeline import get_mld_estimate
from mld_core import DEFAULT_RTOFS_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mld-mcp-server")


def start_mcp_server():
    if not MCP_AVAILABLE:
        logger.error("The 'mcp' package is not installed. Please try: pip install mcp")
        return

    # Load dataset
    try:
        rtofs_ds = xr.open_dataset(DEFAULT_RTOFS_FILE)
        logger.info("Loaded RTOFS dataset.")
    except Exception as e:
        rtofs_ds = None
        logger.error(f"Failed to load rtofs ds: {e}")

    server = Server("mld-estimator")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """
        List available tools.
        """
        return [
            Tool(
                name="get_mld_estimate",
                description="Get the best Machine Learning corrected Mixed Layer Depth (MLD) estimate for an ocean location. It combines background hydrodynamic models with nearby real-time observations.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number", "description": "Latitude of the query location (e.g. 28.5)"},
                        "lon": {"type": "number", "description": "Longitude of the query location (e.g. -88.2)"},
                        "time": {"type": "string", "description": "ISO-8601 time string (e.g. 2026-03-01T12:00:00Z)"},
                    },
                    "required": ["lat", "lon", "time"],
                },
            )
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[TextContent]:
        """
        Handle tool execution requests.
        """
        if name != "get_mld_estimate":
            raise ValueError(f"Unknown tool: {name}")

        if not arguments:
            raise ValueError("Missing arguments")

        lat = arguments.get("lat")
        lon = arguments.get("lon")
        query_time = arguments.get("time")

        if lat is None or lon is None or query_time is None:
            raise ValueError("Missing required arguments")

        if rtofs_ds is None:
            return [TextContent(type="text", text="Error: RTOFS backend dataset unavailable.")]

        try:
            res = get_mld_estimate(lat, lon, query_time, rtofs_ds)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(asdict(res), indent=2)
                )
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing get_mld_estimate: {str(e)}")]

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    start_mcp_server()
