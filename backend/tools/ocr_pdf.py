# backend/tools/ocr_pdf.py
import pdfplumber
import pytesseract
from PIL import Image
import os
import io
import pandas as pd

def extract_text_from_pdf(path: str) -> str:
    """
    Use pdfplumber to extract text; fall back to OCR on images if needed.
    """
    text_chunks = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                if txt.strip():
                    text_chunks.append(txt)
                else:
                    # fallback: render page to image and OCR (slow)
                    pil = page.to_image(resolution=150).original
                    ocr_txt = pytesseract.image_to_string(pil)
                    if ocr_txt.strip():
                        text_chunks.append(ocr_txt)
    except Exception as e:
        # as last resort try OCR on entire file if pdfplumber failed
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(path, dpi=150)
            for pil in pages:
                text_chunks.append(pytesseract.image_to_string(pil))
        except Exception:
            pass
    return "\n\n".join(text_chunks)

def extract_tables_from_pdf(path: str) -> list:
    """
    Extract tables as pandas DataFrames using pdfplumber's table extraction.
    Returns list of DataFrames.
    """
    tables = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                try:
                    pg_tables = page.extract_tables()
                    for tab in pg_tables:
                        # convert table (list of rows) to DataFrame if plausible
                        df = pd.DataFrame(tab[1:], columns=tab[0]) if len(tab) > 1 else None
                        if df is not None:
                            tables.append(df)
                except Exception:
                    continue
    except Exception:
        pass
    return tables
