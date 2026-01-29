#!/usr/bin/env python3
"""
Upload all robot photos from database to AWS S3
"""

import boto3
from robotics_photo_db import RoboticsPhotoDatabase
from pathlib import Path
import json

# Configuration
BUCKET_NAME = 'robotics-marketplace-photos'  # Change this to your desired bucket name
REGION = 'us-east-1'

def create_bucket():
    """Create S3 bucket if it doesn't exist."""
    s3 = boto3.client('s3', region_name=REGION)
    
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"✓ Bucket '{BUCKET_NAME}' already exists")
    except:
        print(f"Creating bucket '{BUCKET_NAME}'...")
        s3.create_bucket(Bucket=BUCKET_NAME)
        print("✓ Bucket created")
    
    # Make bucket public for read access
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
        }]
    }
    
    s3.put_bucket_policy(Bucket=BUCKET_NAME, Policy=json.dumps(bucket_policy))
    print("✓ Bucket configured for public read access")


def upload_photos():
    """Upload all photos from database to S3."""
    s3 = boto3.client('s3', region_name=REGION)
    
    db = RoboticsPhotoDatabase()
    db.connect()
    
    # Get all photos
    db.cursor.execute("""
        SELECT p.photo_id, p.file_path, p.file_name, r.robot_id, rc.category_name
        FROM photos p
        JOIN robots r ON p.robot_id = r.robot_id
        JOIN robot_categories rc ON r.category_id = rc.category_id
    """)
    
    photos = db.cursor.fetchall()
    
    print(f"\nUploading {len(photos)} photos to S3...")
    
    photo_mapping = {}
    
    for photo in photos:
        photo_id = photo['photo_id']
        file_path = Path(photo['file_path'])
        file_name = photo['file_name']
        robot_id = photo['robot_id']
        category = photo['category_name'].lower().replace(' ', '-')
        
        if not file_path.exists():
            print(f"  ⚠ Skipping {file_name} - file not found")
            continue
        
        # Create S3 key: photos/category/robot_id/filename
        s3_key = f"photos/{category}/robot_{robot_id}/{file_name}"
        
        # Upload file
        try:
            # Determine content type based on file extension
            content_type = 'image/jpeg'
            if file_name.lower().endswith('.png'):
                content_type = 'image/png'
            elif file_name.lower().endswith('.webp'):
                content_type = 'image/webp'
            elif file_name.lower().endswith('.gif'):
                content_type = 'image/gif'
            
            s3.upload_file(
                str(file_path),
                BUCKET_NAME,
                s3_key,
                ExtraArgs={'ContentType': content_type}
            )
            
            # Generate public URL
            url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
            photo_mapping[photo_id] = url
            
            print(f"  ✓ Uploaded: {file_name} → {s3_key}")
        except Exception as e:
            print(f"  ✗ Error uploading {file_name}: {e}")
    
    db.close()
    
    # Save mapping to JSON file
    with open('photo_urls.json', 'w') as f:
        json.dump(photo_mapping, f, indent=2)
    
    print(f"\n✓ Upload complete!")
    print(f"✓ Photo URL mapping saved to photo_urls.json")
    print(f"\nYour photos are now at: https://{BUCKET_NAME}.s3.amazonaws.com/photos/")


if __name__ == '__main__':
    print("="*70)
    print("ROBOTICS MARKETPLACE - S3 PHOTO UPLOADER")
    print("="*70)
    print(f"\nBucket: {BUCKET_NAME}")
    print(f"Region: {REGION}")
    
    response = input("\nReady to upload photos to S3? (yes/no): ")
    
    if response.lower() == 'yes':
        create_bucket()
        upload_photos()
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. Check photo_urls.json for all your photo URLs")
        print("2. Your photos are now publicly accessible!")
        print("3. Next: We'll convert your app to use these S3 URLs")
    else:
        print("Upload cancelled.")
