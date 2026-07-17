"""Async client for pmproxy REST API."""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

import httpx

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any

    ProgressCallback = Callable[[float, float, str], Coroutine[Any, Any, None]]


class PCPClient:
    """Async client for pmproxy REST API.

    Handles PMAPI context management and metric fetching via the pmproxy
    REST API endpoints.

    Args:
        base_url: Base URL for pmproxy (e.g., http://localhost:44322).
        target_host: Which pmcd host to connect to (passed as hostspec).
        auth: Optional HTTP basic auth tuple (username, password).
        timeout: Request timeout in seconds.
        verify: TLS verification (True, False, or path to CA bundle).
    """

    def __init__(
        self,
        base_url: str,
        target_host: str = "localhost",
        auth: tuple[str, str] | None = None,
        timeout: float = 30.0,
        verify: bool | str = True,
    ) -> None:
        """Initialize the PCP client."""
        self._base_url = base_url
        self._target_host = target_host
        self._auth = auth
        self._timeout = timeout
        self._verify = verify
        self._client: httpx.AsyncClient | None = None
        self._context_id: int | None = None

    async def __aenter__(self) -> Self:
        """Enter async context and establish pmapi context."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            auth=self._auth,
            timeout=self._timeout,
            verify=self._verify,
        )
        resp = await self._client.get(
            "/pmapi/context",
            params={"hostspec": self._target_host},
        )
        resp.raise_for_status()
        self._context_id = resp.json()["context"]
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit async context and close httpx client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def target_host(self) -> str:
        """The pmcd host this client is connected to."""
        return self._target_host

    @property
    def context_id(self) -> int | None:
        """The pmapi context ID, or None if not connected."""
        return self._context_id

    async def _recreate_context(self) -> None:
        """Recreate the pmapi context after expiration."""
        if self._client is None:
            raise RuntimeError("Client not connected. Use async with context.")
        resp = await self._client.get(
            "/pmapi/context",
            params={"hostspec": self._target_host},
        )
        resp.raise_for_status()
        self._context_id = resp.json()["context"]

    async def _request_with_retry(self, method: str, **kwargs) -> httpx.Response:
        """Make a request, recreating context on expiration errors.

        Args:
            method: HTTP method to call.
            **kwargs: Arguments to pass to the request.

        Returns:
            The HTTP response.

        Raises:
            RuntimeError: If client is not connected.
            httpx.HTTPStatusError: If the request fails after retry.
        """
        if self._client is None:
            raise RuntimeError("Client not connected. Use async with context.")

        resp = await self._client.request(method, **kwargs)

        if resp.status_code == 400:
            data = resp.json()
            if "unknown context identifier" in data.get("message", ""):
                await self._recreate_context()
                kwargs["params"]["context"] = self._context_id
                resp = await self._client.request(method, **kwargs)

        return resp

    async def fetch(self, metric_names: list[str]) -> dict:
        """Fetch current values for metrics.

        Args:
            metric_names: List of PCP metric names to fetch.

        Returns:
            Raw JSON response from pmproxy /pmapi/fetch endpoint.

        Raises:
            RuntimeError: If client is not connected.
            httpx.HTTPStatusError: If the request fails.
        """
        resp = await self._request_with_retry(
            "GET",
            url="/pmapi/fetch",
            params={"context": self._context_id, "names": ",".join(metric_names)},
        )
        resp.raise_for_status()
        return resp.json()

    async def search(self, pattern: str) -> list[dict]:
        """Search for metrics matching pattern.

        Args:
            pattern: Metric name prefix to search for (e.g., "kernel.all").

        Returns:
            List of metric metadata dicts from pmproxy.

        Raises:
            RuntimeError: If client is not connected.
            httpx.HTTPStatusError: If the request fails.
        """
        resp = await self._request_with_retry(
            "GET",
            url="/pmapi/metric",
            params={"context": self._context_id, "prefix": pattern},
        )
        resp.raise_for_status()
        return resp.json().get("metrics", [])

    async def describe(self, metric_name: str) -> dict:
        """Get metric metadata.

        Args:
            metric_name: Full PCP metric name.

        Returns:
            Metric metadata dict, or empty dict if not found.

        Raises:
            RuntimeError: If client is not connected.
            httpx.HTTPStatusError: If the request fails.
        """
        resp = await self._request_with_retry(
            "GET",
            url="/pmapi/metric",
            params={"context": self._context_id, "names": metric_name},
        )
        resp.raise_for_status()
        metrics = resp.json().get("metrics", [])
        return metrics[0] if metrics else {}

    async def fetch_with_rates(
        self,
        metric_names: list[str],
        counter_metrics: set[str],
        sample_interval: float = 1.0,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, dict]:
        """Fetch metrics, calculating rates for counters.

        Takes two samples separated by sample_interval seconds.
        Counter metrics are converted to per-second rates.
        Gauge metrics return the second sample's value.

        Args:
            metric_names: List of PCP metric names to fetch.
            counter_metrics: Set of metric names that are counters.
            sample_interval: Seconds between samples for rate calculation.
            progress_callback: Optional async callback for progress updates.
                Called with (current, total, message) during long operations.

        Returns:
            Dict mapping metric name to {value, instances} where value/instances
            contain the rate (for counters) or instant value (for gauges).
        """
        if progress_callback:
            await progress_callback(0, 100, "Collecting first sample...")

        t1 = await self.fetch(metric_names)

        if progress_callback:
            await progress_callback(20, 100, f"Waiting {sample_interval}s for rate calculation...")

        await asyncio.sleep(sample_interval)

        if progress_callback:
            await progress_callback(70, 100, "Collecting second sample...")

        t2 = await self.fetch(metric_names)

        if progress_callback:
            await progress_callback(90, 100, "Computing rates...")

        ts1 = t1.get("timestamp", 0.0)
        ts2 = t2.get("timestamp", 0.0)
        if isinstance(ts1, dict):
            ts1 = ts1.get("s", 0) + ts1.get("us", 0) / 1e6
        if isinstance(ts2, dict):
            ts2 = ts2.get("s", 0) + ts2.get("us", 0) / 1e6
        elapsed = ts2 - ts1 if ts2 > ts1 else sample_interval

        results: dict[str, dict] = {}

        values_t1 = {v.get("name"): v for v in t1.get("values", [])}
        values_t2 = {v.get("name"): v for v in t2.get("values", [])}

        for metric_name in metric_names:
            v1_data = values_t1.get(metric_name, {})
            v2_data = values_t2.get(metric_name, {})

            instances_t1 = {
                inst.get("instance", -1): inst.get("value", 0)
                for inst in v1_data.get("instances", [])
            }
            instances_t2 = {
                inst.get("instance", -1): inst.get("value", 0)
                for inst in v2_data.get("instances", [])
            }

            if metric_name in counter_metrics:
                computed: dict[str | int, float] = {}
                for inst_id, val2 in instances_t2.items():
                    val1 = instances_t1.get(inst_id, val2)
                    delta = val2 - val1
                    if delta < 0:
                        delta = val2
                    computed[inst_id] = delta / elapsed
                results[metric_name] = {"instances": computed, "is_rate": True}
            else:
                results[metric_name] = {"instances": instances_t2, "is_rate": False}

        return results
