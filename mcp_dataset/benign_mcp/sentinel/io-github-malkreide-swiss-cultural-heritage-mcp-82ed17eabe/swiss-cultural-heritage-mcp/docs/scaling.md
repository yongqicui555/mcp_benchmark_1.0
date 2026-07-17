# Scaling & Session Affinity

This document records the horizontal-scaling posture of `swiss-cultural-heritage-mcp` and the prerequisites for running more than one instance. It addresses audit findings **SCALE-002** (stateful load balancing) and **SCALE-003** (`Mcp-Session-Id` edge routing).

## Current posture: single-instance by constraint

**The server must run as a single instance** in the Streamable-HTTP deployment (Render / Docker). This is a deliberate, documented constraint — not an oversight.

- **stdio mode** (Claude Desktop, `uvx`, local) is unaffected: there is one client per process and no load balancer.
- **Streamable-HTTP mode** maintains a per-client **session** keyed by the `Mcp-Session-Id` header. The official MCP SDK's session manager holds this state **in process** (the SSE event stream, the session's initialization state). The server's *tool logic* is fully stateless — there is no database and no cache — but the *transport session* is not.

### Why >1 instance breaks without affinity

If the service is scaled to N > 1 instances behind a normal round-robin load balancer:

1. The client opens a session on instance A and receives an `Mcp-Session-Id`.
2. A follow-up request (or the SSE GET stream) is balanced to instance B.
3. Instance B has never seen that session id → it returns `404 / 400`, and the stream breaks mid-conversation.

This is the failure mode behind both SCALE-002 (from the application/session view) and SCALE-003 (from the load-balancer view).

### Session TTL

The session lives for the duration of the client connection and is reclaimed when the client disconnects or the SSE stream closes; there is no long-lived server-side persistence. Operators terminating idle connections at the edge should use an idle timeout **≥** the expected gap between a client's requests (a few minutes is typical) so that active sessions are not severed.

## Path to horizontal scaling

Before scaling beyond one instance, adopt **one** of the following. Until then, keep the instance count pinned to **1** (Render: do not enable autoscaling; k8s: `replicas: 1`).

### Variant A — sticky sessions at the edge (SCALE-003)

Have the load balancer hash/stick on the `Mcp-Session-Id` header and route every request for a session to the same backend. Set the stick-table TTL ≈ the idle session timeout, and **test backend failover**: when a backend dies, its sessions are gone (there is no shared state), so the client must re-initialize — verify the client recovers gracefully rather than hanging.

HAProxy (stick-table on the header):

```haproxy
backend mcp
    stick-table type string len 64 size 100k expire 30m
    stick on req.hdr(Mcp-Session-Id)
    server s1 10.0.0.11:8080 check
    server s2 10.0.0.12:8080 check
```

Nginx (consistent hash on the header):

```nginx
upstream mcp {
    hash $http_mcp_session_id consistent;
    server 10.0.0.11:8080;
    server 10.0.0.12:8080;
}
```

> Affinity alone does **not** survive a backend failure — a re-homed session is a lost session. Variant A is appropriate when occasional re-initialization on failover is acceptable.

### Variant B — shared session backend

Replace the in-process session store with a shared backend (e.g. Redis, or Cloudflare Durable Objects on Workers) so that **any** instance can serve **any** session. This removes the affinity requirement entirely and survives instance failure, at the cost of a stateful dependency. This is the right choice if the deployment needs true elastic autoscaling or zero-downtime rolling deploys.

## Resource sizing

Independent of instance count, size each instance for the `heritage_cross_search` fan-out (three concurrent upstream connections). See the resource-limits and file-descriptor recommendations in [`security.md`](security.md#resource-limits-scale-006).

## Verification

Re-run the `SCALE-002` and `SCALE-003` checks from the mcp-audit-skill catalog after adopting Variant A or B. The single-instance constraint above is the accepted interim state and is reflected in the deployment configuration (one instance, autoscaling off).
