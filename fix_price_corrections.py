#!/usr/bin/env python
"""
Script para arreglar la tabla price_corrections agregando la columna user_id
"""

import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Crear conexión a la BD
if os.getenv("USE_SQLITE") == "True":
    DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(DATABASE_URL)

def check_column_exists(connection, table_name, column_name):
    """Verifica si una columna existe en una tabla"""
    try:
        if os.getenv("USE_SQLITE") == "True":
            result = connection.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]
        else:
            result = connection.execute(text(f"DESCRIBE {table_name}"))
            columns = [row[0] for row in result.fetchall()]
        
        return column_name in columns
    except Exception as e:
        logger.error(f"Error al verificar columna: {str(e)}")
        return False

def add_user_id_column():
    """Agrega la columna user_id a price_corrections"""
    try:
        with engine.connect() as connection:
            logger.info("=== Verificando tabla price_corrections ===")
            
            # Verificar si la columna user_id ya existe
            if check_column_exists(connection, "price_corrections", "user_id"):
                logger.info("✓ La columna user_id ya existe")
                return True
            
            logger.info("Columna user_id no encontrada. Agregando...")
            
            try:
                if os.getenv("USE_SQLITE") == "True":
                    connection.execute(text("ALTER TABLE price_corrections ADD COLUMN user_id INTEGER DEFAULT 1"))
                else:
                    # Para MySQL, primero agregamos sin la restricción FK
                    connection.execute(text("ALTER TABLE price_corrections ADD COLUMN user_id INT NOT NULL DEFAULT 1"))
                
                connection.commit()
                logger.info("✓ Columna user_id agregada exitosamente")
                
                # Verificar que fue agregada
                if check_column_exists(connection, "price_corrections", "user_id"):
                    logger.info("✓ Columna user_id verificada")
                    return True
                else:
                    logger.error("✗ Error al agregar columna user_id")
                    return False
                    
            except Exception as e:
                logger.error(f"Error al agregar columna: {str(e)}")
                connection.rollback()
                raise
                
    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")
        return False

def add_timestamp_column():
    """Agrega la columna timestamp a price_corrections si no existe"""
    try:
        with engine.connect() as connection:
            # Verificar si la columna timestamp ya existe
            if not check_column_exists(connection, "price_corrections", "timestamp"):
                logger.info("Agregando columna timestamp...")
                
                if os.getenv("USE_SQLITE") == "True":
                    connection.execute(text("ALTER TABLE price_corrections ADD COLUMN timestamp TEXT DEFAULT CURRENT_TIMESTAMP"))
                else:
                    connection.execute(text("ALTER TABLE price_corrections ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"))
                
                connection.commit()
                logger.info("✓ Columna timestamp agregada")
            else:
                logger.info("✓ Columna timestamp ya existe")
            
            return True
            
    except Exception as e:
        logger.error(f"Error al agregar columna timestamp: {str(e)}")
        return False

def verify_table_structure():
    """Verifica la estructura actual de la tabla"""
    try:
        with engine.connect() as connection:
            logger.info("\n=== Estructura de price_corrections ===")
            
            if os.getenv("USE_SQLITE") == "True":
                result = connection.execute(text("PRAGMA table_info(price_corrections)"))
                for row in result.fetchall():
                    logger.info(f"  {row[1]}: {row[2]}")
            else:
                result = connection.execute(text("DESCRIBE price_corrections"))
                for row in result.fetchall():
                    logger.info(f"  {row[0]}: {row[1]}")
            
            return True
    except Exception as e:
        logger.error(f"Error al verificar estructura: {str(e)}")
        return False

def main():
    try:
        logger.info("╔════════════════════════════════════════════╗")
        logger.info("║ Fix Price Corrections - esquelAhorra API  ║")
        logger.info("╚════════════════════════════════════════════╝")
        
        # Agregar columnas faltantes
        if not add_user_id_column():
            logger.error("✗ Error al agregar columna user_id")
            return False
        
        if not add_timestamp_column():
            logger.error("✗ Error al agregar columna timestamp")
            return False
        
        # Verificar estructura final
        if not verify_table_structure():
            logger.error("✗ Error al verificar estructura")
            return False
        
        logger.info("\n✓ Todas las correcciones completadas exitosamente")
        logger.info("Puedes reiniciar tu servidor FastAPI ahora.")
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
