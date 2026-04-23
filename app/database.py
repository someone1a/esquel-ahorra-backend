from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

USE_SQLITE = os.getenv("USE_SQLITE", "False").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Validar que existan las variables de entorno necesarias
    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Variables de entorno faltantes para MySQL: {missing_vars}")
    
    DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en sesión de BD: {str(e)}")
        db.close()
        raise
    finally:
        db.close()

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"Error al crear tablas: {str(e)}")
        raise

def verify_database_connection():
    """Verifica que la conexión a la base de datos sea válida"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Conexión a base de datos verificada")
            return True
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {str(e)}")
        return False