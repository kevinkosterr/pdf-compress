from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, StreamingResponse

from compress import PRESETS, compress_pdf

STATIC = Path(__file__).parent / "static"
MAX_UPLOAD = 200 * 1024 * 1024  # 200 MB

app = FastAPI(title="PDF Compress")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/compress")
async def compress(file: UploadFile = File(...), level: str = Form("medium")):
    if level not in PRESETS:
        raise HTTPException(400, f"level must be one of {list(PRESETS)}")

    data = await file.read()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "File too large")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "Not a PDF file")

    try:
        result = await run_in_threadpool(compress_pdf, data, level)
    except Exception as e:
        raise HTTPException(422, f"Could not process PDF: {e}")

    stem = Path(file.filename or "document.pdf").stem
    chunk = 64 * 1024
    return StreamingResponse(
        (result[i : i + chunk] for i in range(0, len(result), chunk)),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{stem}-compressed.pdf"',
            "Content-Length": str(len(result)),
            "X-Original-Size": str(len(data)),
            "X-Compressed-Size": str(len(result)),
            "Access-Control-Expose-Headers": "X-Original-Size, X-Compressed-Size",
        },
    )
