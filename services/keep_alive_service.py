import asyncio
import os
from contextlib import suppress
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import settings
from logging_setup import get_logger


logger = get_logger("sfjpii.ai.keep_alive")


def _is_enabled() -> bool:
    configured = os.getenv("KEEP_ALIVE_ENABLED")
    if configured is not None:
        return configured.strip().lower() == "true"

    return bool(
        os.getenv("RENDER")
        or os.getenv("RENDER_SERVICE_ID")
        or os.getenv("RENDER_EXTERNAL_URL")
    )


def _health_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/health"


def _request_health(url: str) -> int:
    request = Request(
        url,
        method="GET",
        headers={"User-Agent": "SFJPII-AI-KeepAlive/1.0"},
    )
    with urlopen(request, timeout=10) as response:
        return response.status


async def _ping_backend(url: str) -> None:
    started_at = perf_counter()
    try:
        status = await asyncio.to_thread(_request_health, url)
        logger.info(
            "keep_alive_ping_ok",
            extra={
                "operation": "keep_alive",
                "duration_ms": round((perf_counter() - started_at) * 1000),
                "status": status,
            },
        )
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        logger.warning(
            "keep_alive_ping_failed",
            extra={
                "operation": "keep_alive",
                "duration_ms": round((perf_counter() - started_at) * 1000),
                "error_type": type(error).__name__,
            },
        )


async def _keep_alive_loop(url: str, interval_seconds: int) -> None:
    while True:
        await _ping_backend(url)
        await asyncio.sleep(interval_seconds)


def start_keep_alive_task() -> asyncio.Task | None:
    if not _is_enabled():
        logger.info("keep_alive_disabled", extra={"operation": "startup"})
        return None

    url = _health_url(settings.sfjpii_backend_url)
    task = asyncio.create_task(
        _keep_alive_loop(url, settings.keep_alive_interval_seconds),
        name="sfjpii-backend-keep-alive",
    )
    logger.info(
        "keep_alive_started",
        extra={"operation": "startup"},
    )
    return task


async def stop_keep_alive_task(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
