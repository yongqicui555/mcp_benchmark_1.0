Name:           python-pcp-mcp
Version:        1.3.2
Release:        1%{?dist}
Summary:        MCP server for Performance Co-Pilot metrics

License:        MIT
URL:            https://github.com/major/pcp-mcp
Source:         %{pypi_source pcp_mcp}

BuildArch:      noarch
BuildRequires:  python3-devel

# Required for uv_build backend
BuildRequires:  python3-uv-build

# PCP runtime dependency
Requires:       pcp

%global _description %{expand:
MCP server for Performance Co-Pilot (PCP) metrics. Query system performance
metrics via the Model Context Protocol - CPU, memory, disk I/O, network,
processes, and more.

This package provides an MCP server that exposes PCP metrics through the
Model Context Protocol, enabling LLM applications like Claude to query
system performance data. It connects to PCP's pmproxy REST API to fetch
metrics from local or remote hosts.

Key features:
- System snapshots (CPU, memory, disk, network, load)
- Process monitoring (top by CPU, memory, or I/O)
- Metric search and discovery
- Remote host monitoring via pmproxy}

%description %_description


%package -n python3-pcp-mcp
Summary:        %{summary}

# Allow users to install by CLI name: dnf install pcp-mcp
Provides:       pcp-mcp = %{version}-%{release}

%description -n python3-pcp-mcp %_description


%prep
%autosetup -p1 -n pcp_mcp-%{version}


%generate_buildrequires
# Build-system deps only (-N skips runtime dep generation).
# Test deps (fastmcp, respx, pytest-asyncio) aren't packaged for Fedora,
# so %check is skipped here. CI handles testing via GitHub Actions.
%pyproject_buildrequires -N


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -l pcp_mcp


%files -n python3-pcp-mcp -f %{pyproject_files}
%doc README.md
%{_bindir}/pcp-mcp


%changelog
* Thu Feb 05 2026 Major Hayden <major@mhtx.net> - 1.3.2-1
- Initial package
