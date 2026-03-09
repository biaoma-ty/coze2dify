from __future__ import annotations

from core.ir.types import IRNodeType, MappingStatus


class MappingRule:
    def __init__(self, ir_type: IRNodeType, dify_type: str, status: MappingStatus, notes: str = ""):
        self.ir_type = ir_type
        self.dify_type = dify_type
        self.status = status
        self.notes = notes


MAPPING_RULES: dict[IRNodeType, MappingRule] = {
    IRNodeType.START: MappingRule(IRNodeType.START, "start", MappingStatus.MAPPED),
    IRNodeType.END: MappingRule(IRNodeType.END, "end", MappingStatus.MAPPED),
    IRNodeType.LLM: MappingRule(IRNodeType.LLM, "llm", MappingStatus.PARTIAL, "Prompt template format differs"),
    IRNodeType.CODE: MappingRule(IRNodeType.CODE, "code", MappingStatus.PARTIAL, "JS/TS -> Node.js"),
    IRNodeType.HTTP_REQUEST: MappingRule(IRNodeType.HTTP_REQUEST, "http-request", MappingStatus.PARTIAL, "Auth config differs"),
    IRNodeType.CONDITION: MappingRule(IRNodeType.CONDITION, "if-else", MappingStatus.PARTIAL, "Operator format differs"),
    IRNodeType.LOOP_COUNTED: MappingRule(IRNodeType.LOOP_COUNTED, "loop", MappingStatus.PARTIAL, "Pattern change"),
    IRNodeType.LOOP_ARRAY: MappingRule(IRNodeType.LOOP_ARRAY, "iteration", MappingStatus.PARTIAL, "Pattern change"),
    IRNodeType.LOOP_INFINITE: MappingRule(IRNodeType.LOOP_INFINITE, "loop", MappingStatus.PARTIAL, "Max count workaround"),
    IRNodeType.BATCH: MappingRule(IRNodeType.BATCH, "iteration", MappingStatus.PARTIAL, "Parallel iteration"),
    IRNodeType.KNOWLEDGE_RETRIEVAL: MappingRule(IRNodeType.KNOWLEDGE_RETRIEVAL, "knowledge-retrieval", MappingStatus.PARTIAL, "Dataset IDs differ"),
    IRNodeType.KNOWLEDGE_WRITE: MappingRule(IRNodeType.KNOWLEDGE_WRITE, "knowledge-index", MappingStatus.MAPPED),
    IRNodeType.KNOWLEDGE_DELETE: MappingRule(IRNodeType.KNOWLEDGE_DELETE, "http-request", MappingStatus.PARTIAL, "HTTP workaround"),
    IRNodeType.PLUGIN: MappingRule(IRNodeType.PLUGIN, "tool", MappingStatus.PARTIAL, "Manual tool rebinding required"),
    IRNodeType.SUB_WORKFLOW: MappingRule(IRNodeType.SUB_WORKFLOW, "tool", MappingStatus.PARTIAL, "Workflow-as-tool pattern"),
    IRNodeType.VARIABLE_AGGREGATOR: MappingRule(IRNodeType.VARIABLE_AGGREGATOR, "variable-aggregator", MappingStatus.MAPPED),
    IRNodeType.VARIABLE_ASSIGNER: MappingRule(IRNodeType.VARIABLE_ASSIGNER, "assigner", MappingStatus.MAPPED),
    IRNodeType.TEXT_PROCESSOR: MappingRule(IRNodeType.TEXT_PROCESSOR, "template-transform", MappingStatus.PARTIAL, "Jinja2 template"),
    IRNodeType.OUTPUT_EMITTER: MappingRule(IRNodeType.OUTPUT_EMITTER, "answer", MappingStatus.MAPPED),
    IRNodeType.INTENT_DETECTOR: MappingRule(IRNodeType.INTENT_DETECTOR, "question-classifier", MappingStatus.PARTIAL),
    IRNodeType.QUESTION_ANSWER: MappingRule(IRNodeType.QUESTION_ANSWER, "human-input", MappingStatus.PARTIAL),
    IRNodeType.INPUT_RECEIVER: MappingRule(IRNodeType.INPUT_RECEIVER, "human-input", MappingStatus.PARTIAL),
    IRNodeType.JSON_SERIALIZE: MappingRule(IRNodeType.JSON_SERIALIZE, "code", MappingStatus.MAPPED, "json.dumps()"),
    IRNodeType.JSON_DESERIALIZE: MappingRule(IRNodeType.JSON_DESERIALIZE, "code", MappingStatus.MAPPED, "json.loads()"),
    IRNodeType.CONVERSATION_OP: MappingRule(IRNodeType.CONVERSATION_OP, "http-request", MappingStatus.PARTIAL, "HTTP workaround"),
    IRNodeType.MESSAGE_OP: MappingRule(IRNodeType.MESSAGE_OP, "http-request", MappingStatus.PARTIAL, "HTTP workaround"),
    IRNodeType.DATABASE_QUERY: MappingRule(IRNodeType.DATABASE_QUERY, "code", MappingStatus.PARTIAL, "Code node workaround"),
    IRNodeType.DATABASE_INSERT: MappingRule(IRNodeType.DATABASE_INSERT, "code", MappingStatus.PARTIAL),
    IRNodeType.DATABASE_UPDATE: MappingRule(IRNodeType.DATABASE_UPDATE, "code", MappingStatus.PARTIAL),
    IRNodeType.DATABASE_DELETE: MappingRule(IRNodeType.DATABASE_DELETE, "code", MappingStatus.PARTIAL),
    IRNodeType.DATABASE_CUSTOM_SQL: MappingRule(IRNodeType.DATABASE_CUSTOM_SQL, "code", MappingStatus.PARTIAL),
    IRNodeType.COMMENT: MappingRule(IRNodeType.COMMENT, "", MappingStatus.SKIPPED, "Visual only"),
    IRNodeType.BREAK: MappingRule(IRNodeType.BREAK, "", MappingStatus.PARTIAL, "Handled within loop"),
    IRNodeType.CONTINUE: MappingRule(IRNodeType.CONTINUE, "", MappingStatus.UNMAPPABLE, "No Dify equivalent"),
    IRNodeType.UNKNOWN: MappingRule(IRNodeType.UNKNOWN, "code", MappingStatus.UNMAPPABLE, "Placeholder code node"),
}
