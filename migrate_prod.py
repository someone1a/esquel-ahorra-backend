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
            # 1. Crear tabla 'users' si no existe
            logger.info("Verificando tabla 'users'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `users` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `email` VARCHAR(255) UNIQUE NOT NULL,
                    `name` VARCHAR(255) NOT NULL,
                    `lastname` VARCHAR(255) NOT NULL,
                    `hashed_password` VARCHAR(255) NOT NULL,
                    `rol` VARCHAR(50) NOT NULL,
                    `points` INT DEFAULT 0,
                    `referral_code` VARCHAR(50) UNIQUE DEFAULT '',
                    `referred_by_id` INT,
                    FOREIGN KEY (`referred_by_id`) REFERENCES `users`(`id`)
                )
            """)

            # 2. Crear tabla 'locals' si no existe
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

            # 3. Crear tabla 'products' si no existe
            logger.info("Verificando tabla 'products'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `products` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `nombre` VARCHAR(255) NOT NULL,
                    `marca` VARCHAR(255),
                    `presentacion` VARCHAR(255),
                    `categoria` VARCHAR(255),
                    `imagen_url` VARCHAR(500)
                )
            """)

            # 4. Crear tabla 'barcodes' si no existe
            logger.info("Verificando tabla 'barcodes'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `barcodes` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `codigo_barra` VARCHAR(255) UNIQUE NOT NULL,
                    `product_id` INT NOT NULL,
                    FOREIGN KEY (`product_id`) REFERENCES `products`(`id`) ON DELETE CASCADE,
                    INDEX `idx_codigo_barra` (`codigo_barra`)
                )
            """)

            # 5. Crear tabla 'prices' si no existe
            logger.info("Verificando tabla 'prices'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `prices` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `product_id` INT NOT NULL,
                    `local_id` INT NOT NULL,
                    `precio` FLOAT NOT NULL,
                    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    `created_by` INT,
                    `updated_by` INT,
                    `verificado` VARCHAR(10) DEFAULT 'no',
                    `verificado_por` INT,
                    `verificado_en` DATETIME,
                    FOREIGN KEY (`product_id`) REFERENCES `products`(`id`),
                    FOREIGN KEY (`local_id`) REFERENCES `locals`(`id`),
                    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`),
                    FOREIGN KEY (`updated_by`) REFERENCES `users`(`id`),
                    FOREIGN KEY (`verificado_por`) REFERENCES `users`(`id`),
                    INDEX `idx_price_product_local` (`product_id`, `local_id`),
                    INDEX `idx_price_created_by` (`created_by`),
                    INDEX `idx_price_updated_by` (`updated_by`),
                    INDEX `idx_price_product_local_verified` (`product_id`, `local_id`, `verificado`)
                )
            """)

            # 6. Crear tabla 'price_corrections' si no existe
            logger.info("Verificando tabla 'price_corrections'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `price_corrections` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `product_id` INT NOT NULL,
                    `old_price` FLOAT NOT NULL,
                    `new_price` FLOAT NOT NULL,
                    `local_id` INT NOT NULL,
                    `user_id` INT NOT NULL,
                    `status` VARCHAR(20) DEFAULT 'pending',
                    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (`product_id`) REFERENCES `products`(`id`),
                    FOREIGN KEY (`local_id`) REFERENCES `locals`(`id`),
                    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
                    INDEX `idx_price_correction_status` (`status`),
                    INDEX `idx_price_correction_user` (`user_id`)
                )
            """)

            # 7. Crear tabla 'price_history' si no existe
            logger.info("Verificando tabla 'price_history'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `price_history` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `price_id` INT NOT NULL,
                    `old_price` FLOAT NOT NULL,
                    `new_price` FLOAT NOT NULL,
                    `changed_by` INT NOT NULL,
                    `changed_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (`price_id`) REFERENCES `prices`(`id`),
                    FOREIGN KEY (`changed_by`) REFERENCES `users`(`id`)
                )
            """)

            # 8. Crear tabla 'token_blacklist' si no existe
            logger.info("Verificando tabla 'token_blacklist'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `token_blacklist` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `jti` VARCHAR(255) UNIQUE NOT NULL,
                    `expires_at` DATETIME NOT NULL,
                    INDEX `idx_jti` (`jti`),
                    INDEX `idx_expires_at` (`expires_at`)
                )
            """)

            # Migraciones adicionales para tablas existentes
            logger.info("Aplicando migraciones adicionales...")

            # Agregar columnas faltantes a 'products' si no existen
            columns_to_add_products = [
                ("marca", "VARCHAR(255)"),
                ("presentacion", "VARCHAR(255)"),
                ("categoria", "VARCHAR(255)"),
                ("imagen_url", "VARCHAR(500)")
            ]
            
            for col_name, col_def in columns_to_add_products:
                cursor.execute(f"SHOW COLUMNS FROM `products` LIKE '{col_name}'")
                if not cursor.fetchone():
                    logger.info(f"Añadiendo columna '{col_name}' a 'products'...")
                    cursor.execute(f"ALTER TABLE `products` ADD COLUMN `{col_name}` {col_def}")

            # Agregar columnas faltantes a 'prices' si no existen
            columns_to_add_prices = [
                ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
                ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                ("created_by", "INT, ADD FOREIGN KEY (`created_by`) REFERENCES `users`(`id`)"),
                ("updated_by", "INT, ADD FOREIGN KEY (`updated_by`) REFERENCES `users`(`id`)"),
                ("verificado", "VARCHAR(10) DEFAULT 'no'"),
                ("verificado_por", "INT, ADD FOREIGN KEY (`verificado_por`) REFERENCES `users`(`id`)"),
                ("verificado_en", "DATETIME")
            ]
            
            for col_name, col_def in columns_to_add_prices:
                cursor.execute(f"SHOW COLUMNS FROM `prices` LIKE '{col_name}'")
                if not cursor.fetchone():
                    logger.info(f"Añadiendo columna '{col_name}' a 'prices'...")
                    try:
                        cursor.execute(f"ALTER TABLE `prices` ADD COLUMN `{col_name}` {col_def}")
                    except Exception as e:
                        logger.error(f"Error al añadir {col_name}: {e}")

            # Agregar índices faltantes
            logger.info("Verificando índices...")
            try:
                cursor.execute("SHOW INDEX FROM `prices` WHERE Key_name='idx_price_product_local'")
                if not cursor.fetchone():
                    cursor.execute("CREATE INDEX `idx_price_product_local` ON `prices` (`product_id`, `local_id`)")

                cursor.execute("SHOW INDEX FROM `prices` WHERE Key_name='idx_price_created_by'")
                if not cursor.fetchone():
                    cursor.execute("CREATE INDEX `idx_price_created_by` ON `prices` (`created_by`)")

                cursor.execute("SHOW INDEX FROM `prices` WHERE Key_name='idx_price_updated_by'")
                if not cursor.fetchone():
                    cursor.execute("CREATE INDEX `idx_price_updated_by` ON `prices` (`updated_by`)")

                cursor.execute("SHOW INDEX FROM `prices` WHERE Key_name='idx_price_product_local_verified'")
                if not cursor.fetchone():
                    cursor.execute("CREATE INDEX `idx_price_product_local_verified` ON `prices` (`product_id`, `local_id`, `verificado`)")

                cursor.execute("SHOW INDEX FROM `price_corrections` WHERE Key_name='idx_price_correction_status'")
                if not cursor.fetchone():
                    cursor.execute("CREATE INDEX `idx_price_correction_status` ON `price_corrections` (`status`)")

                cursor.execute("SHOW INDEX FROM `price_corrections` WHERE Key_name='idx_price_correction_user'")
                if not cursor.fetchone():
                    cursor.execute("CREATE INDEX `idx_price_correction_user` ON `price_corrections` (`user_id`)")
            except Exception as e:
                logger.error(f"Error al crear índices: {e}")

        connection.commit()
        logger.info("✓ Migración completada exitosamente")

    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    migrate()
