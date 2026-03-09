# Node Mapping — Complete 42-Type Reference

## Mapping Levels

| Icon | Level | Meaning |
|------|-------|---------|
| 🟢 | **Direct** | 1:1 mapping, minimal transformation |
| 🟡 | **Partial** | Mapping exists but config format differs |
| 🔵 | **Mode Change** | Structural transformation required |
| 🔴 | **Unmappable** | No Dify equivalent, requires workaround |
| ⚪ | **Skipped** | No logic, safe to ignore |

---

## Full Mapping Table

| # | Coze Node | Coze ID | Dify Node | Level | Notes |
|---|-----------|---------|-----------|-------|-------|
| 1 | Entry | 1 | `start` | 🟢 Direct | |
| 2 | Exit | 2 | `end` | 🟢 Direct | |
| 3 | LLM | 3 | `llm` | 🟡 Partial | Prompt template format differs; function calling config needs conversion |
| 4 | Plugin | 4 | `tool` | 🟡 Partial | Tool provider must be manually re-bound |
| 5 | CodeRunner | 5 | `code` | 🟡 Partial | Python maps directly; JS/TS → Node.js |
| 6 | KnowledgeRetriever | 6 | `knowledge-retrieval` | 🟡 Partial | Dataset IDs differ |
| 7 | Selector | 8 | `if-else` | 🟡 Partial | Operator format differs (int→string); branch ports need remapping |
| 8 | SubWorkflow | 9 | `tool` (workflow-as-tool) | 🔵 Mode Change | Must publish as Dify app first, then configure as tool |
| 9 | OutputEmitter | 13 | `answer` | 🟢 Direct | |
| 10 | TextProcessor | 15 | `template-transform` / `code` | 🟡 Partial | Concatenation → Jinja2 template; splitting → Code node |
| 11 | QuestionAnswer | 18 | `human-input` | 🟡 Partial | |
| 12 | VariableAssigner | 20/40 | `assigner` | 🟢 Direct | |
| 13 | Loop | 21 | `loop` / `iteration` | 🔵 Mode Change | Array traversal → iteration; counted loop → loop |
| 14 | IntentDetector | 22 | `question-classifier` | 🟡 Partial | |
| 15 | KnowledgeIndexer | 27 | `knowledge-index` | 🟢 Direct | |
| 16 | Batch | 28 | `iteration` (parallel) | 🔵 Mode Change | Maps to parallel iteration |
| 17 | Continue | 29 | — | 🔴 Unmappable | Dify Loop has no continue; needs conditional branch workaround |
| 18 | Comment | 31 | — | ⚪ Skipped | Visual-only annotation, no logic |
| 19 | VariableAggregator | 32 | `variable-aggregator` | 🟢 Direct | |
| 20 | HTTPRequester | 45 | `http-request` | 🟡 Partial | Auth config format differs |
| 21 | JsonSerialization | 58 | `code` | 🟢 Direct | Generates `json.dumps()` code |
| 22 | JsonDeserialization | 59 | `code` | 🟢 Direct | Generates `json.loads()` code |
| 23–42 | Conversation/DB nodes | 38–57 | `http-request` / `datasource` / `code` | 🟡–🔴 Varies | No direct equivalents; generated as HTTP requests calling Dify API or custom code |

---

## Unmappable Nodes — Workarounds

### Continue (ID: 29)
Dify's Loop node does not support `continue`. Workaround: wrap the remaining loop body in an `if-else` node that skips when the continue condition is met.

### Conversation Management (IDs: 38–57)
These Coze-specific nodes manage conversation state (create/update/delete conversations, messages, etc.). Dify has no equivalent. Workaround: generate `http-request` nodes that call the Dify API for conversation operations.

### Database Nodes (IDs: 12, 42–46)
Partial mapping to Dify's `datasource` node (if available) or `code` node with direct SQL via Python.
