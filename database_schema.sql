-- Robotics Photo Database Schema

CREATE TABLE robot_categories (
    category_id INTEGER PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    description TEXT
);

CREATE TABLE robots (
    robot_id INTEGER PRIMARY KEY,
    category_id INTEGER,
    manufacturer VARCHAR(100),
    model_name VARCHAR(100),
    robot_type VARCHAR(50),
    year_released INTEGER,
    specifications TEXT,
    FOREIGN KEY (category_id) REFERENCES robot_categories(category_id)
);

CREATE TABLE photos (
    photo_id INTEGER PRIMARY KEY,
    robot_id INTEGER,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    upload_date DATE,
    photo_type VARCHAR(50), -- e.g., 'front view', 'side view', 'in operation'
    resolution VARCHAR(20),
    file_size_kb INTEGER,
    tags TEXT,
    description TEXT,
    photographer VARCHAR(100),
    FOREIGN KEY (robot_id) REFERENCES robots(robot_id)
);

CREATE TABLE tags (
    tag_id INTEGER PRIMARY KEY,
    tag_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE photo_tags (
    photo_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (photo_id, tag_id),
    FOREIGN KEY (photo_id) REFERENCES photos(photo_id),
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
);

-- Insert default categories
INSERT INTO robot_categories (category_id, category_name, description) VALUES
(1, 'Drones', 'Unmanned aerial vehicles (UAVs) for various applications'),
(2, 'AMRs', 'Autonomous Mobile Robots for logistics and transportation'),
(3, 'Robotic Arms', 'Industrial and collaborative robotic manipulators');
