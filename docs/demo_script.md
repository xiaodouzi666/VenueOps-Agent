# 3-Minute Demo Script

## 0:00-0:20 Problem

Event venues and retail malls fail during peaks because too many signals arrive at once: crowd density, queues, stockouts, incidents, staffing, and tenant requests. Operators need an agent that can convert fragmented data into safe actions.

## 0:20-0:45 Architecture

VenueOps Agent is built for Google Cloud and MongoDB. Cloud Run hosts the app. Gemini on Google Cloud Agent Platform is the reasoning layer. MongoDB Atlas stores operational data, SOPs, actions, and agent memory. MongoDB MCP provides agentic database access.

## 0:45-1:30 Live Mission

Type:

```text
Kickoff is in 75 minutes. Keep fans moving, avoid stockouts, and handle facility incidents.
```

Show the tool trace:

- `mongodb.collection-schema telemetry`
- `mongodb.aggregate telemetry`
- `mongodb.find inventory`
- `mongodb.find staff_shifts`
- `mongodb.count incidents`
- `mongodb.aggregate sop_docs`
- `create_pending_action`

## 1:30-2:15 Approval

Show five actions:

1. Move four stewards to Gate B.
2. Redirect arrivals from Gate B to Gate D.
3. Restock water.
4. Assign facility team to restroom incident.
5. Draft tenant campaign for Retail Wing East.

Approve two actions and show executed status.

## 2:15-2:45 Before / After

Show heatmap and KPI changes: Gate B pressure and wait time improve; stockout risk falls after restock.

## 2:45-3:00 Close

This is not a chat-only dashboard. It is an agentic operations loop with MongoDB operational data, SOP retrieval, MCP trace, human approval, and audit memory.
