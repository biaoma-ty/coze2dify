import inspect

from fastapi.routing import APIRoute

from api.endpoints.coze_source import router as coze_source_router


def test_coze_source_routes_only_keep_async_handlers_for_upload_and_api_fetch() -> None:
    routes = {
        route.name: inspect.iscoroutinefunction(route.endpoint)
        for route in coze_source_router.routes
        if isinstance(route, APIRoute)
    }

    assert routes == {
        "upload_coze_workflow": True,
        "fetch_from_api": True,
        "test_db_connection": False,
        "list_db_workflows": False,
        "fetch_from_db": False,
    }
