"""
Shared InsForge REST client.
Uses the InsForge API endpoints:

  GET    {base}/api/database/records/{table}              → list rows
  POST   {base}/api/database/records/{table}              → insert rows
  PATCH  {base}/api/database/records/{table}?id=eq.{id}   → update row
  POST   {base}/api/database/advance/rawsql               → raw SQL
"""

import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("INSFORGE_BASE_URL", "")
API_KEY = os.getenv("INSFORGE_API_KEY", "")
ANON_KEY = os.getenv("INSFORGE_ANON_KEY", "")

_TIMEOUT = 30


def _headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    h = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def list_rows(table: str, select: str = "*", params: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Fetch rows from a table via GET /api/database/records/{table}."""
    url = f"{BASE_URL}/api/database/records/{table}"
    query = {"select": select}
    if params:
        query.update(params)
    resp = httpx.get(url, headers=_headers(), params=query, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def update_row(table: str, row_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """PATCH a single row by id. Returns the updated row."""
    url = f"{BASE_URL}/api/database/records/{table}"
    params = {"id": f"eq.{row_id}"}
    resp = httpx.patch(
        url,
        headers=_headers(prefer="return=representation"),
        params=params,
        json=data,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else {}


def insert_rows(table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """POST new rows to a table. Returns inserted rows."""
    url = f"{BASE_URL}/api/database/records/{table}"
    resp = httpx.post(
        url,
        headers=_headers(prefer="return=representation"),
        json=rows,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def raw_sql(query: str, params: Optional[List] = None) -> Dict[str, Any]:
    """Execute raw SQL via POST /api/database/advance/rawsql."""
    url = f"{BASE_URL}/api/database/advance/rawsql"
    body: Dict[str, Any] = {"query": query}
    if params:
        body["params"] = params
    resp = httpx.post(url, headers=_headers(), json=body, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()
