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

def migrate_price_corrections():
    """Agrega columnas user_id y status a price_corrections"""
    try:
        with engine.connect() as connection:
            logger.info("Verificando tabla 'price_corrections'...")
            
            # Verificar si ya existe la columna user_id
            if os.getenv("USE_SQLITE") == "True":
                result = connection.execute(text("PRAGMA table_info(price_corrections)"))
                columns = [row[1] for row in result.fetchall()]
            else:
                result = connection.execute(text("DESCRIBE price_corrections"))
                columns = [row[0] for row in result.fetchall()]
            
            if "user_id" not in columns:
                logger.info("Agregando columna 'user_id'...")
                if os.getenv("USE_SQLITE") == "True":
                    connection.execute(text("ALTER TABLE price_corrections ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1"))
                else:
                    connection.execute(text("ALTER TABLE price_corrections ADD COLUMN user_id INT NOT NULL"))
                logger.info("✓ Columna 'user_id' agregada")
            
            if "status" not in columns:
                logger.info("Agregando columna 'status'...")
                if os.getenv("USE_SQLITE") == "True":
                    connection.execute(text("ALTER TABLE price_corrections ADD COLUMN status TEXT DEFAULT 'approved'"))
                else:
                    connection.execute(text("ALTER TABLE price_corrections ADD COLUMN status VARCHAR(20) DEFAULT 'approved'"))
                logger.info("✓ Columna 'status' agregada")
            
            # Actualizar registros existentes a 'approved' si no tienen status
            logger.info("Actualizando registros existentes...")
            connection.execute(text("UPDATE price_corrections SET status = 'approved' WHERE status IS NULL"))
            connection.commit()
            
            logger.info("✓ Migración de price_corrections completada")
            return True
    except Exception as e:
        logger.error(f"✗ Error en migración de price_corrections: {str(e)}")
        return False
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

def migrate_products_to_prices():
    """Migra precio y local_id de products a nueva tabla prices"""
    try:
        with engine.connect() as connection:
            logger.info("Verificando tabla 'products'...")
            
            # Verificar si existe tabla prices
            if os.getenv("USE_SQLITE") == "True":
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'"))
            else:
                result = connection.execute(text("SHOW TABLES LIKE 'prices'"))
            
            if not result.fetchone():
                logger.info("Creando tabla 'prices'...")
                if os.getenv("USE_SQLITE") == "True":
                    connection.execute(text("""
                        CREATE TABLE prices (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_id INTEGER NOT NULL,
                            local_id INTEGER NOT NULL,
                            precio REAL NOT NULL,
                            FOREIGN KEY (product_id) REFERENCES products (id)
                        )
                    """))
                else:
                    connection.execute(text("""
                        CREATE TABLE prices (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            product_id INT NOT NULL,
                            local_id INT NOT NULL,
                            precio FLOAT NOT NULL,
                            FOREIGN KEY (product_id) REFERENCES products (id)
                        )
                    """))
                connection.commit()
                logger.info("✓ Tabla 'prices' creada")
            
            # Migrar datos
            logger.info("Migrando datos de products a prices...")
            result = connection.execute(text("SELECT id, precio, local_id FROM products"))
            products = result.fetchall()
            
            for product in products:
                product_id, precio, local_id = product
                connection.execute(text("INSERT INTO prices (product_id, local_id, precio) VALUES (?, ?, ?)"), (product_id, local_id, precio))
            
            connection.commit()
            logger.info(f"✓ Migrados {len(products)} precios")
            
            # Dropear columnas precio y local_id de products
            logger.info("Eliminando columnas precio y local_id de products...")
            if os.getenv("USE_SQLITE") == "True":
                # SQLite no soporta DROP COLUMN fácilmente, así que recrear tabla
                logger.info("Para SQLite, es necesario recrear la tabla manualmente o usar una herramienta externa")
                logger.info("Columnas precio y local_id deben ser eliminadas manualmente")
            else:
                connection.execute(text("ALTER TABLE products DROP COLUMN precio"))
                connection.execute(text("ALTER TABLE products DROP COLUMN local_id"))
                connection.commit()
                logger.info("✓ Columnas eliminadas de products")
            
            return True
    except Exception as e:
        logger.error(f"✗ Error en migración de products: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== Iniciando Migración ===")
    
    # Ejecutar migración
    logger.info("\n=== Ejecutando Migración ===")
    success = migrate_null_is_active()
    
    if success:
        logger.info("\n=== Ejecutando Migración de Products ===")
        success_products = migrate_products_to_prices()
        if success_products:
            logger.info("\n=== Ejecutando Migración de Price Corrections ===")
            success_corrections = migrate_price_corrections()
            if success_corrections:
                logger.info("\n✓ Todas las migraciones completadas correctamente")
                exit(0)
            else:
                logger.info("\n✗ Migración de price_corrections falló")
                exit(1)
        else:
            logger.info("\n✗ Migración de products falló")
            exit(1)
    else:
        logger.info("\n✗ Migración falló")
        exit(1)
