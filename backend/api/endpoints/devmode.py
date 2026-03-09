"""Dev Mode endpoints — auto-detect local Coze Studio / Dify deployments."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from config import settings

router = APIRouter()


@router.get("/status")
async def devmode_status():
    """Return dev mode toggle state and detected local deployments."""
    if not settings.dev_mode:
        return {"enabled": False, "detected": {"coze": [], "dify": []}}

    from core.devmode.detector import DevModeDetector

    detector = DevModeDetector()
    detected = detector.detect_all()
    return {
        "enabled": True,
        "detected": {k: [asdict(svc) for svc in v] for k, v in detected.items()},
    }


@router.get("/scan")
async def devmode_scan():
    """Force re-scan for local deployments (regardless of dev_mode toggle)."""
    from core.devmode.detector import DevModeDetector

    detector = DevModeDetector()
    detected = detector.detect_all()
    return {
        "detected": {k: [asdict(svc) for svc in v] for k, v in detected.items()},
    }


@router.post("/connect")
async def devmode_connect():
    """Auto-connect to all detected services and return connection results."""
    from core.devmode.detector import DevModeDetector

    detector = DevModeDetector()
    detected = detector.detect_all()

    results: dict[str, list[dict]] = {"coze": [], "dify": []}

    for svc in detected.get("dify", []):
        conn_result = {"name": svc.name, "path": svc.path, "db_url": svc.db_url, "api_url": svc.api_url}
        # Test DB connection
        if svc.db_url:
            try:
                from core.dify.db_reader import DifyDbReader

                reader = DifyDbReader(svc.db_url)
                conn_result["db_connected"] = reader.test_connection()
            except Exception as exc:
                conn_result["db_connected"] = False
                conn_result["db_error"] = str(exc)
        # Test API connection
        if svc.api_url:
            try:
                from core.dify.api_client import DifyApiClient

                client = DifyApiClient(api_base=svc.api_url)
                api_result = await client.test_connection()
                conn_result["api_connected"] = api_result.get("connected", False)
            except Exception:
                conn_result["api_connected"] = False

        results["dify"].append(conn_result)

    for svc in detected.get("coze", []):
        conn_result = {"name": svc.name, "path": svc.path, "db_url": svc.db_url, "api_url": svc.api_url}
        if svc.db_url:
            try:
                from core.coze.db_reader import CozeDbReader

                reader = CozeDbReader(svc.db_url)
                conn_result["db_connected"] = reader.test_connection()
            except Exception as exc:
                conn_result["db_connected"] = False
                conn_result["db_error"] = str(exc)
        results["coze"].append(conn_result)

    return {"results": results}
