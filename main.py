from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import fitz
import os

app = FastAPI()

@app.get("/health")
def health():
    return {
        "ok": True,
        "git": os.getenv("RENDER_GIT_COMMIT"),
        "repo": os.getenv("RENDER_GIT_REPO_SLUG"),
    }

@app.post("/meta")
async def meta(pdf: UploadFile = File(...)):
    data = await pdf.read()
    doc = fitz.open(stream=data, filetype="pdf")
    return {"pageCount": doc.page_count}

@app.post("/render")
async def render(page: int, dpi: int = 200, pdf: UploadFile = File(...)):
    if page < 1:
        raise HTTPException(400, "page must be >= 1")
    data = await pdf.read()
    doc = fitz.open(stream=data, filetype="pdf")
    if page > doc.page_count:
        raise HTTPException(400, "page out of range")
    p = doc.load_page(page - 1)
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = p.get_pixmap(matrix=mat, alpha=False)
    return Response(content=pix.tobytes("png"), media_type="image/png")

@app.post("/text")
async def text(pdf: UploadFile = File(...)):
    data = await pdf.read()
    doc = fitz.open(stream=data, filetype="pdf")

    pages = []
    full = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        t = page.get_text("text")
        pages.append({"page": i + 1, "text": t})
        full.append(t)

    return {"pageCount": doc.page_count, "text": "\n".join(full), "pages": pages}



@app.route('/split', methods=['POST'])
def split_pdf():
    import fitz, io
    from flask import request, send_file

    pdf_file = request.files['pdf']
    start = int(request.form['start_page'])  # 0-indexed
    end = int(request.form['end_page'])      # 0-indexed, inclusive

    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=start, to_page=end)

    pdf_bytes = new_doc.tobytes()
    new_doc.close()
    doc.close()

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        download_name='split.pdf'
    )


    