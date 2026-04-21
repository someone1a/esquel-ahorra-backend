# Migración de Barcodes - Separación de Tabla

## Resumen de Cambios

Se ha refactorizado la estructura de barcodes para separar los códigos de barra en una tabla independiente (`barcodes`), permitiendo que un producto tenga múltiples barcodes.

### Cambios Realizados

#### 1. **Modelo de Base de Datos** (`app/models/product.py`)
   - ✅ Nuevo modelo `Barcode` con campos:
     - `id`: Clave primaria
     - `codigo_barra`: Código de barra (único, indexado)
     - `product_id`: Referencia a producto
   - ✅ Modelo `Product` modificado:
     - Removido: `codigo_barra` (ahora está en Barcode)
     - Agregado: relación `barcodes` (one-to-many)

#### 2. **Endpoints** (`app/routers/products.py`)
   - ✅ Nuevo endpoint: `GET /products/barcode/{barcode}`
     - Busca un producto por su código de barra
     - Retorna 404 si no encuentra el producto
     - Ejemplo: `GET /products/barcode/7506306213081`

#### 3. **Servicios** (`app/services/products.py`)
   - ✅ `create_product()`: Ahora crea tanto el producto como el barcode
   - ✅ `get_product_by_barcode()`: Busca en la tabla `barcodes` en lugar de `products`

#### 4. **Esquemas** (`app/schemas/product.py`)
   - ✅ Nuevo schema: `Barcode`
   - ✅ Schema `Product` actualizado: incluye relación a barcodes

## Instrucciones de Migración

### Paso 1: Activar Entorno Virtual

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

### Paso 2: Ejecutar Script de Migración

```bash
python migrate_barcodes.py
```

**Salida esperada:**
```
╔════════════════════════════════════════════╗
║ Migración de Barcodes - esquelAhorra API  ║
╚════════════════════════════════════════════╝
2026-04-21 12:00:00 - root - INFO - === Creando nuevas tablas ===
2026-04-21 12:00:00 - root - INFO - ✓ Tablas creadas exitosamente
2026-04-21 12:00:00 - root - INFO - === Iniciando migración de barcodes ===
2026-04-21 12:00:00 - root - INFO - Encontrados X registros con barcodes para migrar
2026-04-21 12:00:00 - root - INFO - Migrando barcodes a la tabla barcodes...
2026-04-21 12:00:00 - root - INFO - ✓ Barcodes migrados exitosamente
2026-04-21 12:00:00 - root - INFO - === Verificando migración ===
2026-04-21 12:00:00 - root - INFO - Barcodes en tabla barcodes: X
2026-04-21 12:00:00 - root - INFO - ✓ Migración verificada
¿Deseas eliminar la columna codigo_barra de products? (s/n):
```

El script te preguntará si deseas eliminar la columna antigua. Se recomienda responder **"s"** (sí) después de verificar que todo funciona correctamente.

### Paso 3: Reiniciar la Aplicación

Después de la migración, reinicia tu servidor FastAPI:

```bash
python main.py
```

## Prueba de Funcionamiento

### Crear Producto

```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "nombre": "Producto Test",
    "codigo_barra": "7506306213081",
    "precio": 100.0,
    "local_id": 1
  }'
```

### Buscar por Barcode

```bash
curl -X GET http://localhost:8000/products/barcode/7506306213081 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Respuesta esperada (200 OK):**
```json
{
  "id": 1,
  "nombre": "Producto Test",
  "barcodes": [
    {
      "id": 1,
      "codigo_barra": "7506306213081",
      "product_id": 1
    }
  ],
  "prices": [
    {
      "id": 1,
      "product_id": 1,
      "local_id": 1,
      "precio": 100.0
    }
  ]
}
```

## Compatibilidad

- ✅ El endpoint `/products/search?barcode=...` sigue funcionando
- ✅ El endpoint `GET /products/{product_id}` sigue funcionando
- ✅ Los endpoints de precios siguen funcionando sin cambios
- ✅ Las correcciones de precio siguen funcionando sin cambios

## Rollback (Si es necesario)

Si necesitas revertir los cambios:

1. Detén el servidor
2. Restaura el backup de la base de datos
3. Revierte los cambios en código:
   ```bash
   git checkout app/models/product.py
   git checkout app/routers/products.py
   git checkout app/services/products.py
   git checkout app/schemas/product.py
   ```
4. Reinicia el servidor

## Preguntas Frecuentes

### ¿Qué pasa si un barcode ya existe?
El script de migración verifica duplicados y no los importa dos veces.

### ¿Puedo tener múltiples barcodes para un producto?
Sí. Ahora la tabla es independiente, así que puedes agregar múltiples barcodes a un producto. Tendrías que agregar un endpoint adicional para esto si lo necesitas.

### ¿La columna codigo_barra sigue en products?
Después de la migración y si respondes "s" a la pregunta del script, la columna se elimina automáticamente. Si respondes "n", puedes eliminarla manualmente después con:
```sql
ALTER TABLE products DROP COLUMN codigo_barra;
```

---

**Fecha de implementación:** 2026-04-21
**Versión:** 2.0.1
