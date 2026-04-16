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
    is_deleted     BOOLEAN        NOT NULL DEFAULT FALSE,
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

-- Sample vehicles (prices are stored in INR)
-- Mix: primarily Indian-market vehicles with a few international imports.
INSERT INTO vehicles (title, description, image_url, starting_price, current_price, auction_end) VALUES
(
    '2024 Tata Nexon EV Max',
    'Top-spec electric SUV in Pristine White with ventilated seats, 360 camera, and connected car features.',
    NULL,
    1650000.00, 1650000.00,
    DATE_ADD(NOW(), INTERVAL 3 DAY)
),
(
    '2023 Mahindra XUV700 AX7L Diesel AT',
    '7-seater premium SUV with ADAS, panoramic sunroof, Sony 3D audio, and full service record.',
    NULL,
    2375000.00, 2375000.00,
    DATE_ADD(NOW(), INTERVAL 5 DAY)
),
(
    '2022 Hyundai Creta SX(O) Diesel',
    'Well-maintained compact SUV with Bose audio, panoramic sunroof, and low ownership cost.',
    NULL,
    1590000.00, 1590000.00,
    DATE_ADD(NOW(), INTERVAL 2 DAY)
),
(
    '2023 Maruti Suzuki Grand Vitara Alpha AT',
    'Strong-hybrid variant with 360-view camera, premium interiors, and excellent city mileage.',
    NULL,
    1740000.00, 1740000.00,
    DATE_ADD(NOW(), INTERVAL 7 DAY)
),
(
    '2021 Toyota Fortuner Legender 4x4 AT',
    'Flagship diesel SUV in pearl white-black dual tone, single owner, highway driven.',
    NULL,
    3850000.00, 3850000.00,
    DATE_ADD(NOW(), INTERVAL 4 DAY)
),
(
    '2024 Kia Seltos X-Line Turbo DCT',
    'Turbo-petrol SUV with ADAS Level 2, premium matte finish, and connected technology pack.',
    NULL,
    1925000.00, 1925000.00,
    DATE_ADD(NOW(), INTERVAL 6 DAY)
),
(
    '2022 BMW 330Li M Sport (Imported)',
    'Long-wheelbase luxury sedan with adaptive suspension, gesture control, and premium Harman Kardon audio.',
    NULL,
    4800000.00, 4800000.00,
    DATE_ADD(NOW(), INTERVAL 8 DAY)
),
(
    '2021 Mercedes-Benz GLC 300 4MATIC (Imported)',
    'Petrol AWD luxury SUV with panoramic roof, digital cockpit, and full dealership service history.',
    NULL,
    5675000.00, 5675000.00,
    DATE_ADD(NOW(), INTERVAL 6 DAY)
);

-- Finished auctions with winners (users 2 and 3)
INSERT INTO vehicles (
    title, description, image_url, starting_price, current_price,
    auction_end, is_active, owner_id
) VALUES
(
    '2020 Skoda Octavia RS 245',
    'Performance sedan with virtual cockpit, paddle shifters, and full service history. Auction closed with competitive bidding.',
    NULL,
    2250000.00, 2485000.00,
    DATE_SUB(NOW(), INTERVAL 2 DAY),
    FALSE, 2
),
(
    '2021 MG Hector Plus Sharp Diesel',
    'Family SUV with captain seats, panoramic sunroof, and connected tech package. Recently completed auction.',
    NULL,
    1790000.00, 1960000.00,
    DATE_SUB(NOW(), INTERVAL 1 DAY),
    FALSE, 3
),
(
    '2019 Honda City ZX CVT',
    'Reliable premium sedan with low maintenance profile and clean ownership records. Sold in a finished auction.',
    NULL,
    980000.00, 1115000.00,
    DATE_SUB(NOW(), INTERVAL 3 DAY),
    FALSE, 2
);

-- Sample bids covering finished auctions and one active auction
-- Vehicle IDs are deterministic after table reset:
-- 1-8 active, 9-11 finished.
INSERT INTO bids (amount, user_id, vehicle_id, created_at) VALUES
(2320000.00, 3, 9, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(2485000.00, 2, 9, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(1885000.00, 2, 10, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(1960000.00, 3, 10, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(1045000.00, 3, 11, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(1115000.00, 2, 11, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(2410000.00, 3, 2, DATE_SUB(NOW(), INTERVAL 6 HOUR));
