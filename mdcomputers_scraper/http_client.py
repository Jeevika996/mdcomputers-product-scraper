
from __future__ import annotations

import logging
import time

import requests
from requests.adapters import HTTPAdapter, Retry

from . import config

logger = logging.getLogger(__name__)


class HttpClient:
    def __init__(
        self,
        timeout: int = config.REQUEST_TIMEOUT,
        max_retries: int = config.MAX_RETRIES,
        request_delay: float = config.DEFAULT_REQUEST_DELAY,
        headers: dict | None = None,
    ) -> None:
        self.timeout = timeout
        self.request_delay = max(0.0, request_delay)
        self._last_request_ts: float | None = None

        self.session = requests.Session()
        self.session.headers.update(headers or config.DEFAULT_HEADERS)

        retry_policy = Retry(
            total=max_retries,
            backoff_factor=config.BACKOFF_FACTOR,
            status_forcelist=config.RETRY_STATUS_CODES,
            allowed_methods=("GET",),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _throttle(self) -> None:
        if self._last_request_ts is None or self.request_delay == 0:
            return
        elapsed = time.monotonic() - self._last_request_ts
        remaining = self.request_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def get(self, url: str, params: dict | None = None) -> requests.Response:
        self._throttle()
        logger.debug("GET %s params=%s", url, params)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            self._last_request_ts = time.monotonic()
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as exc:
            logger.error("Request failed for %s: %s", url, exc)
            raise

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()