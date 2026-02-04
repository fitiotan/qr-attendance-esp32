from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import Request
from fastapi import FastAPI, UploadFile, Depends, Form
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
import socket
import datetime
import os

from .auth import authenticate, hash_password
from .database import SessionLocal, engine
from .models import Base, User, QRCode, Attendance
from .scan import process_scan
from .qr import generate_qr
from fastapi.staticfiles import StaticFiles

# Create tables with automatic migration
try:
    Base.metadata.create_all(bind=engine)
    
    # Add missing columns to existing Attendance table
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE attendance ADD COLUMN check_in DATETIME"))
            conn.commit()
            print("✓ Added check_in column")
        except:
            pass  # Column already exists
        
        try:
            conn.execute(text("ALTER TABLE attendance ADD COLUMN check_out DATETIME"))
            conn.commit()
            print("✓ Added check_out column")
        except:
            pass  # Column already exists
except Exception as e:
    print(f"Database migration error: {e}")

# ESP32 Camera activation state
esp32_active = False

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    SessionMiddleware,
    secret_key="CHANGE_THIS_SECRET",
    max_age=900  # 15 minutes session timeout
)

app.mount("/static", StaticFiles(directory="static"), name="static")


def get_local_ip():
    """Get the local IP address of the server"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def cleanup_qr_codes():
    """Delete all QR code files on startup"""
    static_dir = "static"
    if os.path.exists(static_dir):
        for file in os.listdir(static_dir):
            if file.startswith("qr_") and file.endswith(".png"):
                try:
                    os.remove(os.path.join(static_dir, file))
                except:
                    pass


# Cleanup on server startup
cleanup_qr_codes()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session:
        raise Exception("Not authenticated")
    user = db.query(User).filter(User.id == request.session["user_id"]).first()
    return user


@app.get("/")
def root(request: Request, db: Session = Depends(get_db)):
    # If no admin exists, redirect to setup
    admin_exists = db.query(User).filter(User.role == "admin").first()
    if not admin_exists:
        return RedirectResponse("/setup", status_code=302)

    # If logged in, redirect to appropriate dashboard
    if "user_id" in request.session:
        role = request.session.get("role")
        if role == "admin":
            return RedirectResponse("/admin", status_code=302)
        elif role == "client":
            return RedirectResponse("/client", status_code=302)

    # If not logged in, redirect to login
    return RedirectResponse("/login", status_code=302)


@app.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(get_db)):
    # Check if any admin exists
    admin_exists = db.query(User).filter(User.role == "admin").first()
    if admin_exists:
        return RedirectResponse("/login", status_code=302)

    return templates.TemplateResponse("setup.html", {"request": request})


@app.post("/setup")
def setup_admin(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Check if any admin exists
    admin_exists = db.query(User).filter(User.role == "admin").first()
    if admin_exists:
        return {"error": "Admin already exists"}

    if db.query(User).filter(User.username == username).first():
        return {"error": "Username already taken"}

    admin = User(
        username=username,
        password_hash=hash_password(password),
        role="admin"
    )
    db.add(admin)
    db.commit()
    return {"status": "success", "message": "Admin created! Please login."}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    # If no admin exists, redirect to setup
    admin_exists = db.query(User).filter(User.role == "admin").first()
    if not admin_exists:
        return RedirectResponse("/setup", status_code=302)

    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role

    # Redirect based on role
    if user.role == "admin":
        return RedirectResponse("/admin", status_code=302)
    else:
        return RedirectResponse("/client", status_code=302)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


# ADMIN ROUTES
@app.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session or request.session.get("role") != "admin":
        return RedirectResponse("/login", status_code=302)

    user = db.query(User).filter(User.id == request.session["user_id"]).first()
    if not user:
        return RedirectResponse("/login", status_code=302)
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "username": user.username
        }
    )


@app.post("/scan")
def scan_qr(file: UploadFile, db: Session = Depends(get_db), request: Request = None):
    status, message = process_scan(file, db)
    return {"status": status, "message": message}


@app.get("/admin/clients")
def get_clients(request: Request, db: Session = Depends(get_db)):
    """Get list of all client users for manual attendance"""
    if "user_id" not in request.session or request.session.get("role") != "admin":
        return {"error": "Unauthorized"}
    
    clients = db.query(User).filter(User.role == "client").all()
    return [
        {"id": client.id, "username": client.username}
        for client in clients
    ]


@app.get("/admin/attendance")
def get_attendance(request: Request, db: Session = Depends(get_db)):
    """Get recent attendance records"""
    if "user_id" not in request.session or request.session.get("role") != "admin":
        return {"error": "Unauthorized"}
    
    from .models import Attendance
    
    # Get last 20 attendance records
    records = db.query(Attendance).order_by(Attendance.scan_time.desc()).limit(20).all()
    
    result = []
    for record in records:
        user = db.query(User).filter(User.id == record.employee_id).first()
        result.append({
            "id": record.id,
            "username": user.username if user else "Unknown",
            "status": record.status,
            "reason": record.reason,
            "check_in": record.check_in.strftime("%Y-%m-%d %H:%M:%S") if record.check_in else "N/A",
            "check_out": record.check_out.strftime("%Y-%m-%d %H:%M:%S") if record.check_out else "-",
            "timestamp": record.scan_time.strftime("%Y-%m-%d %H:%M:%S") if record.scan_time else "N/A"
        })
    
    return result


@app.post("/admin/manual-attendance")
def manual_attendance(
    client_id: int = Form(...),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Record attendance manually without QR code"""
    if "user_id" not in request.session or request.session.get("role") != "admin":
        return {"error": "Unauthorized"}
    
    # Verify client exists
    client = db.query(User).filter(User.id == client_id, User.role == "client").first()
    if not client:
        return {"error": "Client not found"}
    
    # Record attendance
    from .models import Attendance
    import datetime
    
    attendance = Attendance(
        employee_id=client_id,
        status="OK",
        reason="Manual entry"
    )
    db.add(attendance)
    db.commit()
    
    return {"status": "success", "message": f"Attendance recorded for {client.username}"}


@app.get("/admin/register", response_class=HTMLResponse)
def admin_register_page(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session or request.session.get("role") != "admin":
        return RedirectResponse("/login", status_code=302)

    user = db.query(User).filter(User.id == request.session["user_id"]).first()
    return templates.TemplateResponse("admin_register.html", {"request": request, "username": user.username})


@app.post("/admin/register")
def admin_register_client(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    request: Request = None,
):
    if "user_id" not in request.session or request.session.get("role") != "admin":
        return {"error": "Unauthorized"}

    if db.query(User).filter(User.username == username).first():
        return {"error": "User exists"}

    user = User(
        username=username,
        password_hash=hash_password(password),
        role="client"
    )
    db.add(user)
    db.commit()
    return {"status": "success", "message": "Client registered"}


# CLIENT ROUTES
@app.get("/client", response_class=HTMLResponse)
def client_home(request: Request, db: Session = Depends(get_db)):
    if "user_id" not in request.session or request.session.get("role") != "client":
        return RedirectResponse("/login", status_code=302)

    user = db.query(User).filter(User.id == request.session["user_id"]).first()
    return templates.TemplateResponse(
        "client.html",
        {
            "request": request,
            "username": user.username,
            "client_id": user.id
        }
    )


@app.post("/generate_qr")
def generate(db: Session = Depends(get_db), request: Request = None):
    if "user_id" not in request.session or request.session.get("role") != "client":
        return {"error": "Unauthorized"}

    user_id = request.session["user_id"]
    path = generate_qr(user_id, db)
    return {"qr_path": path}

# ESP32 CAM ENDPOINTS
@app.get("/esp32/info")
def esp32_info():
    """Get server info for ESP32 connection"""
    local_ip = get_local_ip()
    return {
        "server_ip": local_ip,
        "port": 8000,
        "url": f"http://{local_ip}:8000",
        "scan_endpoint": f"http://{local_ip}:8000/esp32/upload",
        "message": "Connect your ESP32 to this server"
    }


@app.get("/esp32/status")
def esp32_status():
    """Check if ESP32 should be active"""
    global esp32_active
    print(f"ESP32 status check: active={esp32_active}")
    return {"active": esp32_active}


@app.post("/esp32/activate")
def esp32_activate(request: Request):
    """Activate ESP32 camera"""
    global esp32_active
    try:
        user_id = request.session.get("user_id")
        role = request.session.get("role")
        print(f"Activation request - user_id: {user_id}, role: {role}")
        
        if not user_id or role != "admin":
            print("Activation denied - not admin or not logged in")
            return {"error": "Unauthorized - admin access required"}
        
        esp32_active = True
        print(f"ESP32 activated! Status: {esp32_active}")
        return {"status": "activated"}
    except Exception as e:
        print(f"Error in activate: {e}")
        return {"error": str(e)}


@app.post("/esp32/deactivate")
def esp32_deactivate(request: Request):
    """Deactivate ESP32 camera"""
    global esp32_active
    try:
        user_id = request.session.get("user_id")
        role = request.session.get("role")
        
        if not user_id or role != "admin":
            return {"error": "Unauthorized"}
        
        esp32_active = False
        return {"status": "deactivated"}
    except Exception as e:
        print(f"Error in deactivate: {e}")
        return {"error": str(e)}


@app.post("/esp32/upload")
async def esp32_upload(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint for ESP32 cam to upload QR code image (raw JPEG)
    Usage: POST /esp32/upload with raw image bytes
    Returns: {"status": "OK" or "REJECTED", "message": "..."}
    """
    from fastapi import UploadFile
    from io import BytesIO
    import shutil
    
    # Read raw image bytes
    image_bytes = await request.body()
    
    # Save latest frame for live preview
    try:
        with open("static/esp32_latest.jpg", "wb") as f:
            f.write(image_bytes)
    except:
        pass
    
    # Create UploadFile object for processing
    file_obj = BytesIO(image_bytes)
    upload_file = UploadFile(filename="frame.jpg", file=file_obj)
    
    # Process the scan
    status, message = process_scan(upload_file, db)
    
    return {"status": status, "message": message}


@app.get("/esp32/stream")
def esp32_stream():
    """Get the latest frame from ESP32 camera"""
    from fastapi.responses import FileResponse
    import os
    
    frame_path = "static/esp32_latest.jpg"
    if os.path.exists(frame_path):
        return FileResponse(
            frame_path, 
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    
    # Return a placeholder if no frame yet
    return {"message": "No frame available yet"}