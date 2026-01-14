# API Contracts

## Overview

The TFN AI Hub API is a FastAPI backend exposing REST endpoints for manufacturing performance data and AI-powered queries.

**Base URL:** `http://localhost:8000` (development)

## Authentication

Most endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

## Core Endpoints

### Health Check

#### `GET /health`
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-10T12:00:00Z",
  "version": "0.1.0",
  "database": {
    "mssql": "healthy",
    "supabase": "healthy"
  }
}
```

### Root

#### `GET /`
API welcome message.

**Response:**
```json
{
  "message": "Manufacturing Performance Assistant API"
}
```

---

## Asset Endpoints

### `GET /api/assets`
List all assets.

**Response:**
```json
{
  "assets": [
    {
      "id": "uuid",
      "name": "Grinder 5",
      "source_id": "GRN005",
      "area": "Grinding"
    }
  ]
}
```

### `GET /api/assets/{asset_id}`
Get asset details.

### `GET /api/assets/{asset_id}/history`
Get asset performance history (Story 4.4).

**Query Parameters:**
- `days`: Number of days of history (default: 7)
- `metric_type`: Filter by metric type

---

## OEE Endpoints

### `GET /api/oee`
Get OEE data for assets.

**Query Parameters:**
- `asset_id`: Specific asset (optional)
- `area`: Filter by area (optional)
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)

**Response:**
```json
{
  "oee": 85.5,
  "availability": 92.0,
  "performance": 95.0,
  "quality": 97.8,
  "breakdown": {
    "by_asset": [...],
    "by_day": [...]
  }
}
```

---

## Downtime Endpoints

### `GET /api/v1/downtime`
Get downtime analysis.

**Query Parameters:**
- `asset_id`: Specific asset (optional)
- `area`: Filter by area (optional)
- `date_from`: Start date
- `date_to`: End date

**Response:**
```json
{
  "total_downtime_minutes": 480,
  "reasons": [
    {
      "reason": "Mechanical Failure",
      "minutes": 180,
      "percentage": 37.5,
      "occurrences": 3
    }
  ],
  "pareto": {
    "cumulative_percentage": [37.5, 62.5, 80.0, 95.0, 100.0]
  }
}
```

---

## Production Endpoints

### `GET /api/production`
Get production status.

**Response:**
```json
{
  "assets": [
    {
      "asset_id": "uuid",
      "name": "Grinder 5",
      "status": "running",
      "current_rate": 45.2,
      "shift_target": 500,
      "shift_actual": 423,
      "variance_percent": -15.4
    }
  ]
}
```

---

## Safety Endpoints

### `GET /api/safety`
Get safety events.

**Query Parameters:**
- `severity`: Filter by severity (critical, high, medium, low)
- `status`: Filter by status (open, investigating, resolved)
- `area`: Filter by area
- `days`: Number of days to include (default: 30)

**Response:**
```json
{
  "events": [
    {
      "id": "uuid",
      "severity": "high",
      "status": "investigating",
      "area": "Grinding",
      "description": "Near miss incident",
      "occurred_at": "2026-01-09T14:30:00Z"
    }
  ],
  "summary": {
    "total": 5,
    "by_severity": {"critical": 0, "high": 2, "medium": 3, "low": 0}
  }
}
```

---

## Financial Endpoints

### `GET /api/financial/impact`
Calculate financial impact of downtime/waste.

**Query Parameters:**
- `asset_id`: Specific asset (optional)
- `date_from`: Start date
- `date_to`: End date

**Response:**
```json
{
  "total_loss": 125000.00,
  "breakdown": {
    "downtime": 85000.00,
    "quality": 25000.00,
    "waste": 15000.00
  },
  "by_asset": [...]
}
```

---

## Action Endpoints

### `GET /api/actions`
Get prioritized action list (Story 7.3).

**Response:**
```json
{
  "actions": [
    {
      "id": "uuid",
      "priority": 1,
      "category": "safety",
      "title": "Investigate near miss at Grinder 5",
      "description": "High severity incident reported",
      "estimated_impact": 50000.00,
      "asset_id": "uuid"
    }
  ],
  "summary": {
    "safety_items": 2,
    "performance_items": 5,
    "total_potential_savings": 175000.00
  }
}
```

### `GET /api/v1/actions`
Versioned actions endpoint (same response).

---

## AI Agent Endpoints

### `POST /api/agent/query`
Query the AI agent (Story 5.1+).

**Request:**
```json
{
  "query": "What is the OEE for Grinder 5 this week?",
  "conversation_id": "uuid",
  "context": {
    "asset_id": "uuid"
  }
}
```

**Response:**
```json
{
  "response": "The OEE for Grinder 5 this week is 85.5%...",
  "citations": [
    {
      "source": "daily_summaries",
      "query": "SELECT oee FROM daily_summaries WHERE...",
      "table": "daily_summaries",
      "confidence": 1.0
    }
  ],
  "follow_up_questions": [
    "What are the top downtime reasons?",
    "How does this compare to last week?"
  ],
  "tools_used": ["oee_query", "asset_lookup"]
}
```

---

## Chat Endpoints

### `POST /api/chat`
Text-to-SQL chat interface (Story 4.2).

**Request:**
```json
{
  "message": "Show me production for today",
  "conversation_id": "uuid"
}
```

**Response:**
```json
{
  "response": "Here is today's production...",
  "data": {...},
  "sql_generated": "SELECT * FROM...",
  "citations": [...]
}
```

---

## Memory Endpoints

### `POST /api/memory/store`
Store conversation memory (Story 4.1).

**Request:**
```json
{
  "user_id": "uuid",
  "messages": [...],
  "metadata": {
    "asset_ids": ["uuid"],
    "topics": ["oee", "downtime"]
  }
}
```

### `GET /api/memory/recall`
Recall relevant memories (Story 7.1).

**Query Parameters:**
- `query`: Search query
- `asset_id`: Filter by asset (optional)
- `limit`: Max results (default: 5)

---

## Citation Endpoints

### `GET /api/citations/{conversation_id}`
Get citations for a conversation (Story 4.5).

**Response:**
```json
{
  "citations": [
    {
      "id": "uuid",
      "source": "daily_summaries",
      "query": "...",
      "table_name": "daily_summaries",
      "record_id": "uuid",
      "confidence": 1.0,
      "created_at": "2026-01-10T12:00:00Z"
    }
  ]
}
```

---

## Cache Endpoints

### `GET /api/cache/stats`
Get cache statistics (Story 5.8).

**Response:**
```json
{
  "total_entries": 150,
  "hit_rate": 0.85,
  "by_tier": {
    "live": {"entries": 20, "ttl_seconds": 60},
    "daily": {"entries": 100, "ttl_seconds": 900},
    "static": {"entries": 30, "ttl_seconds": 3600}
  }
}
```

### `POST /api/cache/clear`
Clear cache entries.

**Request:**
```json
{
  "tier": "live",
  "tool_name": "asset_lookup"
}
```

---

## Live Pulse Endpoints

### `GET /api/live-pulse`
Get real-time production pulse.

**Response:**
```json
{
  "timestamp": "2026-01-10T12:00:00Z",
  "assets": [
    {
      "asset_id": "uuid",
      "status": "running",
      "current_oee": 87.5,
      "alerts": []
    }
  ]
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

**Common Status Codes:**
- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## OpenAPI Documentation

Interactive API documentation available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---
*Generated by BMAD Document Project Workflow on 2026-01-10*
