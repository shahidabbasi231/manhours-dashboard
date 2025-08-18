from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date, timedelta
import json
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class LicenseClass(str, Enum):
    CLASS_A = "Class A"
    CLASS_B = "Class B"
    CLASS_C = "Class C"
    CDL_A = "CDL Class A"
    CDL_B = "CDL Class B"

class TrainingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"

class CertificationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"

class TrainingModuleType(str, Enum):
    SAFETY = "safety"
    DEFENSIVE_DRIVING = "defensive_driving"
    VEHICLE_INSPECTION = "vehicle_inspection"
    HAZMAT = "hazmat"
    BACKING_MANEUVERS = "backing_maneuvers"
    CARGO_HANDLING = "cargo_handling"
    HOURS_OF_SERVICE = "hours_of_service"
    FATIGUE_MANAGEMENT = "fatigue_management"

# Data Models
class Driver(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    hire_date: date
    license_number: str
    license_class: LicenseClass
    license_expiry: date
    date_of_birth: date
    address: str
    emergency_contact_name: str
    emergency_contact_phone: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DriverCreate(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    hire_date: date
    license_number: str
    license_class: LicenseClass
    license_expiry: date
    date_of_birth: date
    address: str
    emergency_contact_name: str
    emergency_contact_phone: str

class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    license_class: Optional[LicenseClass] = None
    license_expiry: Optional[date] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    is_active: Optional[bool] = None

class TrainingModule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    module_type: TrainingModuleType
    duration_hours: float
    required_score: int  # minimum score to pass (out of 100)
    is_mandatory: bool = True
    prerequisites: List[str] = []  # list of module IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TrainingModuleCreate(BaseModel):
    name: str
    description: str
    module_type: TrainingModuleType
    duration_hours: float
    required_score: int = 80
    is_mandatory: bool = True
    prerequisites: List[str] = []

class TrainingProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    driver_id: str
    module_id: str
    status: TrainingStatus
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    score: Optional[int] = None  # out of 100
    attempts: int = 0
    instructor_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TrainingProgressCreate(BaseModel):
    driver_id: str
    module_id: str
    status: TrainingStatus = TrainingStatus.NOT_STARTED

class TrainingProgressUpdate(BaseModel):
    status: Optional[TrainingStatus] = None
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    score: Optional[int] = None
    instructor_notes: Optional[str] = None

class Certification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    driver_id: str
    certification_name: str
    certification_type: str  # e.g., "DOT Physical", "Drug Test", "Safety Training"
    issue_date: date
    expiry_date: date
    issuing_authority: str
    certificate_number: str
    status: CertificationStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CertificationCreate(BaseModel):
    driver_id: str
    certification_name: str
    certification_type: str
    issue_date: date
    expiry_date: date
    issuing_authority: str
    certificate_number: str

class DashboardSummary(BaseModel):
    total_drivers: int
    active_drivers: int
    total_training_modules: int
    drivers_with_expired_certifications: int
    drivers_with_expiring_certifications: int
    overall_completion_rate: float
    recent_completions: int

# Helper functions
def get_certification_status(expiry_date: date) -> CertificationStatus:
    today = date.today()
    days_until_expiry = (expiry_date - today).days
    
    if days_until_expiry < 0:
        return CertificationStatus.EXPIRED
    elif days_until_expiry <= 30:
        return CertificationStatus.EXPIRING_SOON
    else:
        return CertificationStatus.ACTIVE

# API Routes

# Driver Management
@api_router.post("/drivers", response_model=Driver)
async def create_driver(driver: DriverCreate):
    driver_dict = driver.dict()
    driver_obj = Driver(**driver_dict)
    result = await db.drivers.insert_one(driver_obj.dict())
    return driver_obj

@api_router.get("/drivers", response_model=List[Driver])
async def get_drivers():
    drivers = await db.drivers.find({"is_active": True}).to_list(1000)
    return [Driver(**driver) for driver in drivers]

@api_router.get("/drivers/{driver_id}", response_model=Driver)
async def get_driver(driver_id: str):
    driver = await db.drivers.find_one({"id": driver_id, "is_active": True})
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return Driver(**driver)

@api_router.put("/drivers/{driver_id}", response_model=Driver)
async def update_driver(driver_id: str, driver_update: DriverUpdate):
    update_data = {k: v for k, v in driver_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.drivers.update_one(
        {"id": driver_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    updated_driver = await db.drivers.find_one({"id": driver_id})
    return Driver(**updated_driver)

@api_router.delete("/drivers/{driver_id}")
async def delete_driver(driver_id: str):
    result = await db.drivers.update_one(
        {"id": driver_id}, 
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"message": "Driver deactivated successfully"}

# Training Module Management
@api_router.post("/training-modules", response_model=TrainingModule)
async def create_training_module(module: TrainingModuleCreate):
    module_dict = module.dict()
    module_obj = TrainingModule(**module_dict)
    result = await db.training_modules.insert_one(module_obj.dict())
    return module_obj

@api_router.get("/training-modules", response_model=List[TrainingModule])
async def get_training_modules():
    modules = await db.training_modules.find().to_list(1000)
    return [TrainingModule(**module) for module in modules]

@api_router.get("/training-modules/{module_id}", response_model=TrainingModule)
async def get_training_module(module_id: str):
    module = await db.training_modules.find_one({"id": module_id})
    if not module:
        raise HTTPException(status_code=404, detail="Training module not found")
    return TrainingModule(**module)

# Training Progress Management
@api_router.post("/training-progress", response_model=TrainingProgress)
async def create_training_progress(progress: TrainingProgressCreate):
    # Check if progress already exists
    existing = await db.training_progress.find_one({
        "driver_id": progress.driver_id,
        "module_id": progress.module_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Training progress already exists for this driver-module combination")
    
    progress_dict = progress.dict()
    progress_obj = TrainingProgress(**progress_dict)
    result = await db.training_progress.insert_one(progress_obj.dict())
    return progress_obj

@api_router.get("/training-progress")
async def get_training_progress(driver_id: Optional[str] = None, module_id: Optional[str] = None):
    query = {}
    if driver_id:
        query["driver_id"] = driver_id
    if module_id:
        query["module_id"] = module_id
    
    progress_list = await db.training_progress.find(query).to_list(1000)
    return [TrainingProgress(**progress) for progress in progress_list]

@api_router.put("/training-progress/{progress_id}", response_model=TrainingProgress)
async def update_training_progress(progress_id: str, progress_update: TrainingProgressUpdate):
    update_data = {k: v for k, v in progress_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # If marking as completed, set completion date
    if update_data.get("status") == TrainingStatus.COMPLETED and "completion_date" not in update_data:
        update_data["completion_date"] = date.today()
    
    # If starting training, set start date
    if update_data.get("status") == TrainingStatus.IN_PROGRESS and "start_date" not in update_data:
        update_data["start_date"] = date.today()
    
    # Increment attempts if status is being updated
    if "status" in update_data:
        await db.training_progress.update_one(
            {"id": progress_id},
            {"$inc": {"attempts": 1}}
        )
    
    result = await db.training_progress.update_one(
        {"id": progress_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Training progress not found")
    
    updated_progress = await db.training_progress.find_one({"id": progress_id})
    return TrainingProgress(**updated_progress)

# Certification Management
@api_router.post("/certifications", response_model=Certification)
async def create_certification(cert: CertificationCreate):
    cert_dict = cert.dict()
    cert_dict["status"] = get_certification_status(cert.expiry_date)
    cert_obj = Certification(**cert_dict)
    result = await db.certifications.insert_one(cert_obj.dict())
    return cert_obj

@api_router.get("/certifications")
async def get_certifications(driver_id: Optional[str] = None):
    query = {}
    if driver_id:
        query["driver_id"] = driver_id
    
    certifications = await db.certifications.find(query).to_list(1000)
    # Update status based on current date
    for cert in certifications:
        cert["status"] = get_certification_status(date.fromisoformat(cert["expiry_date"]))
    
    return [Certification(**cert) for cert in certifications]

@api_router.get("/certifications/expiring")
async def get_expiring_certifications():
    thirty_days_from_now = date.today() + timedelta(days=30)
    certifications = await db.certifications.find({
        "expiry_date": {"$lte": thirty_days_from_now.isoformat()}
    }).to_list(1000)
    
    # Update status and get driver info
    result = []
    for cert in certifications:
        cert["status"] = get_certification_status(date.fromisoformat(cert["expiry_date"]))
        driver = await db.drivers.find_one({"id": cert["driver_id"]})
        if driver:
            cert_with_driver = {**cert, "driver_name": f"{driver['first_name']} {driver['last_name']}"}
            result.append(cert_with_driver)
    
    return result

# Analytics and Reporting
@api_router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    # Get driver counts
    total_drivers = await db.drivers.count_documents({"is_active": True})
    active_drivers = total_drivers  # All active drivers
    
    # Get training module count
    total_modules = await db.training_modules.count_documents({})
    
    # Get certification status counts
    today = date.today()
    thirty_days_from_now = today + timedelta(days=30)
    
    expired_certs = await db.certifications.count_documents({
        "expiry_date": {"$lt": today.isoformat()}
    })
    
    expiring_certs = await db.certifications.count_documents({
        "expiry_date": {
            "$gte": today.isoformat(),
            "$lte": thirty_days_from_now.isoformat()
        }
    })
    
    # Calculate completion rate
    total_progress_records = await db.training_progress.count_documents({})
    completed_records = await db.training_progress.count_documents({"status": TrainingStatus.COMPLETED})
    completion_rate = (completed_records / total_progress_records * 100) if total_progress_records > 0 else 0
    
    # Recent completions (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    recent_completions = await db.training_progress.count_documents({
        "status": TrainingStatus.COMPLETED,
        "completion_date": {"$gte": thirty_days_ago.isoformat()}
    })
    
    return DashboardSummary(
        total_drivers=total_drivers,
        active_drivers=active_drivers,
        total_training_modules=total_modules,
        drivers_with_expired_certifications=expired_certs,
        drivers_with_expiring_certifications=expiring_certs,
        overall_completion_rate=round(completion_rate, 2),
        recent_completions=recent_completions
    )

@api_router.get("/analytics/driver-progress/{driver_id}")
async def get_driver_progress_analytics(driver_id: str):
    # Get driver info
    driver = await db.drivers.find_one({"id": driver_id, "is_active": True})
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Get all progress for this driver
    progress_records = await db.training_progress.find({"driver_id": driver_id}).to_list(1000)
    
    # Get training modules for context
    module_ids = [p["module_id"] for p in progress_records]
    modules = await db.training_modules.find({"id": {"$in": module_ids}}).to_list(1000)
    modules_dict = {m["id"]: m for m in modules}
    
    # Calculate statistics
    total_assigned = len(progress_records)
    completed = len([p for p in progress_records if p["status"] == TrainingStatus.COMPLETED])
    in_progress = len([p for p in progress_records if p["status"] == TrainingStatus.IN_PROGRESS])
    not_started = len([p for p in progress_records if p["status"] == TrainingStatus.NOT_STARTED])
    failed = len([p for p in progress_records if p["status"] == TrainingStatus.FAILED])
    
    # Average score
    completed_with_scores = [p for p in progress_records if p["status"] == TrainingStatus.COMPLETED and p.get("score")]
    avg_score = sum(p["score"] for p in completed_with_scores) / len(completed_with_scores) if completed_with_scores else 0
    
    # Get certifications for this driver
    certifications = await db.certifications.find({"driver_id": driver_id}).to_list(1000)
    
    return {
        "driver": Driver(**driver),
        "training_stats": {
            "total_assigned": total_assigned,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started,
            "failed": failed,
            "completion_rate": round((completed / total_assigned * 100) if total_assigned > 0 else 0, 2),
            "average_score": round(avg_score, 2)
        },
        "progress_details": [
            {
                **TrainingProgress(**p).dict(),
                "module_name": modules_dict.get(p["module_id"], {}).get("name", "Unknown Module")
            }
            for p in progress_records
        ],
        "certifications": [Certification(**cert) for cert in certifications]
    }

@api_router.get("/analytics/module-performance/{module_id}")
async def get_module_performance_analytics(module_id: str):
    # Get module info
    module = await db.training_modules.find_one({"id": module_id})
    if not module:
        raise HTTPException(status_code=404, detail="Training module not found")
    
    # Get all progress for this module
    progress_records = await db.training_progress.find({"module_id": module_id}).to_list(1000)
    
    if not progress_records:
        return {
            "module": TrainingModule(**module),
            "stats": {
                "total_assigned": 0,
                "completed": 0,
                "completion_rate": 0,
                "average_score": 0,
                "average_attempts": 0
            },
            "performance_distribution": []
        }
    
    # Calculate statistics
    total_assigned = len(progress_records)
    completed = len([p for p in progress_records if p["status"] == TrainingStatus.COMPLETED])
    
    # Score and attempts analysis
    completed_records = [p for p in progress_records if p["status"] == TrainingStatus.COMPLETED]
    scores = [p["score"] for p in completed_records if p.get("score")]
    attempts = [p["attempts"] for p in progress_records if p.get("attempts")]
    
    avg_score = sum(scores) / len(scores) if scores else 0
    avg_attempts = sum(attempts) / len(attempts) if attempts else 0
    
    return {
        "module": TrainingModule(**module),
        "stats": {
            "total_assigned": total_assigned,
            "completed": completed,
            "completion_rate": round((completed / total_assigned * 100) if total_assigned > 0 else 0, 2),
            "average_score": round(avg_score, 2),
            "average_attempts": round(avg_attempts, 2)
        },
        "performance_distribution": scores
    }

@api_router.get("/analytics/compliance-report")
async def get_compliance_report():
    # Get all drivers
    drivers = await db.drivers.find({"is_active": True}).to_list(1000)
    
    compliance_data = []
    today = date.today()
    
    for driver in drivers:
        driver_obj = Driver(**driver)
        
        # Get training progress
        progress_records = await db.training_progress.find({"driver_id": driver["id"]}).to_list(1000)
        mandatory_modules = await db.training_modules.find({"is_mandatory": True}).to_list(1000)
        
        completed_mandatory = len([
            p for p in progress_records 
            if p["status"] == TrainingStatus.COMPLETED and 
            any(m["id"] == p["module_id"] and m["is_mandatory"] for m in mandatory_modules)
        ])
        total_mandatory = len(mandatory_modules)
        
        # Get certifications
        certifications = await db.certifications.find({"driver_id": driver["id"]}).to_list(1000)
        expired_certs = len([
            c for c in certifications 
            if date.fromisoformat(c["expiry_date"]) < today
        ])
        
        # Check license expiry
        license_expired = driver_obj.license_expiry < today
        
        compliance_status = "Compliant"
        if expired_certs > 0 or license_expired or completed_mandatory < total_mandatory:
            compliance_status = "Non-Compliant"
        
        compliance_data.append({
            "driver": driver_obj,
            "mandatory_training_completion": f"{completed_mandatory}/{total_mandatory}",
            "expired_certifications": expired_certs,
            "license_status": "Expired" if license_expired else "Valid",
            "compliance_status": compliance_status
        })
    
    return compliance_data

# Initialize default training modules
@api_router.post("/training-modules/initialize-defaults")
async def initialize_default_modules():
    default_modules = [
        {
            "name": "Defensive Driving",
            "description": "Learn defensive driving techniques to prevent accidents and ensure road safety",
            "module_type": TrainingModuleType.DEFENSIVE_DRIVING,
            "duration_hours": 8.0,
            "required_score": 85,
            "is_mandatory": True
        },
        {
            "name": "Vehicle Inspection",
            "description": "Pre-trip and post-trip vehicle inspection procedures",
            "module_type": TrainingModuleType.VEHICLE_INSPECTION,
            "duration_hours": 4.0,
            "required_score": 90,
            "is_mandatory": True
        },
        {
            "name": "Safety Protocols",
            "description": "Comprehensive safety protocols and emergency procedures",
            "module_type": TrainingModuleType.SAFETY,
            "duration_hours": 6.0,
            "required_score": 85,
            "is_mandatory": True
        },
        {
            "name": "Hazmat Handling",
            "description": "Hazardous materials handling and transportation safety",
            "module_type": TrainingModuleType.HAZMAT,
            "duration_hours": 12.0,
            "required_score": 95,
            "is_mandatory": False
        },
        {
            "name": "Backing and Maneuvering",
            "description": "Safe backing techniques and tight space maneuvering",
            "module_type": TrainingModuleType.BACKING_MANEUVERS,
            "duration_hours": 4.0,
            "required_score": 80,
            "is_mandatory": True
        },
        {
            "name": "Cargo Handling",
            "description": "Proper cargo loading, securing, and unloading procedures",
            "module_type": TrainingModuleType.CARGO_HANDLING,
            "duration_hours": 6.0,
            "required_score": 85,
            "is_mandatory": True
        },
        {
            "name": "Hours of Service",
            "description": "DOT hours of service regulations and logbook management",
            "module_type": TrainingModuleType.HOURS_OF_SERVICE,
            "duration_hours": 3.0,
            "required_score": 90,
            "is_mandatory": True
        },
        {
            "name": "Fatigue Management",
            "description": "Recognizing and managing driver fatigue for safe operations",
            "module_type": TrainingModuleType.FATIGUE_MANAGEMENT,
            "duration_hours": 2.0,
            "required_score": 85,
            "is_mandatory": True
        }
    ]
    
    created_modules = []
    for module_data in default_modules:
        # Check if module already exists
        existing = await db.training_modules.find_one({"name": module_data["name"]})
        if not existing:
            module_obj = TrainingModule(**module_data)
            await db.training_modules.insert_one(module_obj.dict())
            created_modules.append(module_obj)
    
    return {"message": f"Created {len(created_modules)} default training modules", "modules": created_modules}

# Legacy routes (keeping the existing functionality)
@api_router.get("/")
async def root():
    return {"message": "Truck Driver Training Dashboard API"}

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