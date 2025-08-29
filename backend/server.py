from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT and Password settings
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff" 
    USER = "user"

class RequestStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DENIED = "denied"

class RequestType(str, Enum):
    INCIDENT_REPORT = "incident_report"
    POLICE_REPORT = "police_report"
    BODY_CAM_FOOTAGE = "body_cam_footage"
    CASE_FILE = "case_file"
    OTHER = "other"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.USER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class RecordRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    request_type: RequestType
    status: RequestStatus = RequestStatus.PENDING
    assigned_staff_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    priority: str = "medium"

class RecordRequestCreate(BaseModel):
    title: str
    description: str
    request_type: RequestType
    priority: str = "medium"

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    sender_id: str
    sender_name: str
    sender_role: UserRole
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MessageCreate(BaseModel):
    request_id: str
    content: str

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif hasattr(value, 'value'):  # Handle Enum values
                data[key] = value.value if hasattr(value, 'value') else str(value)
    return data

# Auth Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    del user_dict["password"]
    
    new_user = User(**user_dict)
    user_doc = prepare_for_mongo(new_user.dict())
    user_doc["hashed_password"] = hashed_password
    
    await db.users.insert_one(user_doc)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer", user=new_user)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_obj = User(**user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_obj.id}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user_obj)

# Request Routes
@api_router.post("/requests", response_model=RecordRequest)
async def create_request(request_data: RecordRequestCreate, current_user: User = Depends(get_current_user)):
    request_dict = request_data.dict()
    request_dict["user_id"] = current_user.id
    
    new_request = RecordRequest(**request_dict)
    request_doc = prepare_for_mongo(new_request.dict())
    
    await db.requests.insert_one(request_doc)
    
    # Create notification for admins
    admin_users = await db.users.find({"role": "admin"}).to_list(None)
    for admin in admin_users:
        notification = Notification(
            user_id=admin["id"],
            title="New Request Submitted",
            message=f"New request '{new_request.title}' submitted by {current_user.full_name}"
        )
        await db.notifications.insert_one(prepare_for_mongo(notification.dict()))
    
    return new_request

@api_router.get("/requests", response_model=List[RecordRequest])
async def get_requests(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        # Admins see all requests
        requests = await db.requests.find().to_list(None)
    elif current_user.role == UserRole.STAFF:
        # Staff see assigned requests and unassigned requests
        requests = await db.requests.find({
            "$or": [
                {"assigned_staff_id": current_user.id},
                {"assigned_staff_id": None}
            ]
        }).to_list(None)
    else:
        # Users see only their own requests
        requests = await db.requests.find({"user_id": current_user.id}).to_list(None)
    
    return [RecordRequest(**req) for req in requests]

@api_router.get("/requests/{request_id}", response_model=RecordRequest)
async def get_request(request_id: str, current_user: User = Depends(get_current_user)):
    request = await db.requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_obj = RecordRequest(**request)
    
    # Check permissions
    if current_user.role == UserRole.USER and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == UserRole.STAFF and request_obj.assigned_staff_id != current_user.id and request_obj.assigned_staff_id is not None:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return request_obj

@api_router.put("/requests/{request_id}/assign")
async def assign_request(request_id: str, staff_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can assign requests")
    
    # Update request
    await db.requests.update_one(
        {"id": request_id},
        {"$set": {"assigned_staff_id": staff_id, "status": "assigned", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Create notification for assigned staff
    staff_user = await db.users.find_one({"id": staff_id})
    if staff_user:
        notification = Notification(
            user_id=staff_id,
            title="Request Assigned",
            message=f"You have been assigned a new request"
        )
        await db.notifications.insert_one(prepare_for_mongo(notification.dict()))
    
    return {"message": "Request assigned successfully"}

# Message Routes
@api_router.post("/messages", response_model=Message)
async def create_message(message_data: MessageCreate, current_user: User = Depends(get_current_user)):
    # Verify user has access to this request
    request = await db.requests.find_one({"id": message_data.request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_obj = RecordRequest(**request)
    
    # Check permissions
    if (current_user.role == UserRole.USER and request_obj.user_id != current_user.id) or \
       (current_user.role == UserRole.STAFF and request_obj.assigned_staff_id != current_user.id and request_obj.assigned_staff_id is not None):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
    
    new_message = Message(
        request_id=message_data.request_id,
        sender_id=current_user.id,
        sender_name=current_user.full_name,
        sender_role=current_user.role,
        content=message_data.content
    )
    
    await db.messages.insert_one(prepare_for_mongo(new_message.dict()))
    return new_message

@api_router.get("/messages/{request_id}", response_model=List[Message])
async def get_messages(request_id: str, current_user: User = Depends(get_current_user)):
    # Verify access to request
    request = await db.requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_obj = RecordRequest(**request)
    
    # Check permissions
    if (current_user.role == UserRole.USER and request_obj.user_id != current_user.id) or \
       (current_user.role == UserRole.STAFF and request_obj.assigned_staff_id != current_user.id and request_obj.assigned_staff_id is not None):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
    
    messages = await db.messages.find({"request_id": request_id}).sort("created_at", 1).to_list(None)
    return [Message(**msg) for msg in messages]

# Notification Routes
@api_router.get("/notifications", response_model=List[Notification])
async def get_notifications(current_user: User = Depends(get_current_user)):
    notifications = await db.notifications.find({"user_id": current_user.id}).sort("created_at", -1).to_list(None)
    return [Notification(**notif) for notif in notifications]

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"is_read": True}}
    )
    return {"message": "Notification marked as read"}

# Dashboard Routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        total_requests = await db.requests.count_documents({})
        pending_requests = await db.requests.count_documents({"status": "pending"})
        completed_requests = await db.requests.count_documents({"status": "completed"})
        total_users = await db.users.count_documents({"role": "user"})
        
        return {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "completed_requests": completed_requests,
            "total_users": total_users
        }
    elif current_user.role == UserRole.STAFF:
        assigned_requests = await db.requests.count_documents({"assigned_staff_id": current_user.id})
        completed_by_me = await db.requests.count_documents({
            "assigned_staff_id": current_user.id,
            "status": "completed"
        })
        
        return {
            "assigned_requests": assigned_requests,
            "completed_requests": completed_by_me
        }
    else:
        my_requests = await db.requests.count_documents({"user_id": current_user.id})
        pending_requests = await db.requests.count_documents({
            "user_id": current_user.id,
            "status": {"$in": ["pending", "assigned", "in_progress"]}
        })
        
        return {
            "total_requests": my_requests,
            "pending_requests": pending_requests
        }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()