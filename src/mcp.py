from fastmcp import FastMCP
from fastmcp.server.apps import AppConfig

mcp = FastMCP()

UI = "https://playontable.com/index.html"

@mcp.tool(app = AppConfig(resource_uri = UI))
def index() -> dict:
    return {
        "structuredContent": {},
        "content": [],
        "_meta": {}
    }