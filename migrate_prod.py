import os
import pymysql
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def migrate():
    # Obtener credenciales de producción del .env
    # Asegúrate de que USE_SQLITE esté en False o ignorarlo aquí
    db_host = os.getenv("DB_HOST")
    db_port = int(os.getenv("DB_PORT", 3306))
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")

    if not all([db_host, db_user, db_pass, db_name]):
        logger.error("Faltan variables de entorno para conectar a MySQL")
        return

    logger.info(f"Conectando a la base de datos {db_name} en {db_host}...")

    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_pass,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection.cursor() as cursor:
            # 1. Crear tabla 'locals' si no existe
            logger.info("Verificando tabla 'locals'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `locals` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `nombre` VARCHAR(255) NOT NULL,
                    `direccion` VARCHAR(255) NOT NULL,
                    `telefono` VARCHAR(50),
                    `is_active` BOOLEAN DEFAULT TRUE
                )
            """)

            # 2. Actualizar tabla 'users'
            logger.info("Actualizando tabla 'users'...")
            columns_to_add_users = [
                ("points", "INT DEFAULT 0"),
                ("referral_code", "VARCHAR(50) UNIQUE"),
                ("referred_by_id", "INT, ADD FOREIGN KEY (referred_by_id) REFERENCES users(id)")
            ]
            
            for col_name, col_def in columns_to_add_users:
                cursor.execute(f"SHOW COLUMNS FROM `users` LIKE '{col_name}'")
                if not cursor.fetchone():
                    logger.info(f"Añadiendo columna '{col_name}' a 'users'...")
                    try:
                        cursor.execute(f"ALTER TABLE `users` ADD COLUMN {col_name} {col_def}")
                    except Exception as e:
                        logger.error(f"Error al añadir {col_name}: {e}")

            # 3. Actualizar tabla 'price_corrections'
            logger.info("Actualizando tabla 'price_corrections'...")
            columns_to_add_corrections = [
                ("user_id", "INT NOT NULL, ADD FOREIGN KEY (user_id) REFERENCES users(id)"),
                ("status", "VARCHAR(20) DEFAULT 'pending'")
            ]

            for col_name, col_def in columns_to_add_corrections:
                cursor.execute(f"SHOW COLUMNS FROM `price_corrections` LIKE '{col_name}'")
                if not cursor.fetchone():
                    logger.info(f"Añadiendo columna '{col_name}' a 'price_corrections'...")
                    try:
                        # Para user_id, si hay datos previos, esto podría fallar si no hay un usuario por defecto
                        # Vamos a permitir NULL temporalmente o asignar al primer usuario si existe
                        if col_name == "user_id":
                            cursor.execute("ALTER TABLE `price_corrections` ADD COLUMN user_id INT NULL")
                            cursor.execute("ALTER TABLE `price_corrections` ADD FOREIGN KEY (user_id) REFERENCES users(id)")
                            logger.warning("Columna 'user_id' añadida como NULLABLE para evitar errores con datos existentes")
                        else:
                            cursor.execute(f"ALTER TABLE `price_corrections` ADD COLUMN {col_name} {col_def}")
                    except Exception as e:
                        logger.error(f"Error al añadir {col_name}: {e}")

        connection.commit()
        logger.info("✓ Migración completada exitosamente")

    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    migrate()
