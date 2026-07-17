"""HTTP(S) adapter around the asusrouter library."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from typing import Any

from asusrouter.connection_config import ARConnectionConfigKey
from asusrouter.modules.data import AsusData
from asusrouter.modules.parental_control import (
    AsusParentalControl,
    PCRuleType,
    ParentalControlRule,
)
from asusrouter.modules.port_forwarding import PortForwardingRule
from asusrouter.modules.system import AsusSystem
from asusrouter.modules.wlan import AsusWLAN

from ..config import Settings
from ..errors import RouterOperationError, UnsupportedOperationError


class AsusRouterHttpClient:
    """Thin async wrapper that owns one AsusRouter connection per operation."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._router: Any | None = None

    async def __aenter__(self) -> "AsusRouterHttpClient":
        self._settings.require_http()

        from asusrouter import AsusRouter

        self._router = AsusRouter(
            hostname=self._settings.host or "",
            username=self._settings.username or "",
            password=self._settings.http_password,
            port=self._settings.http_port,
            use_ssl=self._settings.use_ssl,
            cache_time=self._settings.cache_seconds,
            connection_config={
                ARConnectionConfigKey.VERIFY_SSL: self._settings.verify_tls,
                ARConnectionConfigKey.STRICT_SSL: self._settings.verify_tls,
            },
        )
        try:
            connected = await self._router.async_connect()
            if connected is False:
                raise RouterOperationError(
                    code="http_connect_failed",
                    message="Unable to connect to the router over HTTP(S).",
                )
            return self
        except Exception:
            with suppress(Exception):
                await self._router.async_del_connection()
            self._router = None
            raise

    async def __aexit__(self, *_exc: object) -> None:
        if self._router is not None:
            await self._router.async_del_connection()

    @property
    def router(self) -> Any:
        if self._router is None:
            raise RouterOperationError(
                code="http_not_connected",
                message="HTTP router client is not connected.",
            )
        return self._router

    async def get_identity(self) -> Any:
        return await self.router.async_get_identity(force=True)

    async def get_data(self, data_type: str, *, force: bool = True) -> Any:
        try:
            enum_value = AsusData[data_type.upper()]
        except KeyError as exc:
            raise UnsupportedOperationError(
                code="unsupported_data_type",
                message="Unsupported AsusRouter data type.",
                details={"data_type": data_type},
            ) from exc
        return await self.router.async_get_data(enum_value, force=force)

    async def get_many(self, data_types: Sequence[str]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for data_type in data_types:
            try:
                result[data_type] = await self.get_data(data_type)
            except Exception as exc:  # noqa: BLE001 - preserve partial snapshots
                result[data_type] = {"error": str(exc)}
        return result

    async def restart_service(self, service: str) -> bool:
        enum_name = f"RESTART_{service.upper()}"
        if service == "reboot":
            enum_name = "REBOOT"
        try:
            state = AsusSystem[enum_name]
        except KeyError as exc:
            raise UnsupportedOperationError(
                code="unsupported_service",
                message="Service is not in the HTTP restart allowlist.",
                details={"service": service},
            ) from exc
        return bool(await self.router.async_set_state(state))

    async def set_guest_wifi(self, *, band: str, slot: int, enabled: bool) -> bool:
        state = AsusWLAN.ON if enabled else AsusWLAN.OFF
        band_index = {"2g": 0, "5g": 1, "5g2": 2, "6g": 3}[band]
        api_id = f"{band_index}.{slot}"
        return bool(
            await self.router.async_set_state(
                state,
                arguments={"api_type": "gwlan", "api_id": api_id},
            )
        )

    async def set_port_forwarding_enabled(self, enabled: bool) -> bool:
        from asusrouter.modules.port_forwarding import AsusPortForwarding

        state = AsusPortForwarding.ON if enabled else AsusPortForwarding.OFF
        return bool(await self.router.async_set_state(state))

    async def add_port_forwarding_rule(
        self,
        *,
        name: str,
        ip: str,
        port: str,
        protocol: str,
        port_external: str,
        ip_external: str = "",
    ) -> bool:
        rule = PortForwardingRule(
            name=name,
            ip_address=ip,
            port=port,
            protocol=protocol,
            ip_external=ip_external,
            port_external=port_external,
        )
        return bool(await self.router.async_set_port_forwarding_rules(rule))

    async def remove_port_forwarding_rule(
        self,
        *,
        ip: str,
        port_external: str,
        protocol: str,
        port: str | None = None,
        ip_external: str | None = None,
    ) -> list[Any]:
        rule = PortForwardingRule(
            ip_address=ip,
            port=port or "",
            protocol=protocol,
            ip_external=ip_external or "",
            port_external=port_external,
        )
        return await self.router.async_remove_port_forwarding_rules(rules=rule)

    async def set_parental_enabled(self, enabled: bool) -> bool:
        state = AsusParentalControl.ON if enabled else AsusParentalControl.OFF
        return bool(await self.router.async_set_state(state))

    async def set_parental_rule(
        self,
        *,
        mac: str,
        name: str,
        blocked: bool,
    ) -> bool:
        await self.get_data("parental_control")
        rule = ParentalControlRule(
            mac=mac,
            name=name,
            type=PCRuleType.BLOCK if blocked else PCRuleType.DISABLE,
        )
        return bool(await self.router.async_set_state(rule))

    async def remove_parental_rule(self, *, mac: str) -> bool:
        await self.get_data("parental_control")
        rule = ParentalControlRule(mac=mac, type=PCRuleType.REMOVE)
        return bool(await self.router.async_set_state(rule))
