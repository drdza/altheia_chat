import os
from typing import List
import pandas as pd
from docx import Document
from PyPDF2 import PdfReader


def load_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def load_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])


def load_excel(path: str) -> str:
    df = pd.read_excel(path, sheet_name=None)  # todas las hojas
    texts = []
    for sheet, data in df.items():
        texts.append(data.astype(str).apply(" ".join, axis=1).str.cat(sep="\n"))
    return "\n".join(texts)


def load_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".txt", ".md"]:
        return load_txt(path)
    elif ext == ".docx":
        return load_docx(path)
    elif ext == ".pdf":
        return load_pdf(path)
    elif ext in [".xls", ".xlsx"]:
        return load_excel(path)
    else:
        raise ValueError(f"Formato no soportado: {ext}")
