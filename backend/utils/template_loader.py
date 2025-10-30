from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


@lru_cache(maxsize=1)
def get_templates_env() -> Environment:
    root = Path(__file__).resolve().parents[1] / "templates"
    loader = FileSystemLoader(str(root))
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(enabled_extensions=(".j2",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def render_template(template_path: str, **kwargs: Any) -> str:
    env = get_templates_env()
    tmpl = env.get_template(template_path)
    return tmpl.render(**kwargs)
