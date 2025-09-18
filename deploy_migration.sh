#!/bin/bash

# Script para ejecutar la migración en producción (Heroku)
# Este script ejecuta la migración 0018_strategy_status.py

echo "🚀 Ejecutando migración en producción..."

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encontró manage.py. Ejecuta este script desde el directorio del proyecto."
    exit 1
fi

# Verificar que la migración existe
if [ ! -f "strategies/migrations/0018_strategy_status.py" ]; then
    echo "❌ Error: No se encontró la migración 0018_strategy_status.py"
    exit 1
fi

echo "📋 Verificando estado de migraciones..."
python manage.py showmigrations strategies

echo ""
echo "🔄 Ejecutando migración específica..."
python manage.py migrate strategies 0018

echo ""
echo "✅ Verificando que la migración se aplicó correctamente..."
python manage.py showmigrations strategies

echo ""
echo "🎉 Migración completada exitosamente!"
echo ""
echo "📋 Resumen:"
echo "   - Se agregó el campo 'status' a la tabla 'strategies'"
echo "   - Valores posibles: DRAFT, READY, ACTIVE, INACTIVE"
echo "   - Valor por defecto: DRAFT"
echo ""
echo "🚀 El backend está listo para usar el nuevo flujo de creación de estrategias!"
