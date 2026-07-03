import sys 
import bcrypt 
import jwt 
from datetime import datetime, timedelta,timezone
from pathlib import Path 
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SUPABASE_URL,SUPABASE_SERVICE_KEY,JWT_SECRET,JWT_EXPIRY_HOURS
from src.logger import get_logger 
# pyrefly: ignore [missing-import]
from supabase import create_client


logger = get_logger(__name__)
supabase = create_client(SUPABASE_URL,SUPABASE_SERVICE_KEY)

def hash_password(password:str) ->str :
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password:str,hashed_password:str) ->bool :
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_token(user_id:str,email:str) -> str:
    payload= {
        "user_id":user_id,
        "email":email,
        "iat":datetime.now(tz=timezone.utc),
        "exp":datetime.now(tz=timezone.utc)+timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload,JWT_SECRET,algorithm="HS256")

def verify_token(token:str) -> Tuple[Dict[str,Any],str] | Tuple[None,str] :
    try:
        payload=jwt.decode(token,JWT_SECRET,algorithms=["HS256"])
        return {"Valid":True,"user_id":payload['user_id'],"email":payload['email']},200
    except jwt.ExpiredSignatureError:
        return None,"Token expired",401
    except jwt.InvalidTokenError:
        return None,"Invalid token",401

def register_user(email:str,password:str,full_name:str) -> Dict[str,Any]:
    logger.info(f"Registering new user with email: {email}")
    if not email or not password or not full_name:
        return {"error":"Email, password and fullname are required"},400
    try:
        hashed_password=hash_password(password)
        response=supabase.table("users").select("id").eq("email",email).execute()
        if response.data:
            return {"error":"User already exists"},400
        response=supabase.table("users").insert({"email":email,"password":hashed_password,"full_name":full_name}).execute()
        return {"message":"User registered successfully"},200
    except Exception as e:
        return {"error":str(e)},500
        

def login(email:str,password:str) -> Dict[str,Any]:
    if not email or not password:
        return {"error":"Email and password are required"},400
    try:
        response=supabase.table("users").select("id,email,password").eq("email",email).execute()
        if not response.data:
            return {"error":"User not found"},404
        user=response.data[0]
        if not verify_password(password,user["password"]):
            return {"error":"Invalid password"},401
        token=create_token(user["id"],user["email"])
        return {
            "success":True,
            "token":token,
            "user":{"id":user["id"],"email":user["email"],"full_name":user["full_name"]},
            "message":"Login successful"
        }
    except Exception as e:
        return {"error":str(e)},500