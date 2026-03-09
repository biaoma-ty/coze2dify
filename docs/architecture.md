# Architecture

## Conversion Pipeline

```
Data Sources (pick one)                        Output Targets (pick one)
┌─────────────┐                              ┌──────────────────┐
│ JSON/YAML   │──┐                       ┌──→│ Dify DSL YAML    │
│ File Upload  │  │                       │   │ (file download)   │
├─────────────┤  │                       │   ├──────────────────┤
│ Coze API    │──┼→ CozeParser → IR ──→ DifyGenerator ──┤
│ Online Fetch │  │       │         │        │   ├──────────────────┤
├─────────────┤  │  CozeValidator  IRValidator  └──→│ Dify PostgreSQL  │
│ Coze DB     │──┘                           │ DB Direct-Write   │
│ Direct Read  │                              └──────────────────┘
└─────────────┘
```

### Why IR (Intermediate Representation)?

- **Decoupled** — Coze parsing and Dify generation are fully independent
- **Extensible** — Adding LangFlow, Flowise etc. only requires a new Parser/Generator
- **Testable** — Each layer can be tested in isolation
- **Multi-IO** — Parser only cares about "how to read", Generator only cares about "how to write"

---

## IR Data Model

### Core Types

```python
class IRNodeType(str, Enum):
    START = "start"
    END = "end"
    LLM = "llm"
    CODE = "code"
    HTTP_REQUEST = "http_request"
    CONDITION = "condition"
    LOOP_COUNTED = "loop_counted"
    LOOP_ARRAY = "loop_array"
    LOOP_INFINITE = "loop_infinite"
    BATCH = "batch"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    KNOWLEDGE_WRITE = "knowledge_write"
    PLUGIN = "plugin"
    SUB_WORKFLOW = "sub_workflow"
    VARIABLE_AGGREGATOR = "variable_aggregator"
    VARIABLE_ASSIGNER = "variable_assigner"
    TEXT_PROCESSOR = "text_processor"
    QUESTION_ANSWER = "question_answer"
    INTENT_DETECTOR = "intent_detector"
    OUTPUT_EMITTER = "output_emitter"
    DATABASE_QUERY = "database_query"
    CONVERSATION_OP = "conversation_op"
    MESSAGE_OP = "message_op"
    UNKNOWN = "unknown"
```

### Variable Reference Model

```python
class IRVariableRef(BaseModel):
    source_node_id: str
    field_name: str
    nested_path: list[str] = []
    source_type: Literal["node_output", "global_app", "global_system", "global_user"]
    needs_array_drill_down: bool = False

class IRNode(BaseModel):
    id: str
    node_type: IRNodeType
    title: str
    inputs: list[IRVariable]
    outputs: list[IRVariable]
    config: dict[str, Any]
    error_handling: IRErrorHandling
    children: list["IRNode"] = []
    child_edges: list[IREdge] = []
    branches: list[IRBranch] = []

class IRWorkflow(BaseModel):
    id: str
    name: str
    mode: Literal["workflow", "chatflow"]
    nodes: list[IRNode]
    edges: list[IREdge]
    global_variables: list[IRVariable]
```

---

## Variable Reference Transform

```
Coze: BlockInputReference{blockID:"100001", name:"output", path:["detail","name"], source:"block-output"}
  ↓
IR:   IRVariableRef{source_node_id:"100001", field_name:"output", nested_path:["detail","name"]}
  ↓
Dify: variable_selector: ["100001", "output", "detail", "name"]
      Template syntax: {{#100001.output.detail.name#}}
```

**Array auto drill-down**: When Coze iterates over an array field it automatically accesses `[0]`. Dify needs an explicit List Operator or Code node inserted.

---

## Compound Node Flattening

Coze's Loop/Batch nodes embed child nodes (`Blocks[]`). Dify places all nodes at the top level, using `isInLoop` / `isInIteration` flags.

**Algorithm:**
1. Extract `children` from compound nodes → promote to top-level DifyNode
2. Extract `child_edges` → promote to top-level DifyEdge with `isInLoop=true`
3. Generate container nodes (loop/iteration) and connect child nodes

---

## Condition Operator Mapping

Coze uses integer enums (1–16), Dify uses strings. Length comparison operators (`LengthGreaterThan` etc.) have no Dify equivalent — a preceding Code node computing `len()` is inserted.

---

## Edge / Connection Mapping

Coze edges are distributed across three locations (`Canvas.Edges`, `Node.Edges`, `Blocks.Edges`). Dify uses a single flat list. CozeParser collects and merges from all three.

Branch port mapping:
- Coze: `"true"`, `"true_1"`, `"false"` → Dify: `case_id`, `"false"`
- Coze: `"exception"` → Dify: `"fail-branch"`
