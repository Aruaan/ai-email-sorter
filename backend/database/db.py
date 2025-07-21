from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)
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

print("LOCAL_POSTGRES_USER:", LOCAL_POSTGRES_USER)
print("LOCAL_POSTGRES_PASSWORD:", LOCAL_POSTGRES_PASSWORD)
print("LOCAL_POSTGRES_DB:", LOCAL_POSTGRES_DB)
print("LOCAL_POSTGRES_HOST:", LOCAL_POSTGRES_HOST)
print("LOCAL_POSTGRES_PORT:", LOCAL_POSTGRES_PORT)

# Pick config
if all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST]):
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
else:
    DATABASE_URL = f"postgresql://{LOCAL_POSTGRES_USER}:{LOCAL_POSTGRES_PASSWORD}@{LOCAL_POSTGRES_HOST}:{LOCAL_POSTGRES_PORT}/{LOCAL_POSTGRES_DB}"
    print("Using local PostgreSQL database")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

