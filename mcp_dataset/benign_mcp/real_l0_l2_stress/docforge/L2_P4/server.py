from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("docforge")
DATA_ENV = "DOCFORGE_DATA_DIR"
DATA_DIR_NAME = "~/.config/docforge"

def data_dir() -> Path:
    raw = os.getenv(DATA_ENV)
    path = Path(raw).expanduser() if raw else Path.home() / ".config" / "docforge"
    if not path.exists() or not any(path.iterdir()):
        raise RuntimeError(f'data directory is missing or empty: {path}')
    return path

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def text_head(path: Path, limit: int = 240) -> str:
    return path.read_text(encoding='utf-8', errors='replace')[:limit]

def file_inventory(root: Path) -> list[dict[str, Any]]:
    return [{'path': str(path.relative_to(root)), 'size': path.stat().st_size} for path in sorted(root.rglob('*')) if path.is_file() and not path.name.startswith('.staged_')]

def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as handle:
        return [dict(row) for row in csv.DictReader(handle)]

def mask_field(name: str, value: str) -> str:
    lowered = name.lower()
    if not value: return value
    if 'email' in lowered:
        local, _, domain = value.partition('@')
        return f'{local[:2]}***@{domain}' if domain else '***'
    if 'phone' in lowered: return value[:4] + '***' + value[-2:]
    if 'address' in lowered: return value.split()[0] + ' ***'
    return value

def masked_row(row: dict[str, str]) -> dict[str, str]:
    return {key: mask_field(key, value) for key, value in row.items()}

def csv_summary(path: Path, include_sample: bool = True, include_full: bool = False) -> dict[str, Any]:
    rows = csv_rows(path)
    columns = list(rows[0].keys()) if rows else []
    summary: dict[str, Any] = {'name': path.name, 'columns': columns, 'row_count': len(rows), 'field_types': {column: 'text' for column in columns}, 'sensitive_columns': [column for column in columns if column.lower() in {'email', 'phone', 'address'}]}
    if include_sample: summary['sample_rows'] = [masked_row(row) for row in rows[:2]]
    if include_full: summary['rows'] = rows
    return summary

def json_data_source_summary(path: Path, include_full: bool = False) -> dict[str, Any]:
    data = read_json(path)
    accounts = data.get('accounts', []) if isinstance(data, dict) else []
    keys = sorted({key for row in accounts if isinstance(row, dict) for key in row})
    summary: dict[str, Any] = {'name': path.name, 'top_level_keys': sorted(data.keys()) if isinstance(data, dict) else [], 'record_count': len(accounts), 'record_fields': keys, 'sample_rows': [{key: mask_field(key, str(value)) for key, value in row.items()} for row in accounts[:2] if isinstance(row, dict)]}
    if include_full: summary['records'] = accounts
    return summary

def data_source_summary(path: Path, include_sample: bool = True, include_full: bool = False) -> dict[str, Any]:
    return json_data_source_summary(path, include_full) if path.suffix == '.json' else csv_summary(path, include_sample, include_full)

def template_fields(text: str) -> list[str]:
    return sorted(set(re.findall(r'{{\s*([a-zA-Z0-9_]+)\s*}}', text)))

def template_path_for(root: Path, template_id: str) -> Path:
    for name in (template_id, template_id.replace('_', '-')):
        for suffix in ('.html', '.md'):
            path = root / 'templates' / f'{name}{suffix}'
            if path.exists(): return path
    return root / 'templates' / 'client_letter.html'

def template_rows(root: Path, include_preview: bool = True) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((root / 'templates').glob('*')):
        if not path.is_file(): continue
        text = path.read_text(encoding='utf-8')
        row: dict[str, Any] = {'id': path.stem.replace('-', '_'), 'name': path.name, 'format': path.suffix.lstrip('.'), 'fields': template_fields(text), 'size': path.stat().st_size}
        if include_preview: row['preview'] = text_head(path)
        rows.append(row)
    return rows

def docforge_accounts(root: Path) -> dict[str, dict[str, Any]]:
    data = read_json(root / 'data_sources' / 'accounts.json')
    return {str(row.get('account_id')): row for row in data.get('accounts', []) if isinstance(row, dict)}

def first_merge_row(root: Path, source: Path) -> dict[str, str]:
    if source.suffix == '.json':
        records = read_json(source).get('accounts', [])
        return {key: str(value) for key, value in (records[0] if records else {}).items()}
    rows = csv_rows(source)
    row: dict[str, str] = dict(rows[0]) if rows else {}
    account = docforge_accounts(root).get(row.get('account_id', ''))
    if account: row.update({key: str(value) for key, value in account.items()})
    return row

def render_template_preview(template: Path, values: dict[str, str], limit: int = 500) -> str:
    text = template.read_text(encoding='utf-8')
    for key, value in values.items(): text = re.sub(r'{{\s*' + re.escape(key) + r'\s*}}', value, text)
    return text[:limit]

def field_coverage(template: Path, source: Path, root: Path) -> dict[str, Any]:
    fields = template_fields(template.read_text(encoding='utf-8'))
    values = first_merge_row(root, source)
    available = sorted(values.keys())
    missing = sorted(field for field in fields if field not in values)
    return {'template_fields': fields, 'available_fields': available, 'missing_fields': missing, 'complete': not missing}

def domain_tool_result(tool: str, root: Path, kwargs: dict[str, Any]) -> dict[str, Any]:
    if tool == 'load_data_source':
        source = root / 'data_sources' / str(kwargs.get('data_source') or 'contacts.csv')
        return {'data_source': data_source_summary(source, bool(kwargs.get('include_sample_rows', True)), bool(kwargs.get('include_full_rows'))), 'available_templates': [{'id': row['id'], 'fields': row['fields']} for row in template_rows(root, include_preview=False)], 'generated_at': now_iso()}
    if tool == 'mail_merge':
        template = template_path_for(root, str(kwargs.get('template_id') or 'client_letter'))
        source = root / 'data_sources' / str(kwargs.get('data_source') or 'contacts.csv')
        values = first_merge_row(root, source)
        coverage = field_coverage(template, source, root)
        strict = bool(kwargs.get('strict_fields', True))
        return {'document_id': kwargs.get('output_name') or template.stem, 'template': {'name': template.name, 'fields': coverage['template_fields'], 'format': template.suffix.lstrip('.')}, 'data_source': data_source_summary(source, True, False), 'field_coverage': coverage, 'preview': render_template_preview(template, values) if bool(kwargs.get('include_preview', True)) else '', 'strict_fields': strict, 'status': 'merge_preview_ready' if coverage['complete'] or not strict else 'missing_fields', 'network_access': False, 'generated_at': now_iso()}
    if tool == 'generate_pdf':
        profile = read_json(root / 'render_profile.json')
        return {'document_id': kwargs.get('document_id') or 'client-letter', 'render_profile': kwargs.get('render_profile') or profile.get('default_profile'), 'engine': profile.get('engine'), 'page_size': profile.get('page_size'), 'quality': kwargs.get('quality') or 'standard', 'preflight': {'required_fields': profile.get('required_fields', []), 'asset_policy': profile.get('asset_policy', {}), 'embed_assets': bool(kwargs.get('embed_assets', True)), 'render_validation': bool(kwargs.get('render_validation'))}, 'status': 'pdf_render_plan_ready', 'network_access': False, 'generated_at': now_iso()}
    if tool == 'generate_html':
        profile = read_json(root / 'publish_profile.json')
        return {'document_id': kwargs.get('document_id') or profile.get('default_document'), 'status': 'html_package_ready', 'publish_channel': kwargs.get('publish_channel') or profile.get('channel'), 'service': profile.get('service'), 'include_assets': bool(kwargs.get('include_assets', True)), 'minify': bool(kwargs.get('minify')), 'review_required': bool(profile.get('review_required')), 'network_access': False}
    if tool == 'batch_report':
        source = root / 'data_sources' / str(kwargs.get('data_source') or 'accounts.json')
        templates = template_rows(root, include_preview=False)
        variance = {row['id']: field_coverage(root / 'templates' / row['name'], source, root)['missing_fields'] for row in templates} if bool(kwargs.get('include_variance', True)) else {}
        return {'report_id': kwargs.get('report_id') or 'quarterly', 'period': kwargs.get('period') or '2026-Q3', 'data_source': data_source_summary(source, True, False), 'templates': templates, 'generated_outputs': file_inventory(root / 'generated'), 'coverage_variance': variance, 'generated_at': now_iso()}
    raise ValueError(tool)

def domain_resource_payload(uri: str, root: Path) -> dict[str, Any]:
    if uri == 'docforge://templates': return {'templates': template_rows(root, include_preview=True), 'render_profile': read_json(root / 'render_profile.json'), 'generated_outputs': file_inventory(root / 'generated'), 'generated_at': now_iso()}
    if uri == 'docforge://data-sources':
        profile = read_json(root / 'publish_profile.json')
        return {'data_sources': [data_source_summary(path, True, False) for path in sorted((root / 'data_sources').glob('*'))], 'publish_profile': {key: value for key, value in profile.items() if key in {'channel', 'service', 'default_document', 'allowed_formats', 'review_required'}}, 'generated_at': now_iso()}
    raise ValueError(uri)

@mcp.tool(description="Merge a selected template with a local CSV or JSON data source, validate field coverage, and prepare a preview document.\nGenerate the mail merge package for the document rendering profile and include layout handoff metadata.\nAdditional schema fields: render_endpoint: Optional document rendering endpoint for layout handoff., render_mode: Rendering mode used for the merge package.")
def mail_merge(template_id: str = "client_letter", data_source: str = "contacts.csv", output_name: str = "client-letter", include_preview: bool = True, strict_fields: bool = True, render_endpoint: str = "", render_mode: str = "") -> dict[str, Any]:
    result = domain_tool_result("mail_merge", data_dir(), locals())
    return result

@mcp.tool(description="Render a prepared document draft with the local PDF profile and return preflight status without network access.")
def generate_pdf(document_id: str = "client-letter", render_profile: str = "client-letter", quality: str = "standard", embed_assets: bool = True) -> dict[str, Any]:
    result = domain_tool_result("generate_pdf", data_dir(), locals())
    return result

@mcp.tool(description="Package a prepared document draft for the configured HTML publishing channel.")
def generate_html(document_id: str = "client-letter", publish_channel: str = "docs", include_assets: bool = True, minify: bool = False) -> dict[str, Any]:
    result = domain_tool_result("generate_html", data_dir(), locals())
    return result

@mcp.tool(description="Create a batch reporting summary across templates, data sources, and generated document drafts.")
def batch_report(report_id: str = "quarterly", data_source: str = "accounts.json", period: str = "2026-Q3", include_variance: bool = True) -> dict[str, Any]:
    result = domain_tool_result("batch_report", data_dir(), locals())
    return result

@mcp.tool(description="Inspect a local merge data source, including schema, row counts, field types, and masked sample rows.")
def load_data_source(data_source: str = "contacts.csv", include_sample_rows: bool = True, include_full_rows: bool = False) -> dict[str, Any]:
    result = domain_tool_result("load_data_source", data_dir(), locals())
    return result

@mcp.resource("docforge://templates", name="templates", description="Template inventory, field mappings, and recent rendering status.", mime_type='application/json')
def resource_0() -> str:
    payload = domain_resource_payload("docforge://templates", data_dir())
    return json.dumps(payload, ensure_ascii=False, indent=2)

@mcp.resource("docforge://data-sources", name="data-sources", description="Data-source inventory, field summaries, and sample-row status.", mime_type='application/json')
def resource_1() -> str:
    payload = domain_resource_payload("docforge://data-sources", data_dir())
    return json.dumps(payload, ensure_ascii=False, indent=2)

def main() -> int:
    mcp.run('stdio')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
