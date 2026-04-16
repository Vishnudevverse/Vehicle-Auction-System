# AutoBid: Real-Time Vehicle Auction Platform

AutoBid is a full-stack vehicle auction platform built with FastAPI, MySQL, SQLAlchemy, server-rendered templates, and WebSockets. It supports real-time bidding, admin inventory control, automatic winner assignment, and a polished INR-first auction experience.

## Executive Summary

- Real-time bid broadcasting over WebSockets.
- INR pricing across backend-rendered and live-updated UI.
- Admin and customer roles with session-based access control.
- Finished auctions with winner ownership and My Vehicles view.
- Soft-delete lifecycle for vehicles to preserve auction history.
- Optional desktop admin shell via PyWebView (automatic server-only fallback when unavailable).

## Current Demo Dataset

The seeded dataset in Database.sql includes:

- 1 admin user and 2 customer users.
- 8 active auctions (Indian market focus + selected imported vehicles).
- 3 finished auctions with winners already assigned.
- Bid history for finished auctions and active bidding examples.

Default accounts:

- Admin: admin / admin123
- Customer: john_doe / password123
- Customer: jane_smith / password123

## Feature Highlights

### Customer Experience

- Browse live and finished auctions.
- Search, filter, and sort vehicles.
- Place bids with instant UI updates.
- View won vehicles under My Vehicles.

### Admin Experience

- Add vehicles with image upload.
- Validate file type and auction end date.
- Restart or extend auctions.
- Soft-delete listings (history retained).
- View users and bid ledger from dashboard.

### Platform Behavior

- Request-driven auction finalization:
  expired auctions are closed and ownership is assigned to highest bidders.
- Row-level protection during bidding via with_for_update.
- Legacy plain-text passwords auto-upgrade to hashed format after successful login.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Starlette Sessions, SQLAlchemy |
| Database | MySQL (mysql-connector-python) |
| Frontend | Jinja2 templates, Bootstrap 5, Vanilla JavaScript |
| Realtime | WebSocket endpoint (/ws/auction) |
| Auth/Security | Passlib + bcrypt, session middleware |
| Runtime | Uvicorn, optional PyWebView desktop wrapper |

## Architecture at a Glance

- main.py: FastAPI app, routes, bidding logic, websocket broadcasting, auth flow.
- models.py: SQLAlchemy entities (User, Vehicle, Bid).
- schemas.py: API response/request schemas.
- database.py: SQLAlchemy engine/session wiring.
- templates/: server-rendered pages (home, login/register, admin, my vehicles).
- static/js/auction.js: live bidding UX, reconnect logic, bid modal, sorting/filtering.
- Database.sql: schema + presentation-ready seed data.

## Quick Start

### 1) Prerequisites

- Python 3.13+ recommended
- MySQL 8+

### 2) Install Dependencies

Use the same interpreter for installation and runtime:

```bash
python -m pip install -r temp/requirements.txt
```

### 3) Initialize Database

```bash
mysql -u root -p < Database.sql
```

### 4) Configure Environment

Create .env in project root:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=1234
DB_NAME=vehicle_auction
DB_PORT=3306
SECRET_KEY=auction-secret-key-change-in-production
```

### 5) Run the Application

```bash
python main.py
```

Open:

- App: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

Alternative server-only run:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| DB_HOST | MySQL host | localhost |
| DB_USER | MySQL username | root |
| DB_PASSWORD | MySQL password | 1234 |
| DB_NAME | MySQL database name | vehicle_auction |
| DB_PORT | MySQL port | 3306 |
| SECRET_KEY | Session signing key | auction-secret-key-change-in-production |

## API Snapshot

| Endpoint | Method | Purpose |
|---|---|---|
| /api/vehicles | GET | List active, non-deleted vehicles |
| /api/vehicles/{vehicle_id} | GET | Vehicle detail |
| /api/bids | POST | Place bid (login required, admin blocked) |
| /api/vehicles/{vehicle_id}/bids | GET | Bid history for a vehicle |
| /ws/auction | WS | Live bid/vehicle events |

## Security and Data Integrity Notes

- Password hashing: passlib[bcrypt] with bcrypt pinned to 4.0.1.
- Session auth enforced for bidding and admin actions.
- Admin cannot bid.
- Vehicle deletion is soft-delete (is_deleted = True, is_active = False).
- Upload validation checks extension and MIME type.
- Auction edits are blocked for deleted vehicles.

## Demo Flow for Presentation

1. Log in as admin and open the Admin Dashboard.
2. Show active vs finished auction counts and recent bids.
3. Add a new vehicle and demonstrate live card insertion on client view.
4. Log in as customer and place a bid.
5. Show instant INR price update and bid badge state change.
6. Navigate to My Vehicles to show won listings from finished auctions.

## Troubleshooting

### ModuleNotFoundError: No module named fastapi

Install dependencies using the same interpreter:

```bash
python -m pip install -r temp/requirements.txt
```

### bcrypt/passlib error during register/login

Ensure bcrypt 4.0.1 is installed (already pinned in requirements):

```bash
python -m pip install bcrypt==4.0.1
```

### Unknown database vehicle_auction

Import the schema and seed data first:

```bash
mysql -u root -p < Database.sql
```

### PyWebView not available

The app automatically falls back to web-server mode only. This is expected on environments where pywebview is unavailable.

## Project Structure

```text
.
|- main.py
|- database.py
|- models.py
|- schemas.py
|- Database.sql
|- temp/
|  |- requirements.txt
|- static/
|  |- css/
|  |- js/
|  |- uploads/
|- templates/
|  |- base.html
|  |- index.html
|  |- login.html
|  |- admin.html
|  |- my_vehicles.html
```

## License

This project is intended for academic, portfolio, and internal demonstration use.