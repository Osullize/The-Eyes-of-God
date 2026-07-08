from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


def load_project_env(env_file: str | Path | None = None, *, override: bool = False) -> bool:
    path = Path(env_file) if env_file is not None else DEFAULT_ENV_FILE
    return bool(load_dotenv(dotenv_path=path, override=override))
