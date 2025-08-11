#!/usr/bin/env python3
"""
Test database connection script
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_db_connection():
    """Test PostgreSQL database connection"""
    try:
        # Get database connection details from environment variables
        # Using your Google Cloud SQL instance details
        db_config = {
            'host': os.getenv('DB_HOST', '34.187.201.209'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'vicinoAI123!')
        }
        
        print("🔌 Testing database connection...")
        print(f"Host: {db_config['host']}:{db_config['port']}")
        print(f"Database: {db_config['database']}")
        print(f"User: {db_config['user']}")
        
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        # Test the imageand3durl table
        print("\n📋 Testing imageand3durl table...")
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'imageand3durl'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ Table 'imageand3durl' exists")
            
            # Get table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'imageand3durl' 
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print("📋 Table structure:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM imageand3durl;")
            count = cursor.fetchone()[0]
            print(f"📊 Records in table: {count}")
            
            # Show sample data if any
            if count > 0:
                cursor.execute("SELECT * FROM imageand3durl LIMIT 3;")
                rows = cursor.fetchall()
                print("📄 Sample data:")
                for i, row in enumerate(rows, 1):
                    print(f"  {i}. imageurl: {row[0]}")
                    print(f"     zipurl: {row[1]}")
        else:
            print("❌ Table 'imageand3durl' does not exist")
            print("Creating table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS public.imageand3durl (
                    imageurl TEXT,
                    zipurl TEXT
                );
            """)
            conn.commit()
            print("✅ Table created successfully")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def insert_test_data():
    """Insert the test data you mentioned"""
    try:
        db_config = {
            'host': os.getenv('DB_HOST', '34.187.201.209'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postsql'),
            'password': os.getenv('DB_PASSWORD', 'vicinoAI123!')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print("\n💾 Inserting test data...")
        
        imageurl = "https://example.com/test-image.png"
        zipurl = "https://example.com/test-model.zip"
        
        cursor.execute("""
            INSERT INTO public.imageand3durl (imageurl, zipurl) 
            VALUES (%s, %s)
        """, (imageurl, zipurl))
        
        conn.commit()
        print("✅ Test data inserted successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inserting test data: {e}")

if __name__ == "__main__":
    print("🧪 Database Connection Test")
    print("=" * 50)
    
    if test_db_connection():
        print("\n" + "=" * 50)
        print("🎉 Database connection test completed successfully!")
        
        # Ask if user wants to insert test data
        response = input("\nInsert test data? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            insert_test_data()
    else:
        print("\n" + "=" * 50)
        print("💥 Database connection test failed!")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database credentials in .env file:")
        print("   DB_HOST=localhost")
        print("   DB_PORT=5432")
        print("   DB_NAME=your_database")
        print("   DB_USER=your_username")
        print("   DB_PASSWORD=your_password")
