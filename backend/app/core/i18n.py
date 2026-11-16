from typing import Annotated, Literal
from fastapi import Header

SupportedLanguage = Literal["fr", "en"]


def get_request_language(
    accept_language: Annotated[str | None, Header()] = None,
) -> SupportedLanguage:
    if accept_language:
        for item in accept_language.split(","):
            language = item.split(";")[0].strip().lower().split("-")[0]

            if language in ("fr", "en"):
                return language

    return "en"