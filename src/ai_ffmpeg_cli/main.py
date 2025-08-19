from __future__ import annotations

import logging

import typer
from rich import print as rprint

from .command_builder import build_commands
from .config import AppConfig
from .config import load_config
from .confirm import confirm_prompt
from .context_scanner import scan
from .errors import BuildError
from .errors import ConfigError
from .errors import ExecError
from .errors import ParseError
from .intent_router import route_intent
from .llm_client import LLMClient
from .llm_client import OpenAIProvider

app = typer.Typer(add_completion=False, help="AI-powered ffmpeg CLI", invoke_without_command=True)


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


@app.callback()
def main(
    ctx: typer.Context | None = None,
    prompt: str | None = typer.Argument(
        None, help="Natural language prompt; if provided, runs once and exits"
    ),
    yes: bool = typer.Option(False, "--yes/--no-yes", help="Skip confirmation and overwrite"),
    model: str | None = typer.Option(None, "--model", help="LLM model override"),
    dry_run: bool = typer.Option(None, "--dry-run/--no-dry-run", help="Preview only"),
    timeout: int = typer.Option(60, "--timeout", help="LLM timeout seconds"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
) -> None:
    """Initialize global options and optionally run one-shot prompt."""
    _setup_logging(verbose)
    try:
        cfg = load_config()
        if model:
            cfg.model = model
        if dry_run is not None:
            cfg.dry_run = dry_run
        cfg.timeout_seconds = timeout

        if ctx is not None:
            ctx.obj = {"config": cfg, "assume_yes": yes}

        # One-shot if a prompt is passed to the top-level
        invoked_none = (ctx is None) or (ctx.invoked_subcommand is None)
        if prompt is not None and invoked_none:
            try:
                context = scan()
                client = _make_llm(cfg)
                intent = client.parse(prompt, context, timeout=cfg.timeout_seconds)
                plan = route_intent(intent)
                commands = build_commands(plan, assume_yes=yes)
                from .executor import preview
                from .executor import run

                # Always show preview before asking for confirmation
                preview(commands)
                confirmed = (
                    True if yes else confirm_prompt("Run these commands?", cfg.confirm_default, yes)
                )
                code = run(
                    commands,
                    confirm=confirmed,
                    dry_run=cfg.dry_run,
                    show_preview=False,
                    assume_yes=yes,
                )
                raise typer.Exit(code)
            except (ParseError, BuildError, ExecError) as e:
                rprint(f"[red]Error:[/red] {e}")
                raise typer.Exit(1) from e
    except ConfigError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def _make_llm(cfg: AppConfig) -> LLMClient:
    if not cfg.openai_api_key:
        raise ConfigError(
            "OPENAI_API_KEY is required for LLM parsing. "
            "Please set it in your environment or create a .env file with: "
            "OPENAI_API_KEY=sk-your-key-here"
        )
    provider = OpenAIProvider(api_key=cfg.openai_api_key, model=cfg.model)
    return LLMClient(provider)


@app.command()
def nl(
    ctx: typer.Context,
    prompt: str | None = typer.Argument(None, help="Natural language prompt"),
) -> None:
    """Translate NL to ffmpeg, preview, confirm, and execute."""
    obj = ctx.obj or {}
    cfg: AppConfig = obj["config"]
    assume_yes: bool = obj["assume_yes"]

    try:
        context = scan()
        client = _make_llm(cfg)

        def handle_one(p: str) -> int:
            intent = client.parse(p, context, timeout=cfg.timeout_seconds)
            plan = route_intent(intent)
            commands = build_commands(plan, assume_yes=assume_yes)
            confirmed = (
                True
                if assume_yes
                else confirm_prompt("Run these commands?", cfg.confirm_default, assume_yes)
            )
            return_code = 0
            if confirmed:
                from .executor import run

                return_code = run(
                    commands, confirm=True, dry_run=cfg.dry_run, assume_yes=assume_yes
                )
            else:
                from .executor import preview

                preview(commands)
            return return_code

        if prompt:
            code = handle_one(prompt)
            raise typer.Exit(code)
        else:
            rprint("[bold]aiclip[/bold] interactive mode. Type 'exit' to quit.")
            while True:
                try:
                    line = input("> ").strip()
                except EOFError:
                    break
                if not line or line.lower() in {"exit", "quit"}:
                    break
                try:
                    handle_one(line)
                except (ParseError, BuildError, ExecError) as e:
                    rprint(f"[red]Error:[/red] {e}")
    except (ConfigError, ParseError, BuildError, ExecError) as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


# Stretch goal placeholder
@app.command()
def explain(
    ffmpeg_command: str | None = typer.Argument(None, help="Existing ffmpeg command to explain"),
) -> None:
    if not ffmpeg_command:
        rprint("Provide an ffmpeg command to explain.")
        raise typer.Exit(2)
    rprint("Explanation is not implemented in MVP.")


if __name__ == "__main__":
    app()
