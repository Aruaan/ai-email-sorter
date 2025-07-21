from dotenv import load_dotenv
load_dotenv()

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Remote (Render) DB config
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')

# Local DB config
LOCAL_POSTGRES_USER = os.getenv('LOCAL_POSTGRES_USER')
LOCAL_POSTGRES_PASSWORD = os.getenv('LOCAL_POSTGRES_PASSWORD')
LOCAL_POSTGRES_DB = os.getenv('LOCAL_POSTGRES_DB')
LOCAL_POSTGRES_HOST = os.getenv('LOCAL_POSTGRES_HOST')
LOCAL_POSTGRES_PORT = os.getenv('LOCAL_POSTGRES_PORT')

print("POSTGRES_USER:", POSTGRES_USER)
print("POSTGRES_PASSWORD:", POSTGRES_PASSWORD)
print("POSTGRES_DB:", POSTGRES_DB)
print("POSTGRES_HOST:", POSTGRES_HOST)

# Pick config
if all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST]):
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
else:
    DATABASE_URL = f"postgresql://{LOCAL_POSTGRES_USER}:{LOCAL_POSTGRES_PASSWORD}@{LOCAL_POSTGRES_HOST}:{LOCAL_POSTGRES_PORT}/{LOCAL_POSTGRES_DB}"
    print("Using local PostgreSQL database")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# test_db_connection.py
from db import SessionLocal

def test_db():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        print("✅ Successfully connected to the database.")
    except Exception as e:
        print("❌ Failed to connect:", e)
    finally:
        db.close()

if __name__ == "__main__":
    test_db()

