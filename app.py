
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_config_key(key):
    key = key.strip()

    if key == "NUM_WORKERS":
        return "workers"

    if key.startswith("APP_"):
        key = key[4:].lower()

    return key.lower()


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in (
            "true", "1", "yes", "on"
        )

    return str(value)


def load_config():
    config = DEFAULTS.copy()

    env_name = os.environ.get("APP_ENV", "development")
    yaml_path = Path(f"config.{env_name}.yaml")

    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}

        for key, value in yaml_config.items():
            key = to_config_key(key)
            config[key] = coerce(key, value)

    if Path(".env").exists():
        file_env = dotenv_values(".env")

        for key, value in file_env.items():
            if value is not None:
                key = to_config_key(key)
                config[key] = coerce(key, value)

    for key, value in os.environ.items():
        if key.startswith("APP_"):
            normalized = to_config_key(key)
            if normalized in config:
                config[normalized] = coerce(normalized, value)

    return config


@app.get("/effective-config")
def effective_config(set: list[str] | None = Query(default=None)):
    config = load_config()

    for item in set or []:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        key = to_config_key(key)

        if key in config:
            config[key] = coerce(key, value)

    config["api_key"] = "****"
    return config
