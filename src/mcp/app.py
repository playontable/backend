from fastmcp import FastMCP

mcp = FastMCP()

@mcp.tool(app = {"url": "https://playontable.com/"})
def table():
    return {"status": "ok"}