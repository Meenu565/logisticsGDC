"""FastMCP server entrypoint for Smart Dispatcher tools."""

from collections.abc import Callable

from fastmcp import FastMCP

from app.mcp.tools import drivers, eta, health, memory, orders, planning, recommendations

ToolRegistrar = Callable[[FastMCP], None]


def create_mcp_server() -> FastMCP:
    """Create and register the Smart Dispatcher MCP server."""
    mcp = FastMCP("Smart Dispatcher MCP")
    register_tools(mcp)
    return mcp


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tool modules."""
    registrars: list[ToolRegistrar] = [
        health.register,
        orders.register,
        planning.register,
        drivers.register,
        eta.register,
        recommendations.register,
        memory.register,
    ]
    for registrar in registrars:
        registrar(mcp)


mcp = create_mcp_server()


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
