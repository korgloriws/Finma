#!/bin/bash
echo "🚀 Iniciando aplicação Finma..."
echo "📦 Instalando dependências..."
pip install -r requirements.txt

echo "🔧 Configurando ambiente..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "🌐 Iniciando servidor..."
python app.py 