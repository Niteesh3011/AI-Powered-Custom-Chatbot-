import sys 
from pathlib import Path
from typing import Any, Dict, List 

# pyrefly: ignore [missing-import]
from langchain.chains import RetrievalQA 
# pyrefly: ignore [missing-import]
from langchain_core.prompts import PromptTemplate 
# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI 

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    OPENAI_API_KEY,
    OPENAI_LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_TOKENS_RESPONSE,
)
from src.logger import get_logger
from src.vector_store import get_retriever

logger = get_logger(__name__)

# Medical chatbot prompt template
PROMPT_TEMPLATE = """You are a highly knowledgeable, empathetic, and professional medical AI assistant.
Your goal is to provide accurate and helpful answers to the user's health-related questions based STRICTLY on the medical literature context provided below.

Rules:
1. Base your response ONLY on the provided context. If the context does not contain the answer, state clearly that you do not know or that the provided documentation doesn't cover it. Do not make up information.
2. Be professional and objective.
3. Structure your response clearly using paragraphs, bullet points, or numbered lists where appropriate.
4. IMPORTANT: Always include a brief disclaimer at the end of your response stating: "Disclaimer: This information is for educational purposes and is not a substitute for professional medical advice. Always consult a healthcare provider for diagnosis or treatment."

CONTEXT FROM GALE ENCYCLOPEDIA : 
________________________________
{context}
________________________________
Question:
{question}

Answer:"""

def get_llm() -> ChatOpenAI:
    """
    Initialize and return the ChatOpenAI client.
    Automatically routes to Hugging Face Inference API if the API key is a Hugging Face token.
    """
    base_url = None
    if OPENAI_API_KEY.startswith("hf_"):
        base_url = "https://router.huggingface.co/v1"
        logger.info(f"Routing ChatOpenAI to Hugging Face Inference API (model={OPENAI_LLM_MODEL})")
    else:
        logger.info(f"Routing ChatOpenAI to OpenAI API (model={OPENAI_LLM_MODEL})")

    return ChatOpenAI(
        model=OPENAI_LLM_MODEL,
        openai_api_key=OPENAI_API_KEY,
        base_url=base_url,
        temperature=LLM_TEMPERATURE,
        max_tokens=MAX_TOKENS_RESPONSE,
    )

def get_rag_chain() -> RetrievalQA:
    """
    Construct and return the medical RAG chain.
    """
    logger.info("Initializing medical RAG chain...")
    llm = get_llm()
    retriever = get_retriever()

    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )
    logger.info("RAG chain initialized successfully")
    return chain

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test query the Medical ChatBot RAG chain")
    parser.add_argument(
        "query", 
        nargs="?", 
        default="What is maleria?", 
        help="The query to ask the chatbot"
    )
    args = parser.parse_args()
    
    try:
        chain = get_rag_chain()
        print(f"\nAsking: '{args.query}'\n")
        response = chain.invoke({"query": args.query})
        
        print("--- ANSWER ---")
        print(response.get("result"))
        print("\n--- SOURCES ---")
        for idx, doc in enumerate(response.get("source_documents", [])):
            print(f"[{idx+1}] Page {doc.metadata.get('page')} ({doc.metadata.get('source')})")
            
    except Exception as e:
        logger.error(f"Failed to run query: {e}")
        sys.exit(1)