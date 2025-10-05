---
mode: ask
---
# Heartbeat Strategy with Agent/Orchestrator Plugins

## Overview

The heartbeat mechanism will be implemented as a coordinated system of **events**, **plugins**, and an enhanced **EventStore**.  
The goal is to ensure that each agent periodically signals its liveness to the Orchestrator, and the Orchestrator checks these signals to detect failures.

---

## Events

- **AgentEvent.AGENT_HEARTBEAT**  
  Emitted by agents at regular intervals.  

- **OrchestratorEvent.AGENT_HEARTBEAT**  
  Registered when the Orchestrator receives a heartbeat from an agent.  

- **OrchestratorEvent.AGENT_HEARTBEAT_MISSED**  
  Emitted when the Orchestrator determines that an agent has not sent heartbeats within the allowed timeout.

---

## EventStore Extension

The EventStore will be enhanced to support a **pinned view** of the latest events per agent and type:

- Heartbeat events will not be stored only in the ring buffer but also in a fixed memory index:  
  `(event_type, agent) -> last N events` (default: 1).  
- API additions:
  - `latest(type="AGENT_HEARTBEAT", agent="A") -> EventRecord | None`
  - `latest_all_agents(type="AGENT_HEARTBEAT") -> dict[agent, EventRecord]`

This provides **O(1) access** to the last heartbeat for each agent, avoiding redundant structures.

---

## Agent Plugin: AgentHeartbeatTimerPlugin

**Purpose:**  
Send heartbeat events periodically, independent of the agent’s execution cycle.

**Responsibilities:**
- Start a lightweight timer after `AGENT_READY`.
- Emit `AGENT_HEARTBEAT` every configured interval.
- Stop when the agent terminates.

**Parameters:**
- `enabled: bool`
- `send_every: float` (default: `heartbeat_timeout_sec * 0.8`)
- `jitter: float` (optional, to desynchronize many agents)

**Behavior Sketch:**
```python
while not self.stop_event.is_set():
    self.emit_status(event_name=AgentEvent.AGENT_HEARTBEAT.value)
    sleep(send_every * jitter_factor)
```

---

## Orchestrator Plugin: OrchestratorHeartbeatMonitorPlugin

**Purpose:**  
Check the EventStore for agent heartbeats and detect liveness failures.

**Responsibilities:**
- Periodically scan EventStore for the latest heartbeat of each agent.
- Apply timeout and grace rules.
- Emit `AGENT_HEARTBEAT_MISSED` for agents that exceed the limits.
- Optionally trigger restart policy.

**Parameters:**
- `enabled: bool`
- `heartbeat_timeout_sec: float`
- `grace_misses: int`
- `check_interval_sec: float` (default: `timeout / 2`)

**Algorithm:**
1. For each agent:
   - Get last heartbeat from EventStore.
   - If missing or older than `timeout`:
     - Increment `misses`.
     - If `misses > grace`: emit `AGENT_HEARTBEAT_MISSED`.
   - If a new heartbeat arrives after missed → reset and optionally emit `AGENT_ALIVE_AGAIN`.

---

## Workflow

1. **Agent emits heartbeat:**  
   Agent → MessageChannel → Orchestrator.  

2. **Orchestrator records heartbeat:**  
   Orchestrator stores in EventStore (ring + pinned index) and emits `AGENT_HEARTBEAT`.

3. **Monitor plugin check:**  
   Periodically scans pinned heartbeats to verify liveness.  

4. **Missed heartbeat:**  
   Emits `AGENT_HEARTBEAT_MISSED`, updates state, and optionally restarts the agent.  

---

## Parameters Summary

**AgentHeartbeatTimerPlugin**
- `enabled`
- `send_every`
- `jitter`

**OrchestratorHeartbeatMonitorPlugin**
- `enabled`
- `heartbeat_timeout_sec`
- `grace_misses`
- `check_interval_sec`

**EventStore**
- `pinned_specs=[("AGENT_HEARTBEAT", 1)]`
- APIs: `latest`, `latest_all_agents`

---

## Acceptance Criteria

- If the **agent plugin** is active, the agent emits `AGENT_HEARTBEAT` periodically, independent of its work cycle.  
- If the **orchestrator plugin** is active, the Orchestrator detects missed heartbeats and emits `AGENT_HEARTBEAT_MISSED`.  
- EventStore exposes last heartbeat events in O(1).  
- If no plugins are present, no heartbeat logic is executed.  
