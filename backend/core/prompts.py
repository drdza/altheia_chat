# app/cre/prompts.py

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent.parent / "assets" / "prompts")),
    autoescape=select_autoescape(disabled_extensions=("j2",), default_for_string=False, default=False),
    trim_blocks=True, lstrip_blocks=True,
)

def render_prompt(template_name: str, **kwargs) -> str:
    tpl = _env.get_template(template_name)
    return tpl.render(**kwargs)
