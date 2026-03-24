import inspect

from fastapi.routing import APIRoute

from api.endpoints.platform import router as platform_router


def test_platform_routes_only_keep_async_handlers_for_api_clients() -> None:
    routes = {
        route.name: inspect.iscoroutinefunction(route.endpoint)
        for route in platform_router.routes
        if isinstance(route, APIRoute)
    }

    assert routes == {
        "coze_connect": True,
        "coze_list_workflows": True,
        "coze_fetch_workflow": True,
        "dify_connect": True,
        "dify_list_apps": True,
        "db_connect": False,
        "db_list_workflows": False,
    }
