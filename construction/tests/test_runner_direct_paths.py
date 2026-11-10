from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

from scripts import run_interactions


def test_direct_plan_for_p18_has_fixed_two_step_order() -> None:
    plan = run_interactions.direct_plan_for({"path": "P18", "direct_plan": []})

    assert [step["tool"] for step in plan] == ["list_keys", "rotate_key"]
    assert plan[1]["args"]["key_name"] == "id_rsa"


def test_run_one_uses_direct_executor_without_openai_client(monkeypatch: Any, tmp_path: Path) -> None:
    variant_dir = tmp_path / "variants" / "keyvault" / "L3_P17(STEAL)"
    variant_dir.mkdir(parents=True)

    spec = {
        "variant": "L3_P17(STEAL)",
        "path": "P17",
        "layer": "L3",
        "objective": "STEAL",
        "fixed_model_passes": 0,
        "direct": True,
    }
    config = {"mcpServers": {"keyvault": {"command": "uv", "args": []}}}
    called = {"direct": False}

    class ForbiddenClient:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise AssertionError("OpenAI client must not be created for direct paths")

    async def fake_run_direct_one(_vdir: Path, _config: dict[str, Any], _spec: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
        called["direct"] = True
        trace["direct"] = True
        trace["actual_model_passes"] = 0
        trace["direct_steps"] = [{"type": "call_tool", "tool": "list_keys"}]
        return trace

    monkeypatch.setattr(run_interactions, "load_json", lambda path: spec if path.name == "variant_spec.json" else config)
    monkeypatch.setattr(run_interactions, "load_config", lambda _path: config)
    monkeypatch.setattr(run_interactions, "AsyncOpenAI", ForbiddenClient)
    monkeypatch.setattr(run_interactions, "run_direct_one", fake_run_direct_one)

    args = argparse.Namespace(base="keyvault", variants=str(tmp_path / "variants" / "keyvault"), reset_data=False, prompt="")
    trace = asyncio.run(run_interactions.run_one("L3_P17(STEAL)", args, {"paths": {}}))

    assert called["direct"] is True
    assert trace["actual_model_passes"] == 0
