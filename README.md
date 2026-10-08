# pdf-compress

Tiny FastAPI app: drop a PDF on the page, get a compressed PDF back.

Compression uses [pikepdf](https://pikepdf.readthedocs.io/) and Pillow: embedded
images are downscaled and re-encoded as JPEG, then the file is rewritten with
compressed streams and object streams. No external binaries needed.

## Run

```bash
uv run uvicorn main:app --reload
```

Open http://127.0.0.1:8000.

Levels: `low` (light, 2400px / q85), `medium` (1600px / q70), `high` (1000px / q50).
If the result isn't smaller, the original is returned unchanged.

## API

```bash
curl -F file=@input.pdf -F level=medium http://127.0.0.1:8000/compress -o out.pdf
```
