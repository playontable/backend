from fastmcp import FastMCP
from fastmcp.server.apps import AppConfig

mcp = FastMCP()

UI = "https://playontable.com/index.html"

@mcp.tool(app = AppConfig(resource_uri = UI))
def index() -> dict:
    """Returns the initial content of the web site."""
    return {
        "structuredContent": {},
        "content": [],
        "_meta": {}
    }

if __name__ == "__main__": mcp.run()