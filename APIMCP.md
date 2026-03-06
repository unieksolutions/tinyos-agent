<!--
ts: 2026-01-27T12:30:00Z | git: <to-be-filled> | path: /opt/bootstrap
-->

# API & MCP Design Standards

## Service Discovery Metadata

**REQUIRED:** Add YAML frontmatter at the top of your APIMCP.md file for automatic service discovery.

The Service Discovery API (`http://localhost:63100/api/v1/services`) scans all APIMCP.md files and exposes a unified endpoint for agents to discover available tools without reading large docs (100x context window savings).

### Frontmatter Format

```markdown
---
service_name: Your Service Name
version: 1.0.0

# API endpoints (if service provides REST API)
api:
  dev: http://localhost:61XXX
  accept: http://localhost:64XXX
  prod: http://localhost:63XXX

# Health check endpoints (optional, defaults to {api}/health)
health_check:
  dev: http://localhost:61XXX/health
  accept: http://localhost:64XXX/health
  prod: http://localhost:63XXX/health

# MCP server info (if service provides MCP tools)
mcp:
  type: stdio              # or: sse, http
  command: python /opt/projects/yourproject/mcp_server.py
  description: What MCP tools this server provides

# Additional endpoints (optional)
web:
  dev: http://localhost:61XXX
  accept: http://localhost:64XXX
  prod: http://localhost:63XXX
---
```

### Examples

**API Only:**
```yaml
---
service_name: SPI Manager
api:
  dev: http://localhost:61115
  prod: http://localhost:63115
health_check:
  dev: http://localhost:61115/health
  prod: http://localhost:63115/health
---
```

**MCP Only:**
```yaml
---
service_name: Code Analyzer
mcp:
  type: stdio
  command: python /opt/projects/code-analyzer/mcp_server.py
  description: Code analysis and refactoring tools
---
```

**API + MCP:**
```yaml
---
service_name: Tickets
api:
  dev: http://localhost:61119
  prod: http://localhost:63119
mcp:
  type: stdio
  command: python /opt/projects/tickets/mcp_server.py
  description: Ticket management tools
web:
  dev: http://localhost:61549
  prod: http://localhost:63549
---
```

**Why This Matters:**
- Agents query discovery API: `curl http://localhost:63100/api/v1/services`
- Get lightweight JSON (~10-20 tokens) instead of reading 200+ line docs (~2,000 tokens)
- Service Discovery auto-scans APIMCP.md files and extracts metadata
- No manual registry maintenance needed

---

## Overview

This template defines standards for building APIs (REST, GraphQL) and Model Context Protocol (MCP) servers in SPI projects.

---

## Health Endpoint Standard (MANDATORY)

**Every SPI service MUST expose `GET /health` at the root path.**

This is the single, canonical health check endpoint across all SPI projects. Do not use `/healthz`, `/healthcheck`, `/api/health`, `/v1/health`, or any other variant as the primary health endpoint.

### Response Format

```json
{
  "status": "healthy",
  "service": "your-service-name",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

**Required fields:**
- `status`: `"healthy"` or `"unhealthy"`
- `service`: Service name (matches `service_name` in APIMCP.md frontmatter)

**Optional fields:**
- `version`: Service version string
- `uptime_seconds`: Seconds since startup
- `checks`: Object with subsystem status (db, cache, gpu, etc.)

**Unhealthy example (still returns HTTP 200 with status field):**
```json
{
  "status": "unhealthy",
  "service": "spi-manager",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "gpu": "unavailable"
  }
}
```

### Rules
- **HTTP 200** for both healthy and unhealthy (status field distinguishes)
- **HTTP 503** only when service cannot respond at all
- **No authentication** required (health checks must work without API keys)
- **Fast** — must respond within 1 second (no heavy DB queries)
- **Aliases allowed** — you MAY add `/healthz` as an alias pointing to the same handler, but `/health` is canonical
- **Service discovery** uses `/health` — the `health_check` field in APIMCP.md frontmatter defaults to `{api_url}/health`

### Implementation Example (FastAPI)
```python
import time
_start_time = time.time()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "my-service",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - _start_time)
    }
```

---

## REST API Standards

### Endpoint Design

**Versioning:**
- Explicit version in path: `/api/v1/resource`
- Never: `/api/resource` (no version)

**Resource Naming:**
- Plural nouns: `/users`, `/tickets`, `/models`
- Not: `/getUser`, `/createTicket` (verbs in path)

**HTTP Methods:**
- `GET` - Read/retrieve (idempotent, no body)
- `POST` - Create new resource (returns ID)
- `PUT` - Replace entire resource (idempotent)
- `PATCH` - Partial update (specific fields)
- `DELETE` - Remove resource (idempotent)

**Examples:**
```
GET    /api/v1/tickets          # List all tickets
GET    /api/v1/tickets/123      # Get specific ticket
POST   /api/v1/tickets          # Create new ticket
PATCH  /api/v1/tickets/123      # Update specific fields
DELETE /api/v1/tickets/123      # Delete ticket
```

### Response Format

**Standard JSON structure:**
```json
{
  "success": true,
  "data": {
    "id": "123",
    "field": "value"
  },
  "meta": {
    "timestamp": "2026-01-27T12:30:00Z",
    "version": "1.0.0",
    "request_id": "uuid"
  }
}
```

**Error response:**
```json
{
  "success": false,
  "error": {
    "code": "ERR_NOT_FOUND",
    "message": "Ticket with ID 123 not found",
    "details": {
      "resource": "ticket",
      "id": "123"
    }
  },
  "meta": {
    "timestamp": "2026-01-27T12:30:00Z",
    "version": "1.0.0",
    "request_id": "uuid"
  }
}
```

**Stack traces:**
- Development: Include full stack trace in `error.stack`
- Production: Never include stack traces (security risk)

### Error Handling

**HTTP Status Codes:**

**2xx - Success:**
- `200 OK` - Successful GET, PATCH, DELETE
- `201 Created` - Successful POST (include Location header)
- `204 No Content` - Successful DELETE with no response body

**4xx - Client Errors:**
- `400 Bad Request` - Invalid input, validation failed
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Authenticated but not permitted
- `404 Not Found` - Resource doesn't exist
- `409 Conflict` - Resource already exists, version conflict
- `422 Unprocessable Entity` - Valid JSON but business logic fails

**5xx - Server Errors:**
- `500 Internal Server Error` - Unexpected server error
- `502 Bad Gateway` - Upstream service failure
- `503 Service Unavailable` - Temporarily unavailable (maintenance)
- `504 Gateway Timeout` - Upstream timeout

**Error Codes:**
- Format: `ERR_CATEGORY_SPECIFIC`
- Examples: `ERR_AUTH_INVALID_TOKEN`, `ERR_DB_CONNECTION_FAILED`, `ERR_VALIDATION_MISSING_FIELD`

### Authentication

**Development:**
- API keys in header: `X-API-Key: <key>`
- Bearer tokens: `Authorization: Bearer <token>`
- Basic auth for testing only

**Production:**
- OAuth 2.0 / JWT preferred
- Token refresh mechanism
- Rate limiting per client

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-API-Key: sk_live_51HqB2KLLz...
```

### Rate Limiting

**Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1672531199
```

**Response on limit exceeded:**
- Status: `429 Too Many Requests`
- Header: `Retry-After: 60` (seconds)

### Pagination

**Query parameters:**
```
GET /api/v1/tickets?page=2&limit=50&sort=-created_at
```

**Response meta:**
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "page": 2,
    "limit": 50,
    "total": 1234,
    "pages": 25
  }
}
```

### Filtering & Sorting

**Query parameters:**
```
?status=open                    # Filter by field
?status=open,in_progress        # Multiple values (OR)
?priority=high&status=open      # Multiple filters (AND)
?sort=created_at                # Sort ascending
?sort=-created_at               # Sort descending (-)
```

---

## GraphQL Standards

*(Add if project uses GraphQL)*

### Schema Design
- Use strong typing
- Nullable vs non-nullable fields
- Pagination with cursor-based connections

### Resolvers
- Batching and caching (DataLoader pattern)
- N+1 query prevention
- Error handling per field

---

## MCP (Model Context Protocol) Standards

### Server Structure

**Entry point:**
```python
#!/usr/bin/env python3
"""
MCP Server: {Service Name}
Provides tools for {purpose}
"""
from mcp.server import Server
import mcp.types as types

app = Server("{service-name}")
```

### Tool Design

**Naming convention:**
- Descriptive verbs: `search_tickets`, `create_task`, `get_status`
- Not: `tickets`, `task`, `status` (unclear action)

**Parameters:**
- JSON Schema with clear required/optional
- Default values where sensible
- Description for each parameter

**Example:**
```python
@app.tool()
async def search_tickets(
    query: str,
    status: str | None = None,
    limit: int = 10
) -> list[dict]:
    """
    Search tickets by text query.

    Args:
        query: Search text (title, description)
        status: Filter by status (open, closed, in_progress)
        limit: Maximum results (default 10, max 100)

    Returns:
        List of matching tickets with id, title, status
    """
    ...
```

### Resource Design

**URI Schemes:**
- Project-specific: `ticket://123`, `doc://README.md`, `model://llama-3.2`
- Descriptive: `{service}://{identifier}`

**Types:**
- Define clear resource types
- Include MIME types where applicable

**Example:**
```python
@app.resource("ticket://{ticket_id}")
async def get_ticket_resource(uri: str) -> types.Resource:
    ticket_id = uri.split("://")[1]
    ticket = await fetch_ticket(ticket_id)
    return types.Resource(
        uri=uri,
        name=f"Ticket {ticket_id}",
        mimeType="application/json",
        text=json.dumps(ticket, indent=2)
    )
```

### Error Handling

**Structured errors:**
```python
from mcp.server import McpError

if not ticket_exists(id):
    raise McpError(
        code="NOT_FOUND",
        message=f"Ticket {id} not found"
    )
```

---

## Project-Specific Implementation

*(Each project should add this section with their specific details)*

### Example: Tickets Service

**REST API:**
- Base URL (dev): `http://localhost:61119/api/v1`
- Base URL (prod): `http://localhost:63119/api/v1`
- Authentication: API key in header
- Rate limit: 1000 requests/hour

**Endpoints:**
- `GET /tickets` - List tickets (paginated)
- `POST /tickets` - Create ticket
- `GET /tickets/{id}` - Get specific ticket
- `PATCH /tickets/{id}` - Update ticket
- `DELETE /tickets/{id}` - Delete ticket
- `GET /search?q={query}` - Search tickets

**MCP Server:**
- Name: `tickets-mcp`
- Tools:
  - `search_tickets(query, status, limit)` - Search by text
  - `create_ticket(title, description, priority)` - Create new
  - `update_ticket(id, **fields)` - Update fields
  - `get_ticket(id)` - Get by ID
- Resources:
  - `ticket://{id}` - Individual ticket JSON
  - `ticket://search?q={query}` - Search results

---

## Testing

### REST API Tests

**Unit tests:**
- Test each endpoint with valid/invalid inputs
- Test authentication and authorization
- Test error responses

**Integration tests:**
- Test end-to-end flows
- Test with real database
- Test rate limiting

### MCP Tests

**Tool tests:**
- Test with mcp-inspector
- Verify JSON schema validation
- Test error conditions

**Resource tests:**
- Verify URI resolution
- Test MIME types
- Test text/blob responses

---

## Documentation

**Required for each API:**
- OpenAPI/Swagger spec (REST)
- MCP tool descriptions (MCP)
- Example requests and responses
- Authentication guide
- Error code reference

**Location:**
- `/opt/projects/{name}/API.md` - Full API documentation
- `/opt/projects/{name}/APIMCP.md` - This file with project specifics

---

## Security

**Never expose:**
- Internal error details (production)
- Stack traces (production)
- Database schema details
- Credential information

**Always validate:**
- Input parameters (type, range, format)
- Authentication tokens
- Authorization permissions
- Rate limits

**Always log:**
- API calls (request ID, timestamp, endpoint)
- Errors (with context)
- Authentication failures
- Rate limit violations

---

## References

- REST: [REST API Tutorial](https://restfulapi.net/)
- MCP: [Model Context Protocol Spec](https://spec.modelcontextprotocol.io/)
- OpenAPI: [OpenAPI Specification](https://swagger.io/specification/)
- HTTP Status Codes: [MDN HTTP Status](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
