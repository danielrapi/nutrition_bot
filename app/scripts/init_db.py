import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Database

def main():
    """Initialize the database with required tables"""
    print("Initializing database...")
    db = Database()
    db.create_tables()
    print("Database initialization complete!")

if __name__ == "__main__":
    main()