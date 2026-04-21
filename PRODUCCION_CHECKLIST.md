# Checklist para Producción - Esquelahorra API

## 🔴 Error Crítico Corregido: GET /locals/ → 500

### Problema
El endpoint `GET /locals/` retornaba error 500 por validación de Pydantic:
```
3 validation errors for response
  {'type': 'bool_type', 'loc': ('response', 0, 'is_active'), 
   'msg': 'Input should be a valid boolean', 'input': None}
```
- Registros en BD tenían `is_active = NULL`
- Schema esperaba `is_active: bool` (no nullable)

### Solución Aplicada
✅ Schema tolerante a NULL en [app/schemas/local.py](app/schemas/local.py)
✅ Modelo BD con `nullable=False` en [app/models/local.py](app/models/local.py)
✅ Script de migración en [migrations.py](migrations.py)
✅ Script SQL en [fix_is_active.sql](fix_is_active.sql)

### ⚡ EJECUTAR MIGRACIÓN AHORA en Producción

**Opción 1: Script Python (recomendado)**
```bash
cd /ruta/al/proyecto
source .venv/bin/activate
python migrations.py
```

**Opción 2: Script SQL directo**
```bash
mysql -u api -p Esquelahorra < fix_is_active.sql
```

**Ver instrucciones detalladas:** [MIGRACION_IS_ACTIVE.md](MIGRACION_IS_ACTIVE.md)

---

## Cambios Realizados

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

### 4. **Schemas Mejorados**
   - ✅ `app/schemas/local.py` - `is_active` con valor por defecto y validador

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

1. **Ejecutar migración de datos:**
   ```bash
   python migrations.py
   ```

2. **Verifica la BD:**
   ```bash
   mysql -h localhost -u api -p
   USE Esquelahorra;
   SELECT COUNT(*) as null_count FROM locals WHERE is_active IS NULL;
   # Debería devolver: 0
   ```

3. **Reinicia la API:**
   ```bash
   systemctl restart esquel-ahorra-api
   # o donde sea que lo ejecutes
   ```

4. **Revisa los logs:**
   ```bash
   tail -f /var/log/esquel-api/app.log
   ```

5. **Prueba health-check:**
   ```bash
   curl https://tu-dominio.com/health-check
   # Debería devolver:
   # {"status": "ok", "database": "connected"}
   ```

6. **Prueba GET /locals:**
   ```bash
   curl -H "Authorization: Bearer <token>" \
     https://tu-dominio.com/locals/
   # Debería retornar JSON con locales, SIN error 500
   ```

## Si Continúa el Error 500

Revisa los logs del servidor. Ahora deberían mostrar el error específico:

```bash
# Posibles errores que verás:
# 1. Error de conexión a MySQL
#    "Error al conectar a la base de datos: Can't connect to MySQL server"
#    → Solución: Verifica DB_HOST, DB_USER, DB_PASSWORD, firewall

# 2. is_active = NULL (ya debe estar resuelto tras migración)
#    "3 validation errors: ... 'is_active', 'msg': 'Input should be a valid boolean'"
#    → Solución: Ejecutar migrations.py

# 3. Variables de entorno faltantes
#    "Variables de entorno faltantes: ['SECRET_KEY', 'REFRESH_SECRET_KEY']"
#    → Solución: Configura esas variables en tu .env o en el servidor
```

## Recomendaciones Adicionales

1. **Monitoreo**: Configura alertas en los logs para errores 500
2. **Backups**: Realiza backups regulares de la BD
3. **Seguridad**: Cambia SECRET_KEY en producción (generador seguro)
4. **Performance**: Considera agregar cache para queries frecuentes
5. **Rate Limiting**: Considera agregar limitación de rate para protegerse de ataques

## Archivos Importantes

- 📄 [migrations.py](migrations.py) - Script Python para migración
- 📄 [fix_is_active.sql](fix_is_active.sql) - Script SQL para migración
- 📄 [MIGRACION_IS_ACTIVE.md](MIGRACION_IS_ACTIVE.md) - Instrucciones detalladas
- 📄 [main.py](main.py) - Aplicación principal con logging
- 📄 [app/database.py](app/database.py) - Configuración de BD mejorada

## Status

Los cambios han sido aplicados y el código está listo para producción.
**ACCIÓN REQUERIDA:** Ejecutar `python migrations.py` en producción para resolver el error 500.
