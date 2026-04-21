# INSTRUCCIONES DE MIGRACIÓN - Error is_active = NULL

## Problema
El endpoint `GET /locals/` retorna error 500 porque hay registros en la BD con `is_active = NULL`, pero Pydantic espera un `boolean`.

## Solución

### Opción 1: Ejecutar Script Python (Recomendado)

1. **SSH a tu servidor de producción:**
```bash
ssh tu_usuario@tu_servidor
cd /ruta/al/proyecto
```

2. **Activar entorno virtual:**
```bash
source .venv/bin/activate  # Linux/macOS
# o
.venv\Scripts\activate     # Windows
```

3. **Ejecutar migración:**
```bash
python migrations.py
```

**Esperado:**
```
2026-04-21 02:15:30,123 - INFO - === Iniciando Migración ===
2026-04-21 02:15:30,234 - INFO - Verificando estructura de tabla 'locals'...
2026-04-21 02:15:30,345 - INFO - Encontrados 3 registros con is_active = NULL
2026-04-21 02:15:30,456 - INFO - Actualizando registros...
2026-04-21 02:15:30,567 - INFO - ✓ 3 registros actualizados a is_active = TRUE
2026-04-21 02:15:30,678 - INFO - ✓ Migración completada exitosamente
```

---

### Opción 2: Ejecutar Script SQL Directo

Si prefieres hacerlo directamente en MySQL:

```bash
# En tu servidor, ejecuta:
mysql -u api -p Esquelahorra < fix_is_active.sql
# Te pedirá la contraseña
```

**O manualmente en MySQL CLI:**
```bash
mysql -u api -p Esquelahorra
```

Luego ejecuta:
```sql
-- Ver cantidad de NULLs
SELECT COUNT(*) as registros_null FROM locals WHERE is_active IS NULL;

-- Actualizar
UPDATE locals SET is_active = 1 WHERE is_active IS NULL;

-- Verificar
SELECT COUNT(*) as registros_null FROM locals WHERE is_active IS NULL;
```

Debería devolver `0` en la última consulta.

---

### Opción 3: Actualizar Columna (Permanentemente)

Para asegurar que esto no vuelva a ocurrir:

```bash
mysql -u api -p Esquelahorra
```

```sql
ALTER TABLE locals MODIFY COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
```

---

## Cambios en el Código (ya aplicados)

✅ [app/schemas/local.py](app/schemas/local.py):
- `is_active` ahora es `Optional[bool]` con valor por defecto `True`
- Validator automático convierte `None` → `True`

✅ [app/models/local.py](app/models/local.py):
- `is_active` ahora tiene `nullable=False`
- Default value es `True`

✅ [migrations.py](migrations.py):
- Script Python para migrar datos

✅ [fix_is_active.sql](fix_is_active.sql):
- Script SQL directo

---

## Verificar que la Solución Funciona

Después de ejecutar la migración, prueba:

```bash
curl -H "Authorization: Bearer <tu_token>" \
  https://api.esquel-ahorra.online/locals/
```

Debería devolver:
```json
[
  {
    "id": 1,
    "nombre": "Local 1",
    "direccion": "Calle 1",
    "telefono": null,
    "is_active": true
  },
  ...
]
```

---

## Si Algo Sale Mal

**Revertir cambios:**
```sql
-- Si necesitas revertir la ALTER TABLE
ALTER TABLE locals MODIFY COLUMN is_active BOOLEAN DEFAULT TRUE;
```

**Contactar soporte:**
Si el error persiste, revisa:
1. Los logs con: `tail -f /var/log/esquel-api/app.log`
2. Asegúrate que la conexión a MySQL es correcta
3. Verifica permisos de la cuenta de DB

---

## Timeline Aproximado
- ⏱ Opción 1 (Python): 1-2 minutos
- ⏱ Opción 2 (SQL): 30 segundos
- ⏱ Opción 3 (ALTER): 30 segundos

Sin downtime necesario en ninguna opción.
