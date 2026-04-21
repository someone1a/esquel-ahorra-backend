#!/usr/bin/env python
"""
Script de migración para separar barcodes en una tabla independiente.
Migra los códigos de barra existentes desde la tabla products a la tabla barcodes.
"""

import logging
from sqlalchemy import text
from app.database import engine, get_db
from app.models.product import Product, Barcode, Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_tables():
    """Crea las nuevas tablas si no existen"""
    try:
        logger.info("=== Creando nuevas tablas ===")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"✗ Error al crear tablas: {str(e)}")
        raise

def migrate_barcodes():
    """Migra barcodes existentes desde products a barcodes"""
    try:
        logger.info("=== Iniciando migración de barcodes ===")
        
        with engine.connect() as connection:
            # Verificar si la columna codigo_barra existe en products
            result = connection.execute(
                text("SELECT COUNT(*) as count FROM products WHERE codigo_barra IS NOT NULL")
            )
            count = result.fetchone()[0]
            
            if count == 0:
                logger.info("✓ No hay barcodes para migrar")
                connection.commit()
                return
            
            logger.info(f"Encontrados {count} registros con barcodes para migrar")
            
            # Migrar barcodes
            logger.info("Migrando barcodes a la tabla barcodes...")
            connection.execute(
                text("""
                    INSERT INTO barcodes (codigo_barra, product_id)
                    SELECT codigo_barra, id FROM products
                    WHERE codigo_barra IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM barcodes WHERE barcodes.codigo_barra = products.codigo_barra
                    )
                """)
            )
            connection.commit()
            logger.info("✓ Barcodes migrados exitosamente")
            
    except Exception as e:
        logger.error(f"✗ Error durante la migración: {str(e)}")
        raise

def verify_migration():
    """Verifica que la migración se completó correctamente"""
    try:
        logger.info("=== Verificando migración ===")
        
        with engine.connect() as connection:
            # Contar barcodes migrados
            result = connection.execute(
                text("SELECT COUNT(*) as count FROM barcodes")
            )
            barcode_count = result.fetchone()[0]
            
            # Contar productos con barcodes originales
            result = connection.execute(
                text("SELECT COUNT(*) as count FROM products WHERE codigo_barra IS NOT NULL")
            )
            product_count = result.fetchone()[0]
            
            logger.info(f"Barcodes en tabla barcodes: {barcode_count}")
            logger.info(f"Productos con codigo_barra original: {product_count}")
            
            if barcode_count == product_count:
                logger.info("✓ Migración verificada: todos los barcodes se migraron correctamente")
                return True
            else:
                logger.warning(f"⚠ Advertencia: hay discrepancia en los conteos")
                return False
                
    except Exception as e:
        logger.error(f"✗ Error al verificar migración: {str(e)}")
        return False

def remove_old_barcode_column():
    """
    Elimina la columna codigo_barra de la tabla products después de verificar la migración.
    NOTA: Solo ejecutar después de verificar que la migración fue exitosa.
    """
    try:
        logger.info("=== Eliminando columna antigua codigo_barra ===")
        
        with engine.connect() as connection:
            # Verificar si la columna existe
            try:
                connection.execute(
                    text("ALTER TABLE products DROP COLUMN codigo_barra")
                )
                connection.commit()
                logger.info("✓ Columna codigo_barra eliminada exitosamente")
            except Exception as e:
                if "Unknown column" in str(e) or "no such column" in str(e):
                    logger.info("✓ La columna codigo_barra ya no existe")
                else:
                    raise
                    
    except Exception as e:
        logger.error(f"✗ Error al eliminar columna: {str(e)}")
        raise

def main():
    """Ejecuta la migración completa"""
    try:
        logger.info("╔════════════════════════════════════════════╗")
        logger.info("║ Migración de Barcodes - esquelAhorra API  ║")
        logger.info("╚════════════════════════════════════════════╝")
        
        # 1. Crear tablas
        create_tables()
        
        # 2. Migrar barcodes
        migrate_barcodes()
        
        # 3. Verificar migración
        if verify_migration():
            # 4. Eliminar columna antigua (solo si verificación pasó)
            response = input("\n¿Deseas eliminar la columna codigo_barra de products? (s/n): ")
            if response.lower() == 's':
                remove_old_barcode_column()
            else:
                logger.info("⚠ Columna codigo_barra no eliminada. Puedes hacerlo manualmente después.")
        
        logger.info("\n✓ Migración completada")
        
    except Exception as e:
        logger.error(f"\n✗ Migración fallida: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
