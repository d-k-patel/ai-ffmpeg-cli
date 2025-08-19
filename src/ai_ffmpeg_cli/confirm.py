from __future__ import annotations


def confirm_prompt(question: str, default_yes: bool = True, assume_yes: bool = False) -> bool:
    if assume_yes:
        return True
    default = "Y/n" if default_yes else "y/N"
    try:
        resp = input(f"{question} [{default}] ").strip().lower()
    except EOFError:
        return default_yes
    if not resp:
        return default_yes
    return resp in {"y", "yes"}
