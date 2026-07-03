import sys
import time
from pathlib import Path
from typing import List, Optional

# pyrefly: ignore [missing-import]
from langchain_huggingface import HuggingFaceEmbeddings
# pyrefly: ignore [missing-import]
from langchain_core.documents import Document
# pyrefly: ignore [missing-import]
from pinecone import Pinecone as PineconeClient, ServerlessSpec
# pyrefly: ignore [missing-import]
from langchain_pinecone import PineconeVectorStore

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    RETRIEVER_TOP_K,
)
from src.logger import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 100


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Load and return the HuggingFace embedding model.
    Uses GPU (CUDA) when available, otherwise falls back to CPU.
    """
    # pyrefly: ignore [missing-import]
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL} (device={device})")

    model_name = EMBEDDING_MODEL.split("/")[-1]
    model_path = Path(__file__).parent / "models" / model_name

    # Use local path if cached, otherwise pull from hub
    resolved_name = str(model_path) if model_path.exists() else EMBEDDING_MODEL

    embeddings = HuggingFaceEmbeddings(
        model_name=resolved_name,
        model_kwargs={"trust_remote_code": True, "device": device},
        encode_kwargs={"batch_size": BATCH_SIZE, "normalize_embeddings": True},
    )
    logger.info(f"Embedding model loaded successfully on {device}")
    return embeddings


def _get_pinecone_client() -> PineconeClient:
    """Return an authenticated Pinecone client."""
    return PineconeClient(api_key=PINECONE_API_KEY)


def ensure_index_exists(pc: PineconeClient) -> None:
    """
    Create the Pinecone index if it doesn't already exist.
    If it exists but with the wrong dimension, delete and recreate it.
    Blocks until the index reports ready.
    """
    existing_names = pc.list_indexes().names()
    if PINECONE_INDEX_NAME in existing_names:
        desc = pc.describe_index(PINECONE_INDEX_NAME)
        if desc.dimension == EMBEDDING_DIMENSION:
            logger.info(f"Using existing Pinecone index: {PINECONE_INDEX_NAME}")
            return
        logger.warning(
            f"Index dimension mismatch: existing={desc.dimension}, "
            f"expected={EMBEDDING_DIMENSION}. Recreating index..."
        )
        pc.delete_index(PINECONE_INDEX_NAME)
        # Wait for deletion to propagate
        while PINECONE_INDEX_NAME in pc.list_indexes().names():
            time.sleep(1)

    logger.info(f"Creating Pinecone index: {PINECONE_INDEX_NAME} (dim={EMBEDDING_DIMENSION})")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT),
    )
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(1)
    logger.info("Pinecone index created successfully")


def upsert_documents(chunks: List[Document]) -> Optional[PineconeVectorStore]:
    """
    Upsert document chunks into Pinecone in batches.
    Uses retries with exponential backoff to handle transient network drops.
    Returns the resulting vector store, or None if all batches fail.
    """
    pc = _get_pinecone_client()
    ensure_index_exists(pc)
    embeddings = get_embedding_model()

    logger.info(f"Upserting {len(chunks)} documents into Pinecone")
    batches = [chunks[i : i + BATCH_SIZE] for i in range(0, len(chunks), BATCH_SIZE)]

    vectorstore: Optional[PineconeVectorStore] = None
    for i, batch in enumerate(tqdm(batches, desc="Uploading")):
        max_retries = 5
        success = False
        for attempt in range(1, max_retries + 1):
            try:
                if vectorstore is None:
                    vectorstore = PineconeVectorStore.from_documents(
                        documents=batch,
                        embedding=embeddings,
                        index_name=PINECONE_INDEX_NAME,
                    )
                else:
                    vectorstore.add_documents(batch)
                
                success = True
                logger.info(
                    f"Upserted batch {i + 1}/{len(batches)} ({len(batch)} documents)"
                )
                break
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt}/{max_retries} failed to upsert batch {i + 1}: {e}"
                )
                if attempt < max_retries:
                    sleep_time = 2 ** attempt
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(
                        f"Failed to upsert batch {i + 1} after {max_retries} attempts."
                    )

    logger.info(f"Finished upserting {len(chunks)} documents into Pinecone")
    return vectorstore


def load_existing_vectorstore() -> Optional[PineconeVectorStore]:
    """
    Connect to an existing Pinecone index and return it as a
    LangChain vector store, or None on failure.
    """
    try:
        logger.info("Loading existing vectorstore from Pinecone...")
        embeddings = get_embedding_model()
        vectorstore = PineconeVectorStore.from_existing_index(
            embedding=embeddings,
            index_name=PINECONE_INDEX_NAME,
        )
        logger.info("Vectorstore loaded successfully")
        return vectorstore
    except Exception as e:
        logger.warning(f"Failed to load existing vectorstore: {e}")
        return None

def get_retriever(vectorStore: Optional[PineconeVectorStore] = None):
    """
    Return a similarity retriever backed by the Pinecone index.
    Loads the existing vectorstore when none is provided.
    """
    if vectorStore is None:
        vectorStore = load_existing_vectorstore()
    if vectorStore is None:
        raise RuntimeError(
            "No vectorstore available. Upsert documents before querying."
        )
    return vectorStore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_TOP_K},
    )
    
def get_index_stats() -> dict:
    """Return dimension, vector count, and namespace info for the index."""
    pc = _get_pinecone_client()
    index = pc.Index(PINECONE_INDEX_NAME)
    stats = index.describe_index_stats()
    return {
        "dimension": stats.dimension,
        "total_vector_count": stats.total_vector_count,
        "namespaces": dict(stats.namespaces),
    }


if __name__ == "__main__":
    import argparse
    from src.ingestion import load_and_chunk

    default_pdf = str(
        Path(__file__).resolve().parent.parent / "data"
        / "The-Gale-Encyclopedia-of-Medicine.pdf"
    )

    parser = argparse.ArgumentParser(description="Ingest a PDF into Pinecone")
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default=default_pdf,
        help="Path to the PDF file (default: Gale Encyclopedia in data/)",
    )
    args = parser.parse_args()

    logger.info(f"Starting ingestion pipeline for: {args.pdf_path}")

    # 1. Load & chunk
    chunks = load_and_chunk(args.pdf_path)
    if not chunks:
        logger.error("No chunks produced — aborting upload.")
        sys.exit(1)

    logger.info(f"Produced {len(chunks)} chunks, beginning Pinecone upsert...")

    # 2. Upsert to Pinecone
    vectorstore = upsert_documents(chunks)
    if vectorstore is None:
        logger.error("All upsert batches failed.")
        sys.exit(1)

    # 3. Print stats
    stats = get_index_stats()
    logger.info(f"Upload complete — Index stats: {stats}")
