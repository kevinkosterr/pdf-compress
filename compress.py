"""PDF compression: recompress embedded images with Pillow, then rewrite the
file with pikepdf using compressed object streams."""

import io
import zlib

import pikepdf
from PIL import Image
from pikepdf import Name, PdfImage

PRESETS = {
    # name: (max image dimension in px, JPEG quality)
    "low": (2400, 85),
    "medium": (1600, 70),
    "high": (1000, 50),
}


def _recompress_image(pdf: pikepdf.Pdf, raw: pikepdf.Stream, max_dim: int, quality: int) -> None:
    # Leave stencil masks and tiny images alone
    if raw.get("/ImageMask", False):
        return
    try:
        pil = PdfImage(raw).as_pil_image()
    except Exception:
        return  # unsupported colorspace / filter, skip

    if pil.width * pil.height < 64 * 64:
        return

    if max(pil.size) > max_dim:
        pil.thumbnail((max_dim, max_dim), Image.LANCZOS)

    is_gray = pil.mode in ("L", "1", "LA")
    pil = pil.convert("L" if is_gray else "RGB")

    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=quality, optimize=True)
    data = buf.getvalue()

    if len(data) >= len(raw.read_raw_bytes()):
        return  # not worth it

    raw.write(data, filter=Name.DCTDecode)
    raw.Width, raw.Height = pil.width, pil.height
    raw.ColorSpace = Name.DeviceGray if is_gray else Name.DeviceRGB
    raw.BitsPerComponent = 8
    for key in ("/DecodeParms", "/Decode"):
        if key in raw:
            del raw[key]

    # Keep a soft mask (transparency) matching the new size
    smask = raw.get("/SMask")
    if smask is not None:
        try:
            mask = PdfImage(smask).as_pil_image().convert("L")
            if mask.size != pil.size:
                mask = mask.resize(pil.size, Image.LANCZOS)
            smask.write(zlib.compress(mask.tobytes()), filter=Name.FlateDecode)
            smask.Width, smask.Height = pil.width, pil.height
            smask.ColorSpace = Name.DeviceGray
            smask.BitsPerComponent = 8
            if "/DecodeParms" in smask:
                del smask["/DecodeParms"]
        except Exception:
            pass


def compress_pdf(data: bytes, level: str = "medium") -> bytes:
    max_dim, quality = PRESETS.get(level, PRESETS["medium"])
    seen: set[tuple[int, int]] = set()

    with pikepdf.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            for raw in _page_images(page):
                if raw.objgen in seen:
                    continue
                seen.add(raw.objgen)
                _recompress_image(pdf, raw, max_dim, quality)

        pdf.remove_unreferenced_resources()
        out = io.BytesIO()
        pdf.save(
            out,
            compress_streams=True,
            recompress_flate=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
        )

    result = out.getvalue()
    # Never return something bigger than what we got
    return result if len(result) < len(data) else data


def _page_images(page: pikepdf.Page):
    # get_images() (pikepdf >= 10) also finds images nested in form XObjects
    if hasattr(page, "get_images"):
        return page.get_images().values()
    return page.images.values()
