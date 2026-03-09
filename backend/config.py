from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "coze2dify"
    debug: bool = True

    # Project database (migration history, sync config)
    database_url: str = "postgresql://localhost:5432/coze2dify"

    # Coze API
    coze_api_base: str = "https://api.coze.com"
    coze_access_token: str = ""

    # Dify API / Console
    dify_api_base: str = ""
    dify_api_key: str = ""

    # Database direct connections
    dify_database_url: str = ""
    coze_database_url: str = ""

    # Upload
    max_upload_size_mb: int = 50

    # Dev Mode — auto-detect local Coze Studio / Dify deployments
    dev_mode: bool = False
    dev_mode_coze_paths: list[str] = [
        "~/coze-studio",
        "/opt/coze-studio",
        "~/coze-studio/docker",
    ]
    dev_mode_dify_paths: list[str] = [
        "~/dify",
        "~/dify/docker",
        "/opt/dify",
        "~/docker/dify",
    ]

    model_config = {"env_prefix": "COZE2DIFY_", "env_file": ".env"}


settings = Settings()
