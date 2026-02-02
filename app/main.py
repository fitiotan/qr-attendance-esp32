from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
from fastapi import FastAPI, UploadFile, Depends, Form
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .auth import authenticate, hash_password
from .database import SessionLocal, engine
from .models import Base, User
from .scan import process_scan
from .qr import generate_qr
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    SessionMiddleware,
    secret_key="CHANGE_THIS_SECRET"
)

app.mount("/static", StaticFiles(directory="static"), name="static")


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
