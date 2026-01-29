#!/usr/bin/env python3
"""
Robotics Photo Database Manager
A system for organizing and managing photos of drones, AMRs, and robotic arms.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class RoboticsPhotoDatabase:
    """Main database management class for robotics photos."""
    
    def __init__(self, db_path: str = "robotics_photos.db", photo_storage: str = "photo_storage"):
        """
        Initialize the database connection and photo storage.
        
        Args:
            db_path: Path to SQLite database file
            photo_storage: Directory for storing photos
        """
        self.db_path = db_path
        self.photo_storage = Path(photo_storage)
        self.conn = None
        self.cursor = None
        
        # Create photo storage directories
        self.photo_storage.mkdir(exist_ok=True)
        for category in ['drones', 'amrs', 'robotic_arms']:
            (self.photo_storage / category).mkdir(exist_ok=True)
    
    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def initialize_database(self, schema_file: str = "database_schema.sql"):
        """Initialize database with schema."""
        self.connect()
        with open(schema_file, 'r') as f:
            schema = f.read()
            self.cursor.executescript(schema)
        self.conn.commit()
        print("Database initialized successfully!")
    
    def add_robot(self, category_name: str, manufacturer: str, model_name: str,
                  robot_type: str, year_released: Optional[int] = None,
                  specifications: Optional[str] = None) -> int:
        """
        Add a new robot to the database.
        
        Returns:
            robot_id of the newly created robot
        """
        # Get category_id
        self.cursor.execute(
            "SELECT category_id FROM robot_categories WHERE category_name = ?",
            (category_name,)
        )
        result = self.cursor.fetchone()
        if not result:
            raise ValueError(f"Category '{category_name}' not found")
        
        category_id = result[0]
        
        self.cursor.execute("""
            INSERT INTO robots (category_id, manufacturer, model_name, robot_type, 
                              year_released, specifications)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category_id, manufacturer, model_name, robot_type, year_released, specifications))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_photo(self, robot_id: int, source_file: str, photo_type: str = "general",
                  description: Optional[str] = None, tags: Optional[List[str]] = None,
                  photographer: Optional[str] = None) -> int:
        """
        Add a photo to the database and copy it to storage.
        
        Returns:
            photo_id of the newly added photo
        """
        source_path = Path(source_file)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        # Get robot info to determine storage category
        self.cursor.execute("""
            SELECT rc.category_name 
            FROM robots r
            JOIN robot_categories rc ON r.category_id = rc.category_id
            WHERE r.robot_id = ?
        """, (robot_id,))
        result = self.cursor.fetchone()
        if not result:
            raise ValueError(f"Robot with ID {robot_id} not found")
        
        category = result[0].lower().replace(' ', '_')
        
        # Create destination path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{timestamp}_{source_path.name}"
        dest_path = self.photo_storage / category / file_name
        
        # Copy file to storage
        shutil.copy2(source_path, dest_path)
        
        # Get file info
        file_size_kb = dest_path.stat().st_size // 1024
        
        # Insert photo record
        self.cursor.execute("""
            INSERT INTO photos (robot_id, file_name, file_path, upload_date, photo_type,
                              file_size_kb, description, photographer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (robot_id, file_name, str(dest_path), datetime.now().date().isoformat(),
              photo_type, file_size_kb, description, photographer))
        
        photo_id = self.cursor.lastrowid
        
        # Add tags if provided
        if tags:
            for tag_name in tags:
                self.add_tag_to_photo(photo_id, tag_name)
        
        self.conn.commit()
        return photo_id
    
    def add_tag_to_photo(self, photo_id: int, tag_name: str):
        """Add a tag to a photo."""
        # Insert tag if it doesn't exist
        self.cursor.execute(
            "INSERT OR IGNORE INTO tags (tag_name) VALUES (?)",
            (tag_name,)
        )
        
        # Get tag_id
        self.cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_name,))
        tag_id = self.cursor.fetchone()[0]
        
        # Link photo and tag
        self.cursor.execute(
            "INSERT OR IGNORE INTO photo_tags (photo_id, tag_id) VALUES (?, ?)",
            (photo_id, tag_id)
        )
        self.conn.commit()
    
    def search_photos(self, category: Optional[str] = None, manufacturer: Optional[str] = None,
                     model: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict]:
        """
        Search for photos based on various criteria.
        
        Returns:
            List of photo records with robot information
        """
        query = """
            SELECT p.photo_id, p.file_name, p.file_path, p.upload_date, p.photo_type,
                   p.description, r.manufacturer, r.model_name, rc.category_name
            FROM photos p
            JOIN robots r ON p.robot_id = r.robot_id
            JOIN robot_categories rc ON r.category_id = rc.category_id
            WHERE 1=1
        """
        params = []
        
        if category:
            query += " AND rc.category_name = ?"
            params.append(category)
        
        if manufacturer:
            query += " AND r.manufacturer LIKE ?"
            params.append(f"%{manufacturer}%")
        
        if model:
            query += " AND r.model_name LIKE ?"
            params.append(f"%{model}%")
        
        if tags:
            query += """ AND p.photo_id IN (
                SELECT pt.photo_id FROM photo_tags pt
                JOIN tags t ON pt.tag_id = t.tag_id
                WHERE t.tag_name IN ({})
            )""".format(','.join('?' * len(tags)))
            params.extend(tags)
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        # Total photos
        self.cursor.execute("SELECT COUNT(*) FROM photos")
        stats['total_photos'] = self.cursor.fetchone()[0]
        
        # Photos by category
        self.cursor.execute("""
            SELECT rc.category_name, COUNT(p.photo_id) as count
            FROM robot_categories rc
            LEFT JOIN robots r ON rc.category_id = r.category_id
            LEFT JOIN photos p ON r.robot_id = p.robot_id
            GROUP BY rc.category_name
        """)
        stats['by_category'] = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        # Total robots
        self.cursor.execute("SELECT COUNT(*) FROM robots")
        stats['total_robots'] = self.cursor.fetchone()[0]
        
        # Total storage size
        self.cursor.execute("SELECT SUM(file_size_kb) FROM photos")
        total_kb = self.cursor.fetchone()[0] or 0
        stats['total_storage_mb'] = round(total_kb / 1024, 2)
        
        return stats
    
    def list_all_robots(self) -> List[Dict]:
        """List all robots in the database."""
        self.cursor.execute("""
            SELECT r.robot_id, r.manufacturer, r.model_name, r.robot_type,
                   r.year_released, rc.category_name,
                   COUNT(p.photo_id) as photo_count
            FROM robots r
            JOIN robot_categories rc ON r.category_id = rc.category_id
            LEFT JOIN photos p ON r.robot_id = p.robot_id
            GROUP BY r.robot_id
            ORDER BY rc.category_name, r.manufacturer, r.model_name
        """)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def export_catalog(self, output_file: str = "catalog.txt"):
        """Export a text catalog of all robots and photos."""
        robots = self.list_all_robots()
        
        with open(output_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ROBOTICS PHOTO DATABASE CATALOG\n")
            f.write("=" * 80 + "\n\n")
            
            for robot in robots:
                f.write(f"\n{robot['category_name']}: {robot['manufacturer']} {robot['model_name']}\n")
                f.write(f"  Type: {robot['robot_type']}\n")
                if robot['year_released']:
                    f.write(f"  Year: {robot['year_released']}\n")
                f.write(f"  Photos: {robot['photo_count']}\n")
                f.write("-" * 80 + "\n")
        
        print(f"Catalog exported to {output_file}")


def main():
    """Example usage of the database."""
    db = RoboticsPhotoDatabase()
    
    # Initialize database
    if not os.path.exists(db.db_path):
        db.initialize_database()
    
    db.connect()
    
    # Print statistics
    stats = db.get_statistics()
    print("\nDatabase Statistics:")
    print(f"  Total Photos: {stats['total_photos']}")
    print(f"  Total Robots: {stats['total_robots']}")
    print(f"  Storage Used: {stats['total_storage_mb']} MB")
    print("\nPhotos by Category:")
    for category, count in stats['by_category'].items():
        print(f"  {category}: {count}")
    
    db.close()


if __name__ == "__main__":
    main()
