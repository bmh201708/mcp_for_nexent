"""
Simple MCP server using FastMCP.
Exposes a few text utilities on SSE at port 8900.
Run with a conda env (e.g., conda activate mcp-env), then:
  python mcp_server.py
Server URL: http://127.0.0.1:8900/sse
If Nexent runs in Docker on the same host, configure URL as:
  http://host.docker.internal:8900/sse
"""

from fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP(name="Example MCP Server")

@mcp.tool(
    name="calculate_string_length",
    description="计算输入字符串的长度",
)
def calculate_string_length(text: str) -> int:
    return len(text)

@mcp.tool(
    name="to_uppercase",
    description="将字符串转换为大写",
)
def to_uppercase(text: str) -> str:
    return text.upper()

@mcp.tool(
    name="to_lowercase",
    description="将字符串转换为小写",
)
def to_lowercase(text: str) -> str:
    return text.lower()

@mcp.tool(
    name="reverse_text",
    description="反转字符串",
)
def reverse_text(text: str) -> str:
    return text[::-1]

if __name__ == "__main__":
    # Use an uncommon port and bind on all interfaces to avoid conflicts/access issues
    mcp.run(transport="sse", host="0.0.0.0", port=18900)
