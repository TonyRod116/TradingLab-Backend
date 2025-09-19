#!/bin/bash

# Script para ejecutar el servidor Django con PostgreSQL local
echo "🐘 Iniciando servidor Django con PostgreSQL local..."

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Exportar variables de entorno para PostgreSQL local
export PGHOST=localhost
export PGDATABASE=tradinglab_local
export PGUSER=tonirod
export PGPASSWORD=""
export SECRET_KEY="kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu"
export DEBUG="True"

# Ejecutar migraciones
echo "📊 Ejecutando migraciones..."
python manage.py migrate

# Iniciar servidor
echo "🌐 Iniciando servidor en http://localhost:8000"
echo "💡 Usando PostgreSQL local (tradinglab_local)"
echo "🛑 Presiona Ctrl+C para detener"
echo ""

python manage.py runserver






