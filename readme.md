## Esquel Ahorra API
# 2. Crear y activar entorno virtual
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

.venv\Scripts\Activate.ps1 #script para activar el entorno virtual usando Microsoft Powershell
# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env