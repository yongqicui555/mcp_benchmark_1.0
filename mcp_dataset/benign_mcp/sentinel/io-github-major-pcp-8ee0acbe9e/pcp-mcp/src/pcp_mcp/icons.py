"""Centralized icons and tags for MCP components."""

from __future__ import annotations

from mcp.types import Icon

ICON_METRICS = Icon(src="data:,📊", mimeType="text/plain")
ICON_SEARCH = Icon(src="data:,🔍", mimeType="text/plain")
ICON_INFO = Icon(src="data:,📋", mimeType="text/plain")
ICON_SYSTEM = Icon(src="data:,💻", mimeType="text/plain")
ICON_PROCESS = Icon(src="data:,⚙️", mimeType="text/plain")
ICON_HEALTH = Icon(src="data:,💚", mimeType="text/plain")
ICON_CATALOG = Icon(src="data:,📚", mimeType="text/plain")
ICON_NAMESPACE = Icon(src="data:,🗂️", mimeType="text/plain")
ICON_DIAGNOSE = Icon(src="data:,🔬", mimeType="text/plain")
ICON_CPU = Icon(src="data:,🖥️", mimeType="text/plain")
ICON_MEMORY = Icon(src="data:,🧠", mimeType="text/plain")
ICON_DISK = Icon(src="data:,💾", mimeType="text/plain")
ICON_NETWORK = Icon(src="data:,🌐", mimeType="text/plain")
ICON_FILESYSTEM = Icon(src="data:,📁", mimeType="text/plain")

TAGS_METRICS = {"metrics", "pcp"}
TAGS_SYSTEM = {"system", "monitoring", "performance"}
TAGS_PROCESS = {"processes", "monitoring"}
TAGS_HEALTH = {"health", "status", "summary"}
TAGS_CATALOG = {"catalog", "reference", "documentation"}
TAGS_DISCOVERY = {"discovery", "namespace", "exploration"}
TAGS_CPU = {"cpu", "troubleshooting", "performance"}
TAGS_MEMORY = {"memory", "troubleshooting", "performance"}
TAGS_DISK = {"disk", "io", "troubleshooting", "performance"}
TAGS_NETWORK = {"network", "troubleshooting", "performance"}
TAGS_DIAGNOSE = {"diagnosis", "troubleshooting", "workflow"}
TAGS_FILESYSTEM = {"filesystem", "storage", "disk", "capacity"}
TAGS_NETWORK_STATS = {"network", "tcp", "udp", "protocol", "troubleshooting"}
