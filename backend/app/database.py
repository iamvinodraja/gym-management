import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gym_db")

# Load configuration from environment or .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = BASE_DIR / ".env"

if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

DATABASE_TYPE = os.getenv("DATABASE_TYPE", "auto").lower()

# Supabase / PostgreSQL Configuration
DEFAULT_SUPABASE_URL = "postgresql://postgres:Passwardhacked123@db.hhwdtcmcotqmieigmdxx.supabase.co:5432/postgres"
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or DEFAULT_SUPABASE_URL

# MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "gym_management")

# SQLite fallback path
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "gym_management.db")

engine = None
db_selected = "sqlite"
last_db_error = None

# 1. Try Supabase / PostgreSQL if URL provided
if SUPABASE_DB_URL and SUPABASE_DB_URL.strip():
    try:
        url = SUPABASE_DB_URL.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        # Connect with SSL requirement for Supabase
        pg_engine = create_engine(
            url,
            pool_recycle=300,
            pool_pre_ping=True,
            connect_args={"sslmode": "require"} if "localhost" not in url and "127.0.0.1" not in url else {}
        )
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        engine = pg_engine
        db_selected = "supabase"
        logger.info("Successfully connected to Supabase PostgreSQL database!")
    except Exception as e:
        last_db_error = str(e)
        logger.warning(f"Failed to connect to Supabase PostgreSQL ({e}). Checking alternative databases...")

# 2. Try MySQL if Supabase wasn't connected and DATABASE_TYPE is mysql or auto
if engine is None and DATABASE_TYPE in ("mysql", "auto"):
    try:
        import pymysql
        pwd = MYSQL_PASSWORD or ""
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=int(MYSQL_PORT),
            user=MYSQL_USER,
            password=pwd,
            connect_timeout=2
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        conn.close()

        mysql_url = f"mysql+pymysql://{MYSQL_USER}:{pwd}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
        mysql_engine = create_engine(mysql_url, pool_recycle=3600, pool_pre_ping=True)
        with mysql_engine.connect() as test_conn:
            test_conn.execute(text("SELECT 1"))

        engine = mysql_engine
        db_selected = "mysql"
        logger.info(f"Connected successfully to MySQL database '{MYSQL_DATABASE}' at {MYSQL_HOST}:{MYSQL_PORT}")
    except Exception as e:
        if DATABASE_TYPE == "mysql":
            logger.error(f"Failed to connect to required MySQL database: {e}")
            raise
        else:
            logger.info("MySQL not configured or password required. Proceeding with fallback.")

# 3. Fallback to SQLite
if engine is None:
    sqlite_file = BASE_DIR / "backend" / SQLITE_DB_PATH
    sqlite_url = f"sqlite:///{sqlite_file}"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    db_selected = "sqlite"
    logger.info(f"Using SQLite database at {sqlite_file}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_active_db_type():
    return db_selected

def get_db_error():
    return last_db_error
