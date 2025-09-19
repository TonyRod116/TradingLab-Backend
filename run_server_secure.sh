#!/bin/bash

# Script seguro para ejecutar el servidor
# NO contiene credenciales hardcodeadas

echo "🚀 Iniciando servidor de forma segura..."

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo "❌ Error: Archivo .env no encontrado"
    echo "📋 Crea el archivo .env basándote en env_template.txt"
    echo "   cp env_template.txt .env"
    echo "   # Luego edita .env con tus credenciales reales"
    exit 1
fi

# Cargar variables de entorno desde .env
echo "📁 Cargando configuración desde .env..."
export $(grep -v '^#' .env | xargs)

# Verificar que las variables críticas están definidas
if [ -z "$PGPASSWORD" ] || [ -z "$SECRET_KEY" ]; then
    echo "❌ Error: Variables críticas no definidas en .env"
    echo "   Asegúrate de que PGPASSWORD y SECRET_KEY estén definidas"
    exit 1
fi

echo "✅ Configuración cargada correctamente"
echo "📊 Base de datos: $PGHOST/$PGDATABASE"
echo "👤 Usuario: $PGUSER"

# Activar entorno virtual
source venv/bin/activate

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py migrate

# Ejecutar servidor
echo "🌐 Iniciando servidor..."
python manage.py runserver 0.0.0.0:8000
