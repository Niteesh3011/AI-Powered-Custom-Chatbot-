import os
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify
from flask_cors import CORS

from src.Rag_chain import get_rag_chain
from src.auth import register_user, login, verify_token
from src.chat_db import get_user_sessions, get_session_messages, create_session, save_message
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
    # Verify token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized. Please log in."}), 401
    token = auth_header.split(" ")[1]
    decoded, msg, status = verify_token(token)
    if status != 200:
        return jsonify({"error": msg}), status

    if not rag_chain:
        return jsonify({"error": "Medical RAG chain is not initialized on the server."}), 500

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    query = data['query']
    session_id = data.get('session_id')
    chat_history_raw = data.get('chat_history', [])
    
    # If no session_id is provided, create a new one
    if not session_id:
        title = query[:50] + "..." if len(query) > 50 else query
        new_session = create_session(decoded['user_id'], title=title)
        if new_session:
            session_id = new_session['id']
            
    # Save user message
    if session_id:
        save_message(session_id, 'user', query)
    
    # Format chat history into tuples (human, ai) for LangChain
    chat_history = []
    current_human = None
    for msg in chat_history_raw:
        if msg.get('role') == 'user':
            current_human = msg.get('content')
        elif msg.get('role') == 'bot' and current_human:
            chat_history.append((current_human, msg.get('content')))
            current_human = None

    logger.info(f"Received query: {query} with {len(chat_history)} history turns")

    try:
        response = rag_chain.invoke({
            "question": query,
            "chat_history": chat_history
        })
        answer = response.get("answer", "I'm sorry, I could not generate a response.")
        
        # Extract sources to return them to the frontend
        sources = []
        for doc in response.get("source_documents", []):
            sources.append({
                "page": doc.metadata.get("page"),
                "source": doc.metadata.get("source")
            })

        # Save AI message
        if session_id:
            save_message(session_id, 'bot', answer, sources=sources)

        return jsonify({
            "response": answer,
            "sources": sources,
            "session_id": session_id
        })
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401
    decoded, msg, status = verify_token(auth_header.split(" ")[1])
    if status != 200:
        return jsonify({"error": msg}), status
        
    sessions = get_user_sessions(decoded['user_id'])
    return jsonify({"sessions": sessions})

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401
    decoded, msg, status = verify_token(auth_header.split(" ")[1])
    if status != 200:
        return jsonify({"error": msg}), status
        
    messages = get_session_messages(session_id)
    return jsonify({"messages": messages})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "rag_chain_loaded": rag_chain is not None})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    result, status_code = login(email, password)
    return jsonify(result), status_code

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    result, status_code = register_user(email, password, full_name)
    return jsonify(result), status_code

if __name__ == '__main__':
    logger.info(f"Starting Flask server on port {FLASK_PORT}...")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=FLASK_DEBUG)
