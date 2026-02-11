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