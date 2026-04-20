# Checklist para Producción - Esquelahorra API

## Cambios Realizados

He mejorado el manejo de errores en toda la aplicación para evitar errores 500 sin detalles:

### 1. **Logging Global** (`main.py`)
   - ✅ Agregado logging centralizado en todas las operaciones
   - ✅ Verificación de conexión a BD en startup
   - ✅ Endpoint `/health-check` mejorado que verifica la BD

### 2. **Manejo de Excepciones Robusto**
   - ✅ `app/routers/locals.py` - Try/catch con logging
   - ✅ `app/routers/products.py` - Try/catch en todos los endpoints
   - ✅ `app/routers/auth.py` - Try/catch mejorado
   - ✅ `app/services/products.py` - Manejo de IntegrityError y SQLAlchemyError

### 3. **Validación de Base de Datos** (`app/database.py`)
   - ✅ Validación de variables de entorno en startup
   - ✅ `pool_pre_ping=True` para MySQL (reconecta si la conexión se perdió)
   - ✅ Nueva función `verify_database_connection()`

## Verificación Antes de Desplegar

### Variables de Entorno Requeridas
```bash
# Verificar que tienes configurado en producción:
USE_SQLITE=False  # Asegúrate que es False para MySQL
DB_USER=<tu_usuario>
DB_PASSWORD=<tu_contraseña>
DB_HOST=<tu_host>
DB_PORT=3306
DB_NAME=<tu_base_datos>
SECRET_KEY=<clave_aleatoria_segura>
REFRESH_SECRET_KEY=<clave_aleatoria_segura>
PORT=8000
```

### Paso a Paso para Verificar

1. **Verifica la conexión a MySQL en producción:**
   ```bash
   # En tu servidor
   mysql -h DB_HOST -u DB_USER -p
   # Verifica que la base de datos existe:
   SHOW DATABASES;
   ```

2. **Revisa los logs después del deploy:**
   ```bash
   tail -f /var/log/esquel-api/app.log
   ```

3. **Prueba el endpoint de health-check:**
   ```bash
   curl https://tu-dominio.com/health-check
   # Debería devolver:
   # {"status": "ok", "database": "connected"}
   ```

4. **Para el error en POST /locals específicamente:**
   - ✅ Verificado: Ahora captura errores de BD
   - ✅ Verificado: Retorna mensajes claros si falla
   - ✅ Verificado: Logging detallado del error

## Si Continúa el Error 500

Revisa los logs del servidor. Ahora deberían mostrar el error específico:

```bash
# Posibles errores que verás:
# 1. Error de conexión a MySQL
#    "Error al conectar a la base de datos: Can't connect to MySQL server"
#    → Solución: Verifica DB_HOST, DB_USER, DB_PASSWORD, firewall

# 2. Tabla no existe
#    "Error en base de datos al crear local: Table 'BD' doesn't exist"
#    → Solución: Las tablas se crean automáticamente, pero verifica permisos de BD

# 3. Campo faltante en LocalCreate
#    "Error de integridad al crear local: Column 'X' cannot be null"
#    → Solución: Verifica que envíes los campos requeridos en el POST

# 4. Variables de entorno faltantes
#    "Variables de entorno faltantes: ['SECRET_KEY', 'REFRESH_SECRET_KEY']"
#    → Solución: Configura esas variables en tu .env o en el servidor
```

## Recomendaciones Adicionales

1. **Monitoreo**: Configura alertas en los logs para errores 500
2. **Backups**: Realiza backups regulares de la BD
3. **Seguridad**: Cambia SECRET_KEY en producción (generador seguro)
4. **Performance**: Considera agregar cache para queries frecuentes
5. **Rate Limiting**: Considera agregar limitación de rate para protegerse de ataques

## Probado Localmente

Los cambios han sido aplicados y el código está listo para producción. 
Si el error 500 continúa, los logs ahora te dirán exactamente qué está fallando.
