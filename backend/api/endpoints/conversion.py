from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response

from core.engine.converter import ConversionEngine

router = APIRouter()
engine = ConversionEngine()

# In-memory store for conversion results (replace with DB in production)
_conversions: dict[str, dict] = {}
_counter = 0


@router.post("")
async def convert_workflow(file: UploadFile = File(...)):
    global _counter
    content = await file.read()
    fmt = "yaml" if file.filename and file.filename.endswith((".yaml", ".yml")) else "json"

    dsl, report = engine.convert_from_json(content, fmt)
    _counter += 1
    conversion_id = str(_counter)

    yaml_output = engine.dify_generator.to_yaml(dsl)
    _conversions[conversion_id] = {
        "dsl": dsl.model_dump(),
        "yaml": yaml_output,
        "report": report.model_dump(),
    }

    return {"conversion_id": conversion_id, "report": report.model_dump()}


@router.get("/{conversion_id}")
async def get_conversion(conversion_id: str):
    data = _conversions.get(conversion_id)
    if not data:
        return {"error": "Conversion not found"}
    return {"dsl": data["dsl"], "report": data["report"]}


@router.get("/{conversion_id}/dsl")
async def download_dsl(conversion_id: str):
    data = _conversions.get(conversion_id)
    if not data:
        return {"error": "Conversion not found"}
    return Response(
        content=data["yaml"],
        media_type="application/x-yaml",
        headers={"Content-Disposition": f"attachment; filename=workflow_{conversion_id}.yml"},
    )


@router.get("/{conversion_id}/report")
async def get_report(conversion_id: str):
    data = _conversions.get(conversion_id)
    if not data:
        return {"error": "Conversion not found"}
    return data["report"]


@router.post("/{conversion_id}/write-to-dify")
async def write_to_dify(conversion_id: str):
    # TODO: Implement DifyDbWriter
    return {"status": "not_implemented"}
