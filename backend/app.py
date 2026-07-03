import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from src.Rag_chain import get_rag_chain
from src.logger import get_logger
from config import FLASK_PORT, FLASK_DEBUG, FLASK_SECRET_KEY

logger = get_logger(__name__)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
CORS(app)  # Enable CORS for all routes to allow Next.js frontend to communicate

# Initialize the RAG chain globally so it's loaded once on startup
logger.info("Initializing RAG chain on startup...")
try:
    rag_chain = get_rag_chain()
    logger.info("RAG chain successfully initialized.")
except Exception as e:
    logger.error(f"Failed to initialize RAG chain: {e}")
    rag_chain = None

@app.route('/api/chat', methods=['POST'])
def chat():
    if not rag_chain:
        return jsonify({"error": "Medical RAG chain is not initialized on the server."}), 500

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    query = data['query']
    logger.info(f"Received query: {query}")

    try:
        response = rag_chain.invoke({"query": query})
        answer = response.get("result", "I'm sorry, I could not generate a response.")
        
        # Extract sources to return them to the frontend
        sources = []
        for doc in response.get("source_documents", []):
            sources.append({
                "page": doc.metadata.get("page"),
                "source": doc.metadata.get("source")
            })

        return jsonify({
            "response": answer,
            "sources": sources
        })
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "rag_chain_loaded": rag_chain is not None})

if __name__ == '__main__':
    logger.info(f"Starting Flask server on port {FLASK_PORT}...")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=FLASK_DEBUG)
