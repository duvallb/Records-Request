from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse
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
import aiofiles
import aiosmtplib
from email.message import EmailMessage
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import pandas as pd
from jinja2 import Template
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT and Password settings
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Email settings
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@police.gov")

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

class FileUpload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    filename: str
    original_name: str
    file_size: int
    content_type: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RecordRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    request_type: RequestType
    status: RequestStatus = RequestStatus.PENDING
    assigned_staff_id: Optional[str] = None
    assigned_staff_name: Optional[str] = None
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    priority: str = "medium"
    files: List[FileUpload] = []

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

class AnalyticsData(BaseModel):
    total_requests: int
    requests_by_status: dict
    requests_by_type: dict
    requests_by_priority: dict
    average_resolution_time: float
    monthly_trends: List[dict]
    staff_workload: List[dict]

class RequestAssignment(BaseModel):
    request_id: str
    staff_id: str

class StaffUser(BaseModel):
    id: str
    full_name: str
    email: str
    assigned_requests: int
    completed_requests: int

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
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
    return data

# Email functions
async def send_email(to_email: str, subject: str, content: str, html_content: str = None):
    """Send email notification"""
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            print(f"📧 Email would be sent to {to_email}")
            print(f"📧 Subject: {subject}")
            print(f"📧 Content: {content}")
            print("=" * 50)
            return True  # Skip actual sending in development
            
        message = EmailMessage()
        message["From"] = FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(content)
        
        if html_content:
            message.add_alternative(html_content, subtype="html")
        
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

async def send_new_request_notification(request: RecordRequest, user: User):
    """Send notification when new request is created"""
    subject = f"New Records Request: {request.title}"
    content = f"""
    A new records request has been submitted.
    
    Request Details:
    - Title: {request.title}
    - Type: {request.request_type.replace('_', ' ').title()}
    - Priority: {request.priority.title()}
    - Submitted by: {user.full_name}
    - Submitted at: {request.created_at.strftime('%Y-%m-%d %H:%M')}
    
    Please log in to the Police Records Portal to review and assign this request.
    """
    
    # Send to all admins with valid email addresses
    admin_users = await db.users.find({"role": "admin"}).to_list(None)
    for admin in admin_users:
        # Skip fake/example email addresses
        admin_email = admin.get("email", "")
        if admin_email and not admin_email.endswith("@example.com") and "@" in admin_email:
            try:
                await send_email(admin_email, subject, content)
                logger.info(f"New request notification sent to admin: {admin_email}")
            except Exception as e:
                logger.error(f"Failed to send email to admin {admin_email}: {str(e)}")
        else:
            logger.warning(f"Skipping notification to admin with invalid email: {admin_email}")

async def send_assignment_notification(request: RecordRequest, staff_user: dict):
    """Send notification when request is assigned to staff"""
    subject = f"Request Assigned: {request.title}"
    content = f"""
    You have been assigned a new records request.
    
    Request Details:
    - Title: {request.title}
    - Type: {request.request_type.replace('_', ' ').title()}
    - Priority: {request.priority.title()}
    - Request ID: {request.id}
    
    Please log in to the Police Records Portal to review and process this request.
    """
    
    staff_email = staff_user.get("email", "")
    if staff_email and not staff_email.endswith("@example.com") and "@" in staff_email:
        try:
            await send_email(staff_email, subject, content)
            logger.info(f"Assignment notification sent to staff: {staff_email}")
        except Exception as e:
            logger.error(f"Failed to send assignment email to {staff_email}: {str(e)}")
    else:
        logger.warning(f"Skipping assignment notification to staff with invalid email: {staff_email}")

async def send_status_update_notification(request: RecordRequest, user: dict, old_status: str, new_status: str):
    """Send notification when request status changes"""
    subject = f"Request Update: {request.title}"
    content = f"""
    Your records request status has been updated.
    
    Request Details:
    - Title: {request.title}
    - Previous Status: {old_status.replace('_', ' ').title()}
    - New Status: {new_status.replace('_', ' ').title()}
    - Request ID: {request.id}
    
    Please log in to the Police Records Portal to view the latest updates.
    """
    
    await send_email(user["email"], subject, content)

# PDF Generation function (keeping existing implementation)
def generate_request_pdf(request_data: dict, user_data: dict, messages: List[dict] = None):
    """Generate PDF report for a request"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Police Department Records Request", title_style))
    story.append(Spacer(1, 20))
    
    # Request Information
    story.append(Paragraph("Request Information", styles['Heading2']))
    
    request_info = [
        ["Request ID:", request_data['id'][:8] + "..."],
        ["Title:", request_data['title']],
        ["Type:", request_data['request_type'].replace('_', ' ').title()],
        ["Priority:", request_data['priority'].title()],
        ["Status:", request_data['status'].replace('_', ' ').title()],
        ["Submitted:", request_data['created_at'][:19]],
        ["Last Updated:", request_data['updated_at'][:19]],
    ]
    
    request_table = Table(request_info, colWidths=[2*inch, 4*inch])
    request_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(request_table)
    story.append(Spacer(1, 20))
    
    # Requester Information
    story.append(Paragraph("Requester Information", styles['Heading2']))
    
    user_info = [
        ["Name:", user_data['full_name']],
        ["Email:", user_data['email']],
        ["Role:", user_data['role'].title()],
    ]
    
    user_table = Table(user_info, colWidths=[2*inch, 4*inch])
    user_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(user_table)
    story.append(Spacer(1, 20))
    
    # Description
    story.append(Paragraph("Request Description", styles['Heading2']))
    story.append(Paragraph(request_data['description'], styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Messages if provided
    if messages:
        story.append(Paragraph("Communication History", styles['Heading2']))
        for msg in messages:
            msg_text = f"<b>{msg['sender_name']} ({msg['sender_role']}):</b> {msg['content']}"
            story.append(Paragraph(msg_text, styles['Normal']))
            story.append(Spacer(1, 10))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

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

# ADMIN ROUTES - NEW
@api_router.post("/admin/create-staff", response_model=User)
async def create_staff_user(user_data: UserCreate, current_user: User = Depends(get_current_user)):
    """Admin-only route to create staff users"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create staff users")
    
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
    
    return new_user

@api_router.get("/admin/staff-members", response_model=List[StaffUser])
async def get_staff_members(current_user: User = Depends(get_current_user)):
    """Get all staff members with their workload"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view staff members")
    
    staff_users = await db.users.find({"role": "staff"}).to_list(None)
    staff_list = []
    
    for staff in staff_users:
        assigned_count = await db.requests.count_documents({"assigned_staff_id": staff["id"]})
        completed_count = await db.requests.count_documents({
            "assigned_staff_id": staff["id"],
            "status": "completed"
        })
        
        staff_list.append(StaffUser(
            id=staff["id"],
            full_name=staff["full_name"],
            email=staff["email"],
            assigned_requests=assigned_count,
            completed_requests=completed_count
        ))
    
    return staff_list

@api_router.get("/admin/requests-master-list")
async def get_master_requests_list(current_user: User = Depends(get_current_user)):
    """Get complete master list of all requests with full details"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view master requests list")
    
    # Get all requests
    requests = await db.requests.find().to_list(None)
    
    # Enhance with user and staff information
    enhanced_requests = []
    for req in requests:
        # Get requester information
        requester = await db.users.find_one({"id": req["user_id"]})
        
        # Get assigned staff information if assigned
        assigned_staff = None
        if req.get("assigned_staff_id"):
            assigned_staff = await db.users.find_one({"id": req["assigned_staff_id"]})
        
        # Get file count
        file_count = await db.files.count_documents({"request_id": req["id"]})
        
        # Get message count
        message_count = await db.messages.count_documents({"request_id": req["id"]})
        
        # Filter out MongoDB ObjectId and other non-serializable fields
        clean_req = {k: v for k, v in req.items() if k != '_id'}
        enhanced_request = {
            **clean_req,
            "requester_name": requester["full_name"] if requester else "Unknown",
            "requester_email": requester["email"] if requester else "Unknown",
            "assigned_staff_name": assigned_staff["full_name"] if assigned_staff else None,
            "assigned_staff_email": assigned_staff["email"] if assigned_staff else None,
            "file_count": file_count,
            "message_count": message_count
        }
        enhanced_requests.append(enhanced_request)
    
    return enhanced_requests

@api_router.get("/admin/unassigned-requests")
async def get_unassigned_requests(current_user: User = Depends(get_current_user)):
    """Get all unassigned requests for admin assignment"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view unassigned requests")
    
    unassigned = await db.requests.find({"assigned_staff_id": None}).to_list(None)
    
    # Enhance with requester information
    enhanced_requests = []
    for req in unassigned:
        requester = await db.users.find_one({"id": req["user_id"]})
        req["requester_name"] = requester["full_name"] if requester else "Unknown"
        req["requester_email"] = requester["email"] if requester else "Unknown"
        enhanced_requests.append(req)
    
    return enhanced_requests

# File Upload Routes (existing)
@api_router.post("/upload/{request_id}")
async def upload_file(request_id: str, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    # Verify user has access to this request
    request = await db.requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_obj = RecordRequest(**request)
    
    # Check permissions
    if (current_user.role == UserRole.USER and request_obj.user_id != current_user.id) or \
       (current_user.role == UserRole.STAFF and request_obj.assigned_staff_id != current_user.id and request_obj.assigned_staff_id is not None):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    unique_filename = f"{file_id}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Create file record
    file_upload = FileUpload(
        request_id=request_id,
        filename=unique_filename,
        original_name=file.filename,
        file_size=len(content),
        content_type=file.content_type,
        uploaded_by=current_user.id
    )
    
    await db.files.insert_one(prepare_for_mongo(file_upload.dict()))
    
    return {"message": "File uploaded successfully", "file_id": file_upload.id}

@api_router.get("/download/{file_id}")
async def download_file(file_id: str, current_user: User = Depends(get_current_user)):
    # Get file record
    file_record = await db.files.find_one({"id": file_id})
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions for the associated request
    request = await db.requests.find_one({"id": file_record["request_id"]})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_obj = RecordRequest(**request)
    
    # Check permissions
    if (current_user.role == UserRole.USER and request_obj.user_id != current_user.id) or \
       (current_user.role == UserRole.STAFF and request_obj.assigned_staff_id != current_user.id and request_obj.assigned_staff_id is not None):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
    
    file_path = UPLOAD_DIR / file_record["filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file_record["original_name"],
        media_type=file_record.get("content_type", "application/octet-stream")
    )

@api_router.get("/files/{request_id}")
async def get_request_files(request_id: str, current_user: User = Depends(get_current_user)):
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
    
    files = await db.files.find({"request_id": request_id}).to_list(None)
    return [FileUpload(**file) for file in files]

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
    
    # Send email notification
    await send_new_request_notification(new_request, current_user)
    
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

@api_router.post("/requests/{request_id}/assign", response_model=dict)
async def assign_request(request_id: str, assignment: RequestAssignment, current_user: User = Depends(get_current_user)):
    """Assign a request to a staff member"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can assign requests")
    
    # Validate request exists
    original_request = await db.requests.find_one({"id": request_id})
    if not original_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Validate staff user exists
    staff_user = await db.users.find_one({"id": assignment.staff_id, "role": "staff"})
    if not staff_user:
        raise HTTPException(status_code=404, detail="Staff user not found")
    
    # Update request
    await db.requests.update_one(
        {"id": request_id},
        {"$set": {
            "assigned_staff_id": assignment.staff_id,
            "status": "assigned",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Create notification for assigned staff
    notification = Notification(
        user_id=assignment.staff_id,
        title="Request Assigned",
        message=f"You have been assigned request: {original_request['title']}"
    )
    await db.notifications.insert_one(prepare_for_mongo(notification.dict()))
    
    # Send email notification
    request_obj = RecordRequest(**original_request)
    await send_assignment_notification(request_obj, staff_user)
    
    return {
        "message": "Request assigned successfully",
        "assigned_to": staff_user["full_name"],
        "request_id": request_id
    }

@api_router.put("/requests/{request_id}/status")
async def update_request_status(request_id: str, new_status: RequestStatus, current_user: User = Depends(get_current_user)):
    # Get original request
    original_request = await db.requests.find_one({"id": request_id})
    if not original_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    old_status = original_request["status"]
    
    # Check permissions
    if current_user.role == UserRole.USER:
        raise HTTPException(status_code=403, detail="Users cannot update request status")
    elif current_user.role == UserRole.STAFF and original_request["assigned_staff_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Can only update assigned requests")
    
    # Update request
    await db.requests.update_one(
        {"id": request_id},
        {"$set": {"status": new_status.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Send notification to requester
    requester = await db.users.find_one({"id": original_request["user_id"]})
    if requester:
        notification = Notification(
            user_id=requester["id"],
            title="Request Status Updated",
            message=f"Your request '{original_request['title']}' status changed to {new_status.value.replace('_', ' ').title()}"
        )
        await db.notifications.insert_one(prepare_for_mongo(notification.dict()))
        
        # Send email notification
        request_obj = RecordRequest(**original_request)
        await send_status_update_notification(request_obj, requester, old_status, new_status.value)
    
    return {"message": "Status updated successfully"}

# Export Routes
@api_router.get("/export/request/{request_id}/pdf")
async def export_request_pdf(request_id: str, current_user: User = Depends(get_current_user)):
    # Get request
    request = await db.requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_obj = RecordRequest(**request)
    
    # Check permissions
    if current_user.role == UserRole.USER and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == UserRole.STAFF and request_obj.assigned_staff_id != current_user.id and request_obj.assigned_staff_id is not None:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get user data
    user = await db.users.find_one({"id": request_obj.user_id})
    
    # Get messages
    messages = await db.messages.find({"request_id": request_id}).sort("created_at", 1).to_list(None)
    
    # Generate PDF
    pdf_buffer = generate_request_pdf(request, user, messages)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer.getvalue()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=request_{request_id[:8]}.pdf"}
    )

@api_router.get("/export/requests/csv")
async def export_requests_csv(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can export all requests")
    
    # Get all requests with enhanced details
    requests = await db.requests.find().to_list(None)
    
    # Convert to DataFrame with full details
    df_data = []
    for req in requests:
        requester = await db.users.find_one({"id": req["user_id"]})
        assigned_staff = None
        if req.get("assigned_staff_id"):
            assigned_staff = await db.users.find_one({"id": req["assigned_staff_id"]})
        
        df_data.append({
            "Request ID": req["id"],
            "Title": req["title"],
            "Description": req["description"][:100] + "..." if len(req["description"]) > 100 else req["description"],
            "Type": req["request_type"],
            "Status": req["status"],
            "Priority": req["priority"],
            "Requester Name": requester["full_name"] if requester else "Unknown",
            "Requester Email": requester["email"] if requester else "Unknown",
            "Assigned Staff": assigned_staff["full_name"] if assigned_staff else "Unassigned",
            "Staff Email": assigned_staff["email"] if assigned_staff else "",
            "Created At": req["created_at"],
            "Updated At": req["updated_at"]
        })
    
    df = pd.DataFrame(df_data)
    
    # Create CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=master_requests_export.csv"}
    )

# Analytics Routes (existing)
@api_router.get("/analytics/dashboard", response_model=AnalyticsData)
async def get_analytics_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view analytics")
    
    # Total requests
    total_requests = await db.requests.count_documents({})
    
    # Requests by status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_results = await db.requests.aggregate(status_pipeline).to_list(None)
    requests_by_status = {item["_id"]: item["count"] for item in status_results}
    
    # Requests by type
    type_pipeline = [
        {"$group": {"_id": "$request_type", "count": {"$sum": 1}}}
    ]
    type_results = await db.requests.aggregate(type_pipeline).to_list(None)
    requests_by_type = {item["_id"]: item["count"] for item in type_results}
    
    # Requests by priority
    priority_pipeline = [
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
    ]
    priority_results = await db.requests.aggregate(priority_pipeline).to_list(None)
    requests_by_priority = {item["_id"]: item["count"] for item in priority_results}
    
    # Average resolution time (for completed requests)
    completed_requests = await db.requests.find({"status": "completed"}).to_list(None)
    total_resolution_time = 0
    completed_count = 0
    
    for req in completed_requests:
        if req.get("created_at") and req.get("updated_at"):
            created = datetime.fromisoformat(req["created_at"].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(req["updated_at"].replace('Z', '+00:00'))
            resolution_time = (updated - created).total_seconds() / 3600  # hours
            total_resolution_time += resolution_time
            completed_count += 1
    
    average_resolution_time = total_resolution_time / completed_count if completed_count > 0 else 0
    
    # Monthly trends (last 12 months)
    monthly_trends = []
    for i in range(12):
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        month_count = await db.requests.count_documents({
            "created_at": {
                "$gte": month_start.isoformat(),
                "$lt": month_end.isoformat()
            }
        })
        
        monthly_trends.append({
            "month": month_start.strftime("%Y-%m"),
            "count": month_count
        })
    
    monthly_trends.reverse()
    
    # Staff workload
    staff_workload = []
    staff_users = await db.users.find({"role": "staff"}).to_list(None)
    for staff in staff_users:
        assigned_count = await db.requests.count_documents({"assigned_staff_id": staff["id"]})
        completed_count = await db.requests.count_documents({
            "assigned_staff_id": staff["id"],
            "status": "completed"
        })
        
        staff_workload.append({
            "name": staff["full_name"],
            "assigned": assigned_count,
            "completed": completed_count
        })
    
    return AnalyticsData(
        total_requests=total_requests,
        requests_by_status=requests_by_status,
        requests_by_type=requests_by_type,
        requests_by_priority=requests_by_priority,
        average_resolution_time=average_resolution_time,
        monthly_trends=monthly_trends,
        staff_workload=staff_workload
    )

# Message Routes (existing)
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

# Notification Routes (existing)
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

# Dashboard Routes (existing)
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

# Test email endpoint for debugging
@api_router.post("/test-email")
async def test_email_sending(current_user: User = Depends(get_current_user)):
    """Test email sending functionality"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    test_subject = "Police Records System - Email Test"
    test_content = f"""
Hello Administrator,

This is a test email from the Police Records Request System to verify that email notifications are working correctly.

Test Details:
- Sent at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
- From: {FROM_EMAIL}
- SMTP Server: {SMTP_SERVER}:{SMTP_PORT}
- Username: {SMTP_USERNAME}

If you receive this email, the notification system is working properly.

Best regards,
Police Records System
    """
    
    try:
        success = await send_email(
            to_email=FROM_EMAIL,  # Send to the administrator email
            subject=test_subject,
            content=test_content
        )
        
        if success:
            return {"message": "Test email sent successfully", "sent_to": FROM_EMAIL}
        else:
            return {"message": "Failed to send test email", "error": "Check server logs"}
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}")
        return {"message": "Test email failed", "error": str(e)}

# Admin-only endpoints for user management
@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    """Get all users for admin management"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}).to_list(None)
    return [{"id": user["id"], "email": user["email"], "full_name": user["full_name"], 
             "role": user["role"], "is_active": user.get("is_active", True), 
             "created_at": user["created_at"]} for user in users]

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role_data: dict, current_user: User = Depends(get_current_user)):
    """Update user role - admin only"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    new_role = role_data.get("role")
    if new_role not in ["user", "staff", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": new_role}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User role updated to {new_role}"}

@api_router.put("/admin/users/{user_id}/email")
async def update_user_email(user_id: str, email_data: dict, current_user: User = Depends(get_current_user)):
    """Update user email - admin only"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    new_email = email_data.get("email")
    if not new_email or "@" not in new_email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": new_email, "id": {"$ne": user_id}})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"email": new_email}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User email updated successfully"}

@api_router.post("/admin/create-staff")
async def create_staff_member(staff_data: UserCreate, current_user: User = Depends(get_current_user)):
    """Create new staff or admin user - admin only"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": staff_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create new user
    hashed_password = pwd_context.hash(staff_data.password)
    user_dict = {
        "id": str(uuid.uuid4()),
        "email": staff_data.email,
        "full_name": staff_data.full_name,
        "role": staff_data.role,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_dict)
    
    # Create user object for response
    user_obj = User(**{k: v for k, v in user_dict.items() if k != "hashed_password"})
    
    return {"message": f"{staff_data.role.title()} created successfully", "user": user_obj}

@api_router.get("/admin/staff-members")
async def get_staff_members(current_user: User = Depends(get_current_user)):
    """Get all staff members with workload info"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all staff and admin users
    staff_users = await db.users.find({"role": {"$in": ["staff", "admin"]}}).to_list(None)
    
    # Get workload for each staff member
    staff_with_workload = []
    for staff in staff_users:
        assigned_count = await db.requests.count_documents({"assigned_staff_id": staff["id"]})
        completed_count = await db.requests.count_documents({
            "assigned_staff_id": staff["id"],
            "status": "completed"
        })
        
        staff_with_workload.append({
            "id": staff["id"],
            "email": staff["email"],
            "full_name": staff["full_name"],
            "role": staff["role"],
            "assigned_requests": assigned_count,
            "completed_requests": completed_count
        })
    
    return staff_with_workload

@api_router.get("/admin/requests-master-list")
async def get_requests_master_list(current_user: User = Depends(get_current_user)):
    """Get complete master list of all requests with full details"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all requests with user and staff details
    requests = await db.requests.find({}).to_list(None)
    
    master_list = []
    for request in requests:
        # Get requester info
        requester = await db.users.find_one({"id": request["user_id"]})
        
        # Get assigned staff info if assigned
        assigned_staff = None
        if request.get("assigned_staff_id"):
            assigned_staff = await db.users.find_one({"id": request["assigned_staff_id"]})
        
        # Get file and message counts
        file_count = await db.files.count_documents({"request_id": request["id"]})
        message_count = await db.messages.count_documents({"request_id": request["id"]})
        
        master_list.append({
            "id": request["id"],
            "title": request["title"],
            "status": request["status"],
            "priority": request["priority"],
            "request_type": request["request_type"],
            "created_at": request["created_at"],
            "updated_at": request.get("updated_at", request["created_at"]),
            "requester_name": requester["full_name"] if requester else "Unknown",
            "requester_email": requester["email"] if requester else "Unknown",
            "assigned_staff_name": assigned_staff["full_name"] if assigned_staff else None,
            "assigned_staff_email": assigned_staff["email"] if assigned_staff else None,
            "file_count": file_count,
            "message_count": message_count
        })
    
    return master_list

@api_router.get("/admin/unassigned-requests")
async def get_unassigned_requests(current_user: User = Depends(get_current_user)):
    """Get all unassigned requests"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get unassigned requests
    unassigned = await db.requests.find({"assigned_staff_id": None}).to_list(None)
    
    unassigned_list = []
    for request in unassigned:
        # Get requester info
        requester = await db.users.find_one({"id": request["user_id"]})
        
        unassigned_list.append({
            "id": request["id"],
            "title": request["title"],
            "description": request["description"],
            "status": request["status"],
            "priority": request["priority"],
            "request_type": request["request_type"],
            "created_at": request["created_at"],
            "requester_name": requester["full_name"] if requester else "Unknown",
            "requester_email": requester["email"] if requester else "Unknown"
        })
    
    return unassigned_list

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