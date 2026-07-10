from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import requests

LOGGER_NAME = "iras_qualtrics_api"
LOG_FILE = Path(__file__).resolve().parents[1] / "logs" / "api_calls.log"
MAX_RESPONSE_CHARS = 2000
REDACTED_KEYS = {
    "authorization",
    "client_secret",
    "access_token",
    "refresh_token",
    "token",
}


class QualtricsAPIError(Exception):
    def __init__(
        self,
        message: str,
        *,
        service: str | None = None,
        function_name: str | None = None,
        method: str | None = None,
        url: str | None = None,
        status_code: int | None = None,
        params: Any = None,
        json_body: Any = None,
        data: Any = None,
        response_body: Any = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.service = service
        self.function_name = function_name
        self.method = method
        self.url = url
        self.status_code = status_code
        self.params = params
        self.json_body = json_body
        self.data = data
        self.response_body = response_body
        self.cause = cause

    def __str__(self) -> str:
        parts = [self.message]
        if self.service:
            parts.append(f"service={self.service}")
        if self.function_name:
            parts.append(f"function={self.function_name}")
        if self.method:
            parts.append(f"method={self.method}")
        if self.url:
            parts.append(f"url={self.url}")
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.params is not None:
            parts.append(f"params={_stringify(self.params)}")
        if self.json_body is not None:
            parts.append(f"json={_stringify(self.json_body)}")
        if self.data is not None:
            parts.append(f"data={_stringify(self.data)}")
        if self.response_body is not None:
            parts.append(f"response={_stringify(self.response_body)}")
        return " | ".join(parts)


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<redacted>" if key.lower() in REDACTED_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact(item) for item in value)
    return value


def _stringify(value: Any) -> str:
    try:
        return json.dumps(_redact(value), ensure_ascii=True, default=str)
    except TypeError:
        return repr(_redact(value))


def _response_summary(response: requests.Response) -> str:
    content_type = response.headers.get("Content-Type", "").lower()
    if "json" in content_type:
        try:
            return _stringify(response.json())
        except ValueError:
            pass

    if any(marker in content_type for marker in ("text/", "xml", "html", "csv", "plain")):
        body = response.text.strip().replace("\n", " ")
        return body[:MAX_RESPONSE_CHARS]

    return f"<{len(response.content)} bytes; content-type={content_type or 'unknown'}>"


def logged_request(
    method: str,
    url: str,
    *,
    function_name: str,
    service: str,
    raise_for_status: bool = False,
    **kwargs: Any,
) -> requests.Response:
    logger = get_logger()
    logged_kwargs = {key: _redact(value) for key, value in kwargs.items() if key != "headers"}
    logger.info(
        "%s | %s %s request | url=%s | params=%s | json=%s | data=%s | stream=%s",
        function_name,
        service,
        method.upper(),
        url,
        _stringify(logged_kwargs.get("params")),
        _stringify(logged_kwargs.get("json")),
        _stringify(logged_kwargs.get("data")),
        logged_kwargs.get("stream", False),
    )

    try:
        response = requests.request(method, url, **kwargs)
    except requests.exceptions.RequestException as exc:
        error = QualtricsAPIError(
            "Request failed",
            service=service,
            function_name=function_name,
            method=method.upper(),
            url=url,
            params=logged_kwargs.get("params"),
            json_body=logged_kwargs.get("json"),
            data=logged_kwargs.get("data"),
            cause=exc,
        )
        logger.exception("%s", error)
        raise error from exc

    logger.info(
        "%s | %s %s response | url=%s | status=%s | body=%s",
        function_name,
        service,
        method.upper(),
        url,
        response.status_code,
        _response_summary(response),
    )

    if raise_for_status:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            error = QualtricsAPIError(
                "HTTP error",
                service=service,
                function_name=function_name,
                method=method.upper(),
                url=url,
                status_code=response.status_code,
                params=logged_kwargs.get("params"),
                json_body=logged_kwargs.get("json"),
                data=logged_kwargs.get("data"),
                response_body=_response_summary(response),
                cause=exc,
            )
            logger.exception("%s", error)
            raise error from exc

    return response