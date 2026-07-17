# Tomcat MCP (Model Context Protocol Server)

[![npm version](https://img.shields.io/npm/v/@sarath-451/tomcat-mcp)](https://www.npmjs.com/package/@sarath-451/tomcat-mcp)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-blue)](https://registry.modelcontextprotocol.io)

A local **Tomcat management MCP server** for **Kiro IDE** that enables AI-assisted
operations such as:

- Start / stop Tomcat
- Diagnose startup failures
- Deploy and rollback WAR files
- Read and analyze logs
- Take thread dumps and heap dumps
- Analyze GC logs
- Detect Windows service installations

This MCP runs **locally** and never exposes Tomcat over the network.

---

## 🌍 Available in MCP Registry

Tomcat MCP is officially published to the **MCP Registry** and npm.

**Registry name:**
io.github.sarath-451/tomcat-mcp

**npm package:**
@sarath-451/tomcat-mcp

Search via Registry API:
https://registry.modelcontextprotocol.io/v0.1/servers?search=tomcat

---


## 🚀 One-Click Install (Kiro IDE)



> Make sure you have cloned this repository and installed dependencies first.



[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=Tomcat%20MCP&config=%7B%22command%22%3A%22node%22%2C%22args%22%3A%5B%22index.js%22%5D%2C%22disabled%22%3Afalse%2C%22autoApprove%22%3A%5B%22start_tomcat%22%2C%22stop_tomcat%22%2C%22check_tomcat_status%22%2C%22read_latest_catalina_log%22%2C%22diagnose_startup_failure%22%2C%22deploy_war%22%2C%22rollback_last_deployment%22%2C%22thread_dump%22%2C%22heap_dump%22%2C%22analyze_gc_log%22%2C%22detect_tomcat_service%22%5D%7D)



---



## 📦 Requirements



\- \*\*Node.js 18+\*\*

\- \*\*Java JDK\*\* (required for `jcmd`, thread dumps, heap dumps)

\- Apache Tomcat (9 / 10 / 10.1 tested)

\- Windows (Linux support planned)



Check:

```bat

node -v

java -version

jcmd -h



