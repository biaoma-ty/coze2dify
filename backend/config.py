from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "coze2dify"
    debug: bool = False

    # Project database (migration history, sync config)
    database_url: str = "sqlite:///./coze2dify.db"
    db_url_encryption_key: str = ""

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

    # Workbench chat orchestration
    workbench_chat_api_base: str = "https://api.openai.com/v1"
    workbench_chat_api_key: str = ""
    workbench_chat_model: str = ""
    workbench_chat_timeout_seconds: float = 15.0

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
