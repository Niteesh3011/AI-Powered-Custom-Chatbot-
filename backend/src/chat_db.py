import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from src.logger import get_logger
from supabase import create_client

logger = get_logger(__name__)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_user_sessions(user_id: str) -> List[Dict[str, Any]]:
    """Fetch all chat sessions for a specific user, ordered by updated_at descending."""
    try:
        response = supabase.table("chat_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
        return response.data
    except Exception as e:
        logger.exception(f"Error fetching user sessions for {user_id}")
        return []

def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """Fetch all messages for a specific session, ordered by create_at ascending."""
    try:
        response = supabase.table("messages").select("*").eq("session_id", session_id).order("create_at").execute()
        return response.data
    except Exception as e:
        logger.exception(f"Error fetching session messages for {session_id}")
        return []

def create_session(user_id: str, title: str = "New Chat") -> Optional[Dict[str, Any]]:
    """Create a new chat session for a user."""
    try:
        response = supabase.table("chat_sessions").insert({
            "user_id": user_id,
            "title": title
        }).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.exception(f"Error creating session for {user_id}")
        return None

def save_message(session_id: str, role: str, content: str, sources: Optional[List[Dict[str, Any]]] = None, duration_ms: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Save a single message to the database."""
    try:
        data = {
            "session_id": session_id,
            "role": role,
            "content": content
        }
        if sources is not None:
            data["sources"] = sources
        if duration_ms is not None:
            data["duration_ms"] = duration_ms
            
        response = supabase.table("messages").insert(data).execute()
        
        # Also update the session's updated_at timestamp
        supabase.table("chat_sessions").update({"updated_at": "now()"}).eq("id", session_id).execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.exception(f"Error saving message for session {session_id}")
        return None
