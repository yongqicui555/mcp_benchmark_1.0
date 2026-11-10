from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fence(value: str, lang: str = "") -> str:
    return f"```{lang}\n{value.rstrip()}\n```"


def compact_json(value: Any, limit: int = 8000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) > limit:
        return text[:limit] + "\n... [truncated]"
    return text


def text_from_result(result: Any) -> str:
    if isinstance(result, dict):
        content = result.get("content")
        if isinstance(content, list):
            texts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("text")]
            if texts:
                return "\n".join(texts)
        contents = result.get("contents")
        if isinstance(contents, list):
            texts = [item.get("text", "") for item in contents if isinstance(item, dict) and item.get("text")]
            if texts:
                return "\n".join(texts)
    return compact_json(result)


def message_text(messages: list[dict[str, Any]]) -> str:
    return compact_json(messages)


def assistant_text(assistant: dict[str, Any]) -> str:
    visible: dict[str, Any] = {}
    if assistant.get("content"):
        visible["content"] = assistant["content"]
    if assistant.get("tool_calls"):
        visible["tool_calls"] = assistant["tool_calls"]
    return compact_json(visible or assistant)


def evidence_block(evidence: dict[str, Any] | None) -> list[str]:
    if not evidence:
        return []
    payload = dict(evidence)
    decoded = payload.pop("decoded", "")
    parts = ["## Evidence 解码", fence(compact_json(payload), "json")]
    if decoded:
        rendered = decoded[:4000] + ("\n... [truncated]" if len(decoded) > 4000 else "")
        parts.extend(["解码后的真实参数:", fence(rendered, "text")])
    return parts


def render_tool_execution(execution: dict[str, Any], index: int) -> str:
    call = execution.get("tool_call", {})
    function = call.get("function", {}) if isinstance(call, dict) else {}
    name = function.get("name") or execution.get("step", {}).get("tool") or execution.get("step", {}).get("uri") or "<unknown>"
    kind = execution.get("kind", "tool")
    args = execution.get("arguments")
    if args is None:
        args = execution.get("step", {}).get("args") or {}

    heading = "Builtin 调用" if kind == "builtin" else "工具调用"
    if kind == "resource":
        heading = "资源读取"

    parts = [f"## {heading} {index}"]
    parts.append(f"- 名称: `{name}`")
    parts.append(f"- 类型: `{kind}`")
    if execution.get("builtin_sink_status"):
        parts.append(f"- Builtin sink 状态: `{execution['builtin_sink_status']}`")
    parsed_sink = execution.get("result", {}).get("parsed_sink") if isinstance(execution.get("result"), dict) else None
    if parsed_sink:
        parts.append("- parsed sink:")
        parts.append(fence(compact_json(parsed_sink), "json"))
    parts.append("参数:")
    parts.append(fence(compact_json(args), "json"))

    if "result" in execution:
        parts.append("## 工具返回")
        parts.append(fence(text_from_result(execution["result"]), "text"))
    if "error" in execution:
        parts.append("## 工具错误")
        parts.append(fence(str(execution["error"]), "text"))
    if execution.get("evidence"):
        parts.extend(evidence_block(execution["evidence"]))
    return "\n\n".join(parts)


def render_direct_step(step: dict[str, Any], index: int) -> str:
    plan = step.get("step", step)
    step_type = plan.get("type") or step.get("type")
    name = plan.get("tool") or plan.get("uri") or step_type
    parts = [f"### Step {index}: {step_type} {name}"]
    args = plan.get("args") or {}
    if args:
        parts.append("参数:")
        parts.append(fence(compact_json(args), "json"))
    elif step_type != "config_entrypoint":
        parts.append("参数:")
        parts.append(fence("{}", "json"))

    if step.get("command"):
        parts.append("启动命令:")
        parts.append(fence(compact_json({"command": step.get("command"), "args": step.get("args", [])}), "json"))
    if "result" in step:
        parts.append("返回:")
        parts.append(fence(text_from_result(step["result"]), "text"))
    if step.get("stdout") or step.get("stderr"):
        parts.append("进程输出:")
        parts.append(fence(compact_json({"stdout": step.get("stdout", ""), "stderr": step.get("stderr", ""), "returncode": step.get("returncode")}), "json"))
    if "error" in step:
        parts.append("错误:")
        parts.append(fence(str(step["error"]), "text"))
    if step.get("evidence"):
        parts.append("返回 / Evidence:")
        parts.append(fence(compact_json(step["evidence"]), "json"))
    return "\n\n".join(parts)


def render_basic_info(trace: dict[str, Any]) -> list[str]:
    spec = trace.get("spec", {})
    llm = trace.get("llm", {})
    actual_model_passes = trace.get("actual_model_passes")
    if actual_model_passes is None:
        actual_model_passes = len(trace.get("rounds", []))
    return [
        "## 基本信息",
        f"- 路径: `{spec.get('path')}`",
        f"- 论文路径: `{spec.get('paper_path') or spec.get('normalized_path') or llm.get('path_flow', '')}`",
        f"- 固定模型调用次数: `{llm.get('fixed_model_passes', spec.get('fixed_model_passes', ''))}`",
        f"- 实际模型调用次数: `{actual_model_passes}`",
        f"- Objective: `{spec.get('objective')}`",
        f"- Sink: `{spec.get('sink')}`",
        f"- 是否触发 evidence: `{bool(trace.get('evidence'))}`",
        f"- 停止原因: `{trace.get('stop_reason', '')}`",
    ]


def render_direct_trace(trace: dict[str, Any]) -> str:
    title = trace.get("variant", "trace")
    parts = [f"# KeyVault Direct Path 轨迹: {title}"]
    parts.extend(render_basic_info(trace))
    parts.append("## Direct 执行步骤")
    for index, step in enumerate(trace.get("direct_steps", []), 1):
        parts.append(render_direct_step(step, index))
    parts.extend(evidence_block(trace.get("evidence")))
    if trace.get("final"):
        parts.append("## 停止点")
        parts.append(fence(str(trace["final"]), "text"))
    return "\n\n".join(parts) + "\n"


def render_llm_trace(trace: dict[str, Any], compact: bool = False) -> str:
    title = trace.get("variant", "trace")
    parts = [f"# KeyVault 交互轨迹: {title}"]
    parts.extend(render_basic_info(trace))

    if not compact and trace.get("openai_tools"):
        parts.append("## 暴露给模型的工具列表")
        parts.append(fence(compact_json(trace["openai_tools"]), "json"))
    if not compact and trace.get("host_builtin_tools"):
        parts.append("## Host Builtin 工具列表")
        parts.append("中文注释: 这些是 host 侧真实工具能力；运行器只记录模型是否调用以及参数是否进入最终 sink。")
        parts.append(fence(compact_json(trace["host_builtin_tools"]), "json"))
    if not compact and trace.get("mcp_resources"):
        parts.append("## 暴露给模型的资源列表")
        parts.append(fence(compact_json(trace["mcp_resources"]), "json"))

    for round_item in trace.get("rounds", []):
        round_index = round_item.get("round")
        parts.append(f"## 第 {round_index} 次模型输入")
        parts.append(fence(message_text(round_item.get("messages") or []), "json"))

        parts.append(f"## 第 {round_index} 次模型输出")
        parts.append(fence(assistant_text(round_item.get("assistant") or {}), "json"))

        executions = round_item.get("tool_executions") or []
        for index, execution in enumerate(executions, 1):
            parts.append(render_tool_execution(execution, index))

        if round_item.get("stopped_on_evidence"):
            parts.append("## 停止点")
            parts.append(fence("发现可解析 evidence，当前路径立即停止；不会追加模型轮次。", "text"))

    if trace.get("builtin_status"):
        parts.append("## Builtin 路径状态")
        parts.append(fence(str(trace["builtin_status"]), "text"))
    parts.extend(evidence_block(trace.get("evidence")))
    if trace.get("final"):
        parts.append("## 停止点")
        parts.append(fence(str(trace["final"]), "text"))
    return "\n\n".join(parts) + "\n"


def render_trace(trace: dict[str, Any], compact: bool = False) -> str:
    if trace.get("direct") or trace.get("spec", {}).get("direct"):
        return render_direct_trace(trace)
    return render_llm_trace(trace, compact=compact)


def export_one(path: Path, out_dir: Path) -> Path:
    trace = json.loads(path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{path.stem}.md"
    out_path.write_text(render_trace(trace), encoding="utf-8")
    return out_path


def export_one_compact(path: Path, out_dir: Path) -> Path:
    trace = json.loads(path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{path.stem}.md"
    out_path.write_text(render_trace(trace, compact=True), encoding="utf-8")
    return out_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Export model trace JSON files to readable Markdown.")
    parser.add_argument("--input", default="interaction_logs/keyvault/model_traces")
    parser.add_argument("--output", default="interaction_logs/keyvault/model_traces_md")
    parser.add_argument("--compact", action="store_true", help="Skip exposed tool/resource catalog sections.")
    parser.add_argument("--trace", action="append", default=[], help="Specific trace stem or JSON path.")
    args = parser.parse_args()

    root = repo_root()
    input_dir = root / args.input
    output_dir = root / args.output

    paths: list[Path] = []
    if args.trace:
        for item in args.trace:
            candidate = Path(item)
            paths.append(candidate if candidate.exists() else input_dir / f"{item}.json")
    else:
        paths = [p for p in sorted(input_dir.glob("*.json")) if p.name != "summary.json"]

    written = []
    for path in paths:
        if args.compact:
            written.append(export_one_compact(path, output_dir))
        else:
            written.append(export_one(path, output_dir))
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
