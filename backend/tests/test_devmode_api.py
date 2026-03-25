import inspect

from fastapi.routing import APIRoute

from api.endpoints.devmode import router as devmode_router


def test_devmode_routes_only_keep_async_handlers_where_http_awaits_are_required() -> None:
    routes = {
        route.name: inspect.iscoroutinefunction(route.endpoint)
        for route in devmode_router.routes
        if isinstance(route, APIRoute)
    }

    assert routes == {
        "devmode_status": False,
        "devmode_scan": False,
        "devmode_connect": True,
    }
