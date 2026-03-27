import inspect

from fastapi.routing import APIRoute

from api.endpoints.conversion import router as conversion_router


def test_conversion_routes_only_keep_async_handlers_where_await_is_required() -> None:
    routes = {
        route.name: inspect.iscoroutinefunction(route.endpoint)
        for route in conversion_router.routes
        if isinstance(route, APIRoute)
    }

    assert routes == {
        "list_conversions": False,
        "convert_workflow": True,
        "convert_workflow_from_api": True,
        "convert_workflow_from_db": False,
        "get_conversion": False,
        "download_dsl": False,
        "get_report": False,
        "write_to_dify": False,
    }
