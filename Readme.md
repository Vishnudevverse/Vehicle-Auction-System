# 🚗 Vehicle Auction System

A real-time vehicle auction platform built with **FastAPI**, **MySQL**, and **WebSockets**. This project features a dual-module system for Admins and Clients, ensuring high-speed bidding and automated inventory management.

## 🌟 Key Features

* **Real-Time Bidding:** Powered by WebSockets so users see price updates instantly.
* **Admin Dashboard:** Manage vehicle inventory and bidding periods.
* **Automated Ownership:** Vehicles are automatically moved to the "My Vehicles" section for the highest bidder once the auction ends.
* **Responsive UI:** Built with **Bootstrap 5** for a professional, modern look.

---

## 🛠️ Installation & Setup

Follow these steps to get the project running locally:

### 1. Install Dependencies

Ensure you have Python installed, then run the following command to install required libraries:

```bash
pip install -r temp/requirements.txt

```

### 2. Database Configuration

1. Open your terminal or Command Prompt.
2. Log into MySQL and import the database schema:

```bash
mysql -u root -p < Database.sql

```

### 3. Environment Setup

Create a `.env` file in the root directory and paste the following configuration:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=1234
DB_NAME=vehicle_auction
DB_PORT=3306
SECRET_KEY=auction-secret-key-change-in-production

```

---

## 🚀 Running the Application

Start the FastAPI server using Python:

```bash
python main.py

```

Once the server is running, open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📂 Project Architecture

* **Frontend:** HTML5, CSS3, JavaScript (Vanilla), Bootstrap 5.
* **Backend:** FastAPI (Python 3.x).
* **Database:** MySQL (Relational Schema).
* **Communication:** WebSockets for live updates.

---

## ❓ FAQ

### 1) How do I install dependencies?

Run:

```bash
pip install -r temp/requirements.txt
```

If `pip` is not recognized, use `python -m pip install -r temp/requirements.txt`.

### 2) How do I initialize the database?

Import the SQL schema and sample data:

```bash
mysql -u root -p < Database.sql
```

Make sure your `.env` values match the database you imported.

### 3) What are the default sample login accounts?

From `Database.sql`:

* Admin: `admin` / `admin123`
* Client: `john_doe` / `password123`
* Client: `jane_smith` / `password123`

### 4) Why can the admin not place bids?

This is intentional. The backend blocks admin bidding (`/api/bids` returns 403 for admin users), and the UI disables bid actions for admins.

### 5) Why does ownership not update exactly when auction time ends?

Auctions are finalized by `finalize_auctions(db)`, which runs when key pages/API routes are accessed. That means ownership assignment is request-driven, not a background scheduler.

### 6) Why did my bid fail with "Bid must be greater than current price"?

Your bid amount must be strictly greater than the current price. The frontend suggests a higher minimum (current + 100) in the modal, but the backend rule is simply `amount > current_price`.

### 7) Why am I seeing "Login required to place a bid"?

Bidding uses session authentication. Log in first from `/login`, then place bids from the homepage.

### 8) Why are real-time updates not appearing?

Check these points:

* The browser is connected to `/ws/auction` (look for the live/reconnecting status badge).
* You are opening the app from the same FastAPI server host/port.
* No proxy/firewall is blocking WebSocket traffic.

### 9) Where are uploaded vehicle images stored?

Uploaded files are saved in:

* `static/uploads/`

Image paths are stored as `/static/uploads/<filename>` in the database.

### 10) Is vehicle deletion permanent?

No. Admin deletion is a soft-delete:

* `is_deleted = True`
* `is_active = False`

Records stay in the database for audit/history.

### 11) Why does running `python main.py` open a desktop window?

`main.py` starts Uvicorn in a thread and launches a PyWebView admin GUI. This is expected behavior in this project.

If you only want the web server, run:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 12) Where can I view API docs?

Once running, open:

* `http://127.0.0.1:8000/docs`

### 13) What environment variables are required?

In `.env`:

* `DB_HOST`
* `DB_USER`
* `DB_PASSWORD`
* `DB_NAME`
* `DB_PORT`
* `SECRET_KEY`

Defaults exist in code, but production should always use explicit secure values.

### 14) Do passwords use hashing?

Yes. New registrations are stored with bcrypt hashing via Passlib.

For backward compatibility, legacy plain-text passwords from older seed data can still log in and are upgraded to hashed format on successful login.

### 15) Why does `/admin` redirect me to login?

You must be authenticated and have `is_admin=True`. Non-admin users are redirected to `/login`.