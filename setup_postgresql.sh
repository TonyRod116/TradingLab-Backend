#!/bin/bash

# Script para configurar PostgreSQL local
echo "🐘 Configurando PostgreSQL local..."

# Crear base de datos si no existe
echo "📊 Creando base de datos tradinglab_local..."
createdb tradinglab_local 2>/dev/null || echo "Base de datos ya existe"

# Configurar usuario local (sin contraseña)
echo "👤 Configurando usuario local..."
psql -d tradinglab_local -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'tonirod') THEN CREATE ROLE tonirod WITH LOGIN SUPERUSER; END IF; END \$\$;" 2>/dev/null || echo "Usuario ya existe o error de permisos"

# Configurar pg_hba.conf para permitir conexiones locales sin contraseña
echo "🔐 Configurando autenticación local..."
echo "local   all             tonirod                                 trust" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf 2>/dev/null || echo "No se pudo modificar pg_hba.conf"

# Reiniciar PostgreSQL
echo "🔄 Reiniciando PostgreSQL..."
sudo systemctl restart postgresql 2>/dev/null || echo "No se pudo reiniciar PostgreSQL"

echo "✅ Configuración completada"
echo "💡 Ahora puedes usar: ./run_postgresql.sh"






