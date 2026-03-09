from fastapi import APIRouter, File, UploadFile

router = APIRouter()


@router.post("/coze")
async def validate_coze(file: UploadFile = File(...)):
    try:
        content = await file.read()
        from core.coze.parser import CozeParser
        parser = CozeParser()
        fmt = "yaml" if file.filename and file.filename.endswith((".yaml", ".yml")) else "json"
        ir = parser.parse_file(content, fmt)
        return {"valid": True, "node_count": len(ir.nodes), "edge_count": len(ir.edges)}
    except Exception as e:
        return {"valid": False, "error": str(e)}


@router.post("/dify")
async def validate_dify(file: UploadFile = File(...)):
    try:
        content = await file.read()
        import yaml
        data = yaml.safe_load(content)
        has_graph = "workflow" in data and "graph" in data.get("workflow", {})
        return {"valid": has_graph, "version": data.get("version", "unknown")}
    except Exception as e:
        return {"valid": False, "error": str(e)}
