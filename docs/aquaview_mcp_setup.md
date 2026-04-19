# AQUAVIEW MCP Setup

AQUAVIEW exposes a remote MCP endpoint at:

```text
https://mcp.aquaview.org/mcp
```

Legacy SSE is also listed by AQUAVIEW at:

```text
https://mcp.aquaview.org/sse
```

## VS Code Workspace Config

This repo includes a workspace MCP config at:

```text
.vscode/mcp.json
```

with:

```json
{
  "servers": {
    "aquaview": {
      "type": "http",
      "url": "https://mcp.aquaview.org/mcp"
    }
  }
}
```

In VS Code, use:

```text
MCP: List Servers
```

or:

```text
MCP: Open Workspace Folder MCP Configuration
```

Then start the `aquaview` server. For GitHub Copilot, MCP tools are generally available in Agent mode.

## Gemini / Antigravity

A Gemini/Antigravity config already exists at:

```text
/home/suramya/.gemini/antigravity/mcp_config.json
```

with an AQUAVIEW server entry.

## Claude

A user-scope Claude config was also observed at:

```text
/home/suramya/.claude.json
```

with an AQUAVIEW MCP entry.

## Codex Caveat

This Codex session does not automatically inherit VS Code, Gemini, or Claude MCP settings. MCP servers are normally loaded by the client process at startup. Adding `.vscode/mcp.json` helps VS Code-based agents, but it does not dynamically add `aquaview` tools to an already-running Codex API session.

If a future Codex runtime supports project MCP discovery, this workspace config is the file it should consume. Until then, we can still inspect AQUAVIEW through normal HTTP/browser access, but direct MCP tool calls are not available to this Codex session unless the host starts Codex with that MCP server configured.
