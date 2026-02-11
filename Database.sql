-- ============================================
-- Vehicle Auction System — Database Schema
-- ============================================

CREATE DATABASE IF NOT EXISTS vehicle_auction;
USE vehicle_auction;

-- ── Drop existing tables (order matters for FK) ──
DROP TABLE IF EXISTS bids;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS users;

-- ── Users ────────────────────────────────────
CREATE TABLE users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    email       VARCHAR(120) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    is_admin    BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ── Vehicles ─────────────────────────────────
CREATE TABLE vehicles (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(120)   NOT NULL,
    description    TEXT,
    image_url      VARCHAR(500)   DEFAULT NULL,
    starting_price DECIMAL(12,2)  NOT NULL,
    current_price  DECIMAL(12,2)  NOT NULL,
    auction_end    DATETIME       NOT NULL,
    is_active      BOOLEAN        NOT NULL DEFAULT TRUE,
    owner_id       INT            DEFAULT NULL,
    created_at     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ── Bids ─────────────────────────────────────
CREATE TABLE bids (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    amount      DECIMAL(12,2) NOT NULL,
    user_id     INT NOT NULL,
    vehicle_id  INT NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- Sample Data
-- ============================================

-- Admin user  (password: admin123)
INSERT INTO users (username, email, password, is_admin) VALUES
('admin', 'admin@auction.com', 'admin123', TRUE);

-- Regular users
INSERT INTO users (username, email, password) VALUES
('john_doe',  'john@example.com',  'password123'),
('jane_smith','jane@example.com',  'password123');

-- Sample vehicles (image_url = NULL → placeholder will render)
INSERT INTO vehicles (title, description, image_url, starting_price, current_price, auction_end) VALUES
(
    '2023 Tesla Model S',
    'Fully loaded Long Range with autopilot. Pearl white exterior, black leather interior. Only 8,200 miles.',
    NULL,
    45000.00, 45000.00,
    DATE_ADD(NOW(), INTERVAL 3 DAY)
),
(
    '2022 Ford Mustang GT',
    'Race Red, 5.0L V8, 6-speed manual. Performance package with Brembo brakes and MagneRide suspension.',
    NULL,
    38000.00, 38000.00,
    DATE_ADD(NOW(), INTERVAL 5 DAY)
),
(
    '2024 BMW M4 Competition',
    'Alpine White with carbon-fiber roof. Twin-turbo inline-6 producing 503 hp. Under factory warranty.',
    NULL,
    72000.00, 72000.00,
    DATE_ADD(NOW(), INTERVAL 2 DAY)
),
(
    '2021 Porsche 911 Carrera',
    'GT Silver Metallic, PDK transmission, Sport Chrono package. Certified pre-owned with 15,000 miles.',
    NULL,
    95000.00, 95000.00,
    DATE_ADD(NOW(), INTERVAL 7 DAY)
),
(
    '2023 Mercedes-AMG C63',
    'Obsidian Black, Burmester sound system, heads-up display. Hybrid turbo-4 with 671 hp combined output.',
    NULL,
    68000.00, 68000.00,
    DATE_ADD(NOW(), INTERVAL 4 DAY)
),
(
    '2022 Chevrolet Corvette C8',
    'Rapid Blue with natural dipped interior. 6.2L V8, Z51 performance package, front-lift system.',
    NULL,
    62000.00, 62000.00,
    DATE_ADD(NOW(), INTERVAL 6 DAY)
);
