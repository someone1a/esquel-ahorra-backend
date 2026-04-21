"""
Script de migración para actualizar registros existentes
Ejecutar: python migrations.py
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import logging

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

def migrate_null_is_active():
    """Actualiza registros con is_active = NULL a is_active = 1 (True)"""
    try:
        with engine.connect() as connection:
            # Verificar si la tabla existe
            logger.info("Verificando tabla 'locals'...")
            
            # Contar registros con is_active NULL
            result = connection.execute(text("SELECT COUNT(*) as count FROM locals WHERE is_active IS NULL"))
            count = result.fetchone()[0]
            
            if count > 0:
                logger.info(f"Encontrados {count} registros con is_active = NULL")
                
                # Actualizar a True (1)
                logger.info("Actualizando registros...")
                connection.execute(text("UPDATE locals SET is_active = 1 WHERE is_active IS NULL"))
                connection.commit()
                
                logger.info(f"✓ {count} registros actualizados a is_active = TRUE")
            else:
                logger.info("✓ No hay registros con is_active = NULL. Todo está bien.")
            
            # Verificar que no hay más NULLs
            result = connection.execute(text("SELECT COUNT(*) as count FROM locals WHERE is_active IS NULL"))
            final_count = result.fetchone()[0]
            
            if final_count == 0:
                logger.info("✓ Migración completada exitosamente")
                return True
            else:
                logger.error(f"✗ Aún hay {final_count} registros con is_active = NULL")
                return False
                
    except Exception as e:
        logger.error(f"✗ Error en migración: {str(e)}")
        return False

def check_table_structure():
    """Verifica la estructura de la tabla"""
    try:
        with engine.connect() as connection:
            logger.info("\nVerificando estructura de tabla 'locals'...")
            
            if os.getenv("USE_SQLITE") == "True":
                result = connection.execute(text("PRAGMA table_info(locals)"))
            else:
                result = connection.execute(text("DESCRIBE locals"))
            
            rows = result.fetchall()
            for row in rows:
                logger.info(f"  {row}")
            
            return True
    except Exception as e:
        logger.error(f"✗ Error al verificar estructura: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== Iniciando Migración ===")
    
    # Verificar estructura
    check_table_structure()
    
    # Ejecutar migración
    logger.info("\n=== Ejecutando Migración ===")
    success = migrate_null_is_active()
    
    if success:
        logger.info("\n✓ Migración completada correctamente")
        exit(0)
    else:
        logger.info("\n✗ Migración falló")
        exit(1)
