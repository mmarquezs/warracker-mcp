# Warracker MCP Server

MCP server for [Warracker](https://github.com/sassanix/Warracker) warranty management. Enables AI agents to create, update, query warranties, upload files, and manage tags programmatically.

Built with [FastMCP](https://github.com/jlowin/fastmcp), runs as a stdio subprocess — no HTTP server, no Docker.

## Installation

```bash
pip install warracker-mcp
```

Or install directly from GitHub (pin to a tag):

```bash
pip install warracker-mcp@git+https://github.com/mmarquezs/warracker-mcp@v0.1.0
```

## Configuration

Set these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `WARRACKER_URL` | Base URL of your Warracker instance | `http://10.0.0.143:80` |
| `WARRACKER_USERNAME` | Username for authentication | `admin` |
| `WARRACKER_PASSWORD` | Password for authentication | `your-password` |

## MCP Client Configuration

Add to your MCP client config (e.g. Claude Desktop, opencode, Cursor):

```json
{
  "mcpServers": {
    "warracker": {
      "command": "warracker-mcp",
      "env": {
        "WARRACKER_URL": "http://10.0.0.143:80",
        "WARRACKER_USERNAME": "your-username",
        "WARRACKER_PASSWORD": "your-password"
      }
    }
  }
}
```

Or with `uvx`:

```json
{
  "mcpServers": {
    "warracker": {
      "command": "uvx",
      "args": ["warracker-mcp"],
      "env": {
        "WARRACKER_URL": "http://10.0.0.143:80",
        "WARRACKER_USERNAME": "your-username",
        "WARRACKER_PASSWORD": "your-password"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `warranty_create` | Create a warranty with all fields + optional file attachment |
| `warranty_update` | Update warranty fields by ID, with optional file attachment |
| `warranty_get` | Get a single warranty by ID |
| `warranties_list` | List/search warranties with optional filtering and pagination |
| `tags_list` | List all existing tags |
| `tag_create` | Create a new tag with name and optional color |
| `currencies_list` | List all supported currencies |
| `warranty_upload_file` | Upload a file to an existing warranty (base64 content or URL) |

### Warranty Duration

When creating or updating a warranty, provide exactly one of:
- `warranty_duration_years` — duration in years
- `warranty_duration_months` — duration in months
- `warranty_duration_days` — duration in days
- `exact_expiration_date` — exact date (YYYY-MM-DD)
- `is_lifetime` — set to `true` for lifetime warranty

### File Uploads

Files can be attached during creation/update via `file_content_b64`, `file_name`, and `file_type` parameters, or uploaded separately using `warranty_upload_file` which accepts either base64-encoded content or a URL to download from.

Supported file types:
- **invoice, manual, other_document**: PDF, PNG, JPG, JPEG, ZIP, RAR, WEBP, GIF
- **product_photo**: PNG, JPG, JPEG, WEBP, GIF

## Development

```bash
git clone https://github.com/mmarquezs/warracker-mcp
cd warracker-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run the server:

```bash
WARRACKER_URL=http://localhost:80 WARRACKER_USERNAME=admin WARRACKER_PASSWORD=pass warracker-mcp
```

## License

MIT
