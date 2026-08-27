# 把不同类型的文件转换为纯文本
from fastapi import UploadFile
from PyPDF2 import PdfReader
from docx import Document
import io


async def extract_text_from_file(file: UploadFile) -> str:
    suffix = file.filename.lower().split(".")[-1]
    bytes_data = await file.read()
    stream = io.BytesIO(bytes_data)

    text = ""

    if suffix == "txt":
        text = stream.read().decode("utf-8")

    elif suffix == "pdf":
        reader = PdfReader(stream)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    elif suffix == "docx":
        doc = Document(stream)
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        raise ValueError(f"不支持的文件类型：.{suffix}, 仅支持 txt / pdf / docx")

    if not text.strip():
        raise ValueError("解析后文档文本为空")

    return text
