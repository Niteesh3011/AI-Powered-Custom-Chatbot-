import re
import sys
from pathlib import Path 
from typing import List 
# pyrefly: ignore [missing-import]
from langchain_core.documents import Document
# pyrefly: ignore [missing-import]
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Prefer pymupdf (faster, handles corrupted PDFs better)
try:
    # pyrefly: ignore [missing-import]
    import fitz  # pymupdf
    _USE_FITZ = True
except ImportError:
    # pyrefly: ignore [missing-import]
    from pypdf import PdfReader
    _USE_FITZ = False

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))

from src.logger import get_logger
from config import CHUNK_SIZE,CHUNK_OVERLAP

logger = get_logger(__name__)

def clean_text(text:str) -> str:
    """
    Clean up raw extracted PDF text
    """
    if not text:
        return ""
    else:
        text = text.replace("\r\n","\n").replace("\r","\n").replace("\n\n","\n").replace("\n ","\n").replace(" \n","\n")
        text = re.sub(r"\n{3,}","\n\n",text)
        text = re.sub(r"^\s+\d+\s+$","",text,flags=re.MULTILINE)
        text = re.sub(r"^\s{2,}","",text,flags=re.MULTILINE)
        text = text.replace("\u2013","-").replace("\u2014","--")
        text = text.replace("\u201c",'"').replace("\u201d",'"').replace("\u2018","'").replace("\u2019","'")
        text = re.sub(r"[\t]{2,}"," ",text)
        text = text.strip()
        return text 

def _load_pdf_fitz(path: Path) -> List[Document]:
    """Extract text using pymupdf (fitz) — fast and robust."""
    doc = fitz.open(str(path))
    total_pages = len(doc)
    logger.info(f"Total pages: {total_pages} (using pymupdf)")

    documents = []
    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text("text")
        clean = clean_text(text)
        if len(clean) < 50:
            continue
        documents.append(Document(
            page_content=clean,
            metadata={
                "source": path.name,
                "page": page_num + 1,
                "total_pages": total_pages,
                "file_size": path.stat().st_size,
                "file_path": str(path),
            }
        ))
    doc.close()
    return documents

def _load_pdf_pypdf(path: Path) -> List[Document]:
    """Extract text using pypdf — fallback parser."""
    reader = PdfReader(str(path))
    total_pages = len(reader.pages)
    logger.info(f"Total pages: {total_pages} (using pypdf)")

    documents = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        clean = clean_text(text)
        if len(clean) < 50:
            continue
        documents.append(Document(
            page_content=clean,
            metadata={
                "source": path.name,
                "page": page_num,
                "total_pages": total_pages,
                "file_size": path.stat().st_size,
                "file_path": str(path),
            }
        ))
    return documents

def load_pdf(pdf_path: str) -> List[Document]:
    """
    Extract text from a PDF file.
    Uses pymupdf if available, otherwise falls back to pypdf.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")    
    
    logger.info(f"Loading PDF: {path.name}")
    
    if _USE_FITZ:
        document = _load_pdf_fitz(path)
    else:
        document = _load_pdf_pypdf(path)
    
    if not document:
        logger.warning(f"No text extracted from: {path.name}")
        return []
    
    logger.info(f"Extracted {len(document)} pages from {path.name}")
    return document


def chunk_document(document: List[Document]) -> List[Document]:
    """
    Chunk a list of documents into smaller chunks.
    """
    if not document:
        logger.warning("No documents to chunk")
        return []

    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " ",""],
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_documents(document)
    logger.info(f"Chunked {len(document)} documents into {len(chunks)} chunks")

    if not chunks:
        logger.warning("Splitter produced zero chunks")
        return []

    for i, chunk in enumerate(chunks):
        chunk.metadata['chunk_id'] = i
        chunk.metadata['char_count'] = len(chunk.page_content)

    avg = sum(c.metadata['char_count'] for c in chunks) // len(chunks)
    logger.info(f"Avg chunk size: {avg} chars")
    return chunks 

def load_and_chunk(pdf_path: str) -> List[Document]:
    """
    Load a PDF file and chunk it into smaller chunks.
    """
    pages = load_pdf(pdf_path)
    chunks = chunk_document(pages)
    return chunks  

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    args = parser.parse_args()
    chunks = load_and_chunk(args.pdf_path)
    for chunk in chunks:
        print(chunk)
        print("\n")