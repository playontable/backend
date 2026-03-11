from fastmcp import FastMCP

mcp = FastMCP()

@mcp.tool(app = {"url": "https://playontable.com/"})
def table():
    return {"status": "ok"}

if __name__ == "__main__": mcp.run("http")