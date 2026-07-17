"""HTTP client with automatic x402 payment for Feedback Synthesis backend."""

import base64
import json
import logging
from typing import Any

import requests

logger = logging.getLogger("feedback-synthesis-mcp")

PAYMENT_REQUIRED_HEADER = "payment-required"
PAYMENT_SIGNATURE_HEADER = "Payment-Signature"


class PaymentError(Exception):
    """Raised when x402 payment cannot be completed."""


class FeedbackSynthesisClient:
    """Thin HTTP client that calls the Feedback Synthesis backend and auto-pays x402."""

    def __init__(self, backend_url: str, private_key: str = ""):
        self.backend_url = backend_url.rstrip("/")
        self._private_key = private_key
        self._x402_client = None
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "feedback-synthesis-mcp-client/0.1.0"

    def _get_x402_client(self):
        if self._x402_client is not None:
            return self._x402_client
        if not self._private_key:
            return None

        from eth_account import Account
        from x402 import SchemeRegistration, x402ClientConfig, x402ClientSync
        from x402.mechanisms.evm.exact.client import ExactEvmScheme
        from x402.mechanisms.evm.signers import EthAccountSigner

        try:
            account = Account.from_key(self._private_key)
        except Exception as e:
            raise PaymentError(f"Invalid wallet key: {e}")

        signer = EthAccountSigner(account)
        scheme = ExactEvmScheme(signer=signer)
        config = x402ClientConfig(
            schemes=[
                SchemeRegistration(
                    network="eip155:8453",
                    client=scheme,
                )
            ]
        )
        self._x402_client = x402ClientSync.from_config(config)
        return self._x402_client

    def call(self, tool_name: str, **params: Any) -> dict[str, Any]:
        """Call a backend tool endpoint with automatic x402 payment."""
        url = f"{self.backend_url}/api/v1/{tool_name}"
        body = {k: v for k, v in params.items() if v is not None}

        try:
            resp = self._session.post(url, json=body, timeout=60)
        except requests.ConnectionError as e:
            return {"error": f"Cannot reach backend: {e}"}
        except requests.RequestException as e:
            return {"error": f"Request failed: {e}"}

        if resp.status_code == 402:
            return self._handle_402(resp, url, body)

        if resp.status_code >= 400:
            return {
                "error": f"Backend error: HTTP {resp.status_code}",
                "tool": tool_name,
                "detail": resp.text[:500],
            }

        return resp.json()

    def _handle_402(self, resp: requests.Response, url: str, body: dict) -> dict[str, Any]:
        if not self._private_key:
            return {
                "error": "Payment required but no wallet key configured. "
                         "Set EVM_PRIVATE_KEY env var with a wallet funded with USDC on Base mainnet.",
            }

        try:
            x402_client = self._get_x402_client()
        except PaymentError as e:
            return {"error": str(e)}
        if x402_client is None:
            return {"error": "Failed to initialize x402 payment client."}

        pr_header = resp.headers.get(PAYMENT_REQUIRED_HEADER)
        if not pr_header:
            return {"error": "Server returned 402 but no PAYMENT-REQUIRED header."}

        try:
            from x402 import parse_payment_required
            pr_bytes = base64.b64decode(pr_header)
            payment_required = parse_payment_required(pr_bytes)
        except Exception as e:
            return {"error": f"Failed to parse payment requirements: {e}"}

        try:
            payment_payload = x402_client.create_payment_payload(payment_required)
        except Exception as e:
            return {"error": f"Failed to create payment: {e}"}

        try:
            payload_json = payment_payload.model_dump_json(by_alias=True, exclude_none=True)
            payload_b64 = base64.b64encode(payload_json.encode()).decode()
        except Exception as e:
            return {"error": f"Failed to serialize payment: {e}"}

        try:
            retry_resp = self._session.post(
                url,
                json=body,
                headers={PAYMENT_SIGNATURE_HEADER: payload_b64},
                timeout=60,
            )
        except requests.ConnectionError as e:
            return {"error": f"Cannot reach backend: {e}"}
        except requests.RequestException as e:
            return {"error": f"Request failed: {e}"}

        if retry_resp.status_code == 402:
            return {"error": "Payment was rejected. Ensure your wallet has sufficient USDC on Base mainnet."}

        if retry_resp.status_code >= 400:
            return {
                "error": f"Backend error after payment: HTTP {retry_resp.status_code}",
                "detail": retry_resp.text[:500],
            }

        return retry_resp.json()
