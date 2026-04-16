"""Vehicle Auction System — FastAPI Application with WebSockets."""

from fastapi import (
    FastAPI, Request, Depends, HTTPException,
    Form, UploadFile, File, WebSocket, WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
from typing import List, Optional
from passlib.context import CryptContext
import os, uuid, shutil, secrets

from database import engine, get_db, Base
from models import User, Vehicle, Bid
from schemas import VehicleOut, BidCreate, BidOut

# ── App setup ─────────────────────────────────
app = FastAPI(title="Vehicle Auction System")

SECRET_KEY = os.getenv("SECRET_KEY", "auction-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

UPLOAD_DIR = os.path.join("static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# One-time token so only the GUI window can auto-login as admin
# When launched via `python main.py`, the token is set as an env var
# so the same value is used by both the GUI and the server.
GUI_TOKEN: str = os.environ.get("_AUTOBID_GUI_TOKEN", secrets.token_urlsafe(32))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def format_inr(amount) -> str:
    """Format numeric values in Indian Rupee style (e.g. Rs 12,34,567.89)."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return "Rs 0.00"

    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    integer_part, fractional_part = f"{abs_value:.2f}".split(".")

    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        rest = integer_part[:-3]
        chunks = []
        while len(rest) > 2:
            chunks.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            chunks.insert(0, rest)
        integer_part = ",".join(chunks + [last_three])

    return f"{sign}Rs {integer_part}.{fractional_part}"


templates.env.globals["format_inr"] = format_inr


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WEBSOCKET CONNECTION MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ConnectionManager:
    """Manages active WebSocket connections for real-time broadcasts."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws/auction")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()        # keep-alive; client doesn't send data
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── Helper: current user from session ─────────
def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def password_is_hashed(stored_password: str) -> bool:
    return bool(pwd_context.identify(stored_password))


def hash_password(raw_password: str) -> str:
    return pwd_context.hash(raw_password)


def verify_password(raw_password: str, stored_password: str) -> bool:
    if password_is_hashed(stored_password):
        return pwd_context.verify(raw_password, stored_password)
    return secrets.compare_digest(raw_password, stored_password)


def parse_auction_end(raw_value: str) -> datetime:
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid auction_end datetime format") from exc


def get_highest_bidder_map(db: Session, vehicle_ids: Optional[list[int]] = None) -> dict[int, int]:
    if vehicle_ids is not None and not vehicle_ids:
        return {}

    max_amount_query = db.query(
        Bid.vehicle_id.label("vehicle_id"),
        func.max(Bid.amount).label("max_amount"),
    )
    if vehicle_ids is not None:
        max_amount_query = max_amount_query.filter(Bid.vehicle_id.in_(vehicle_ids))
    max_amount_subquery = max_amount_query.group_by(Bid.vehicle_id).subquery()

    max_id_query = (
        db.query(
            Bid.vehicle_id.label("vehicle_id"),
            func.max(Bid.id).label("max_bid_id"),
        )
        .join(
            max_amount_subquery,
            and_(
                Bid.vehicle_id == max_amount_subquery.c.vehicle_id,
                Bid.amount == max_amount_subquery.c.max_amount,
            ),
        )
    )
    if vehicle_ids is not None:
        max_id_query = max_id_query.filter(Bid.vehicle_id.in_(vehicle_ids))
    max_id_subquery = max_id_query.group_by(Bid.vehicle_id).subquery()

    rows = (
        db.query(Bid.vehicle_id, Bid.user_id)
        .join(max_id_subquery, Bid.id == max_id_subquery.c.max_bid_id)
        .all()
    )
    return {vehicle_id: user_id for vehicle_id, user_id in rows}


# ── Helper: finalize expired auctions ─────────
def finalize_auctions(db: Session):
    """Close expired auctions and assign vehicles to highest bidders."""
    now = datetime.now()
    expired = (
        db.query(Vehicle)
        .filter(
            Vehicle.is_active.is_(True),
            Vehicle.is_deleted.is_(False),
            Vehicle.auction_end <= now,
        )
        .all()
    )

    if not expired:
        return

    expired_ids = [vehicle.id for vehicle in expired]
    highest_bidders = get_highest_bidder_map(db, expired_ids)

    for vehicle in expired:
        vehicle.is_active = False
        vehicle.owner_id = highest_bidders.get(vehicle.id)

    db.commit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HTML PAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    finalize_auctions(db)
    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.is_active.is_(True), Vehicle.is_deleted.is_(False))
        .all()
    )
    finished = (
        db.query(Vehicle)
        .filter(Vehicle.is_active.is_(False), Vehicle.is_deleted.is_(False))
        .order_by(Vehicle.auction_end.desc())
        .all()
    )
    user = get_current_user(request, db)

    highest_bidders = get_highest_bidder_map(db, [vehicle.id for vehicle in vehicles])

    return templates.TemplateResponse(request, "index.html", {
        "vehicles": vehicles,
        "finished": finished,
        "user": user,
        "highest_bidders": highest_bidders,
    })


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(request, "login.html", {
        "user": user,
        "error": None,
    })


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(request, "login.html", {
            "user": None,
            "error": "Invalid username or password",
        })

    if not password_is_hashed(user.password):
        user.password = hash_password(password)
        db.commit()

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(request, "login.html", {
        "user": user,
        "error": None,
        "register_mode": True,
    })


@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip()
    email = email.strip().lower()

    if len(username) < 3:
        return templates.TemplateResponse(request, "login.html", {
            "user": None,
            "error": "Username must be at least 3 characters",
            "register_mode": True,
        })
    if len(password) < 6:
        return templates.TemplateResponse(request, "login.html", {
            "user": None,
            "error": "Password must be at least 6 characters",
            "register_mode": True,
        })

    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing:
        return templates.TemplateResponse(request, "login.html", {
            "user": None,
            "error": "Username or email already taken",
            "register_mode": True,
        })
    new_user = User(
        username=username,
        email=email,
        password=hash_password(password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# ── My Vehicles (Purchased / Won) ─────────────
@app.get("/my-vehicles", response_class=HTMLResponse)
def my_vehicles(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    finalize_auctions(db)
    owned = (
        db.query(Vehicle)
        .filter(Vehicle.owner_id == user.id, Vehicle.is_active == False)
        .all()
    )
    return templates.TemplateResponse(request, "my_vehicles.html", {
        "user": user,
        "vehicles": owned,
    })


# ── Admin: GUI auto-login (token protected) ───
@app.get("/admin/gui-login", response_class=HTMLResponse)
def admin_gui_login(request: Request, token: str = "", db: Session = Depends(get_db)):
    """Called once by the desktop GUI window to establish an admin session."""
    if not token or token != GUI_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    admin_user = db.query(User).filter(User.is_admin == True).first()
    if not admin_user:
        raise HTTPException(status_code=500, detail="No admin user found in database")
    request.session["user_id"] = admin_user.id
    return RedirectResponse(url="/admin", status_code=303)


# ── Admin Panel ───────────────────────────────
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        return RedirectResponse(url="/login", status_code=303)
    finalize_auctions(db)
    active_vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.is_active.is_(True), Vehicle.is_deleted.is_(False))
        .all()
    )
    finished_vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.is_active.is_(False), Vehicle.is_deleted.is_(False))
        .order_by(Vehicle.auction_end.desc())
        .all()
    )
    deleted_vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.is_deleted.is_(True))
        .order_by(Vehicle.auction_end.desc())
        .all()
    )
    users = db.query(User).all()
    bids = db.query(Bid).order_by(Bid.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin.html", {
        "user": user,
        "active_vehicles": active_vehicles,
        "finished_vehicles": finished_vehicles,
        "deleted_vehicles": deleted_vehicles,
        "users": users,
        "bids": bids,
    })


# ── Admin: Add Vehicle (with image upload) ────
@app.post("/admin/add-vehicle")
async def admin_add_vehicle(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    starting_price: float = Form(...),
    auction_end: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    image_url = None
    if image and image.filename:
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported image file type")
        if image.content_type and not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_url = f"/static/uploads/{filename}"

    end_dt = parse_auction_end(auction_end)
    if end_dt <= datetime.now():
        raise HTTPException(status_code=400, detail="Auction end time must be in the future")

    vehicle = Vehicle(
        title=title,
        description=description,
        image_url=image_url,
        starting_price=starting_price,
        current_price=starting_price,
        auction_end=end_dt,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    # broadcast new vehicle to all clients
    await manager.broadcast({
        "type": "vehicle_added",
        "vehicle": {
            "id": vehicle.id,
            "title": vehicle.title,
            "description": vehicle.description or "",
            "image_url": vehicle.image_url,
            "starting_price": float(vehicle.starting_price),
            "current_price": float(vehicle.current_price),
            "auction_end": vehicle.auction_end.isoformat(),
        },
    })

    return RedirectResponse(url="/admin", status_code=303)


# ── Admin: Delete Vehicle ─────────────────────
@app.post("/admin/delete-vehicle/{vehicle_id}")
async def admin_delete_vehicle(
    vehicle_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Soft-delete: mark as deleted but keep the record
    vehicle.is_deleted = True
    vehicle.is_active = False
    db.commit()

    # broadcast removal to all clients
    await manager.broadcast({
        "type": "vehicle_removed",
        "vehicle_id": vehicle_id,
    })

    return RedirectResponse(url="/admin", status_code=303)


# ── Admin: Update Auction Period ──────────────
@app.post("/admin/update-auction/{vehicle_id}")
async def admin_update_auction(
    vehicle_id: int,
    request: Request,
    auction_end: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot update deleted vehicle")

    new_end = parse_auction_end(auction_end)
    vehicle.auction_end = new_end

    # If the new end time is in the future, reactivate the auction
    if new_end > datetime.now():
        vehicle.is_active = True
        vehicle.owner_id = None        # clear previous winner

    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  REST API ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/vehicles", response_model=List[VehicleOut])
def api_get_vehicles(db: Session = Depends(get_db)):
    finalize_auctions(db)
    return (
        db.query(Vehicle)
        .filter(Vehicle.is_active.is_(True), Vehicle.is_deleted.is_(False))
        .all()
    )


@app.get("/api/vehicles/{vehicle_id}", response_model=VehicleOut)
def api_get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id, Vehicle.is_deleted.is_(False))
        .first()
    )
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@app.post("/api/bids", response_model=BidOut)
async def api_place_bid(
    request: Request,
    bid: BidCreate,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required to place a bid")
    if user.is_admin:
        raise HTTPException(status_code=403, detail="Admins cannot place bids")

    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == bid.vehicle_id, Vehicle.is_deleted.is_(False))
        .with_for_update()
        .first()
    )
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if not vehicle.is_active:
        raise HTTPException(status_code=400, detail="Auction has ended")
    if datetime.now() >= vehicle.auction_end:
        raise HTTPException(status_code=400, detail="Auction period has expired")
    if bid.amount <= vehicle.current_price:
        raise HTTPException(
            status_code=400,
            detail=f"Bid must be greater than current price ${vehicle.current_price:,.2f}",
        )

    new_bid = Bid(amount=bid.amount, user_id=user.id, vehicle_id=vehicle.id)
    vehicle.current_price = bid.amount
    db.add(new_bid)
    db.commit()
    db.refresh(new_bid)

    # broadcast bid update to all connected clients
    await manager.broadcast({
        "type": "bid_update",
        "vehicle_id": vehicle.id,
        "current_price": float(vehicle.current_price),
        "bidder": user.username,
        "bidder_id": user.id,
    })

    return new_bid


@app.get("/api/vehicles/{vehicle_id}/bids", response_model=List[BidOut])
def api_get_bids(vehicle_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Bid)
        .filter(Bid.vehicle_id == vehicle_id)
        .order_by(Bid.created_at.desc())
        .all()
    )


# ── Run ───────────────────────────────────────
if __name__ == "__main__":
    import threading
    import time
    import uvicorn

    try:
        import webview
    except ModuleNotFoundError:
        webview = None

    HOST, PORT = "127.0.0.1", 8000
    BASE_URL = f"http://{HOST}:{PORT}"

    # Share the token via env var so the re-imported module gets the same value
    os.environ["_AUTOBID_GUI_TOKEN"] = GUI_TOKEN

    if webview is None:
        print("PyWebView is not installed. Starting in web-server mode only.")
        uvicorn.run("main:app", host=HOST, port=PORT, log_level="info")
        raise SystemExit(0)

    # Start uvicorn in a daemon thread so it shuts down with the GUI
    server_thread = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": "main:app", "host": HOST, "port": PORT, "log_level": "info"},
        daemon=True,
    )
    server_thread.start()

    # Wait for the server to become reachable
    import urllib.request, urllib.error
    for _ in range(30):
        try:
            urllib.request.urlopen(f"{BASE_URL}/docs")
            break
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.3)

    # Open the native desktop window, auto-login via the one-time token
    login_url = f"{BASE_URL}/admin/gui-login?token={GUI_TOKEN}"
    webview.create_window(
        "AutoBid — Admin Panel",
        url=login_url,
        width=1280,
        height=820,
        min_size=(900, 600),
    )
    webview.start()   # blocks until the window is closed
