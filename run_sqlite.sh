#!/bin/bash

# Script para ejecutar el servidor Django con SQLite (desarrollo local)
# Soluciona el problema de cuota excedida en Neon

echo "🚀 Iniciando servidor Django con SQLite..."

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Exportar variables de entorno necesarias
export SECRET_KEY="kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu"
export DEBUG="True"
export USE_SQLITE_LOCAL="true"

# Ejecutar migraciones si es necesario
echo "📊 Ejecutando migraciones..."
python manage.py migrate

# Iniciar servidor
echo "🌐 Iniciando servidor en http://localhost:8000"
echo "💡 Usando SQLite local (db.sqlite3)"
echo "🛑 Presiona Ctrl+C para detener"
echo ""

python manage.py runserver
