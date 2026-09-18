---
name: jev-memory-selector
description: Selects retrieved memories that actually fit the current query and token budget. Use when an agent already retrieved many memories and must keep only the ones worth sending.
---

# JEV Memory Selector

Call the `memory_select` MCP tool. Do not put API keys in the tool arguments.

Required arguments: `query`, `memories`.

`JEV_PROVIDER` defaults to `local`. The tool ranks or filters candidates. It does not generate user-facing text and it does not execute the selected item.

Keys stay in the process environment.
