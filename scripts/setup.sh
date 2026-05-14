#!/usr/bin/env bash
set -euo pipefail

echo "================================================"
echo "  AI QA Agent Platform — Project Setup"
echo "================================================"

PLATFORM=$(uname -s)
PYTHON=${PYTHON:-python3}

check_dependencies() {
    echo "[1/5] Checking dependencies..."
    command -v $PYTHON >/dev/null 2>&1 || { echo "Error: Python 3.12+ is required"; exit 1; }
    command -v node >/dev/null 2>&1 || { echo "Error: Node.js 20+ is required"; exit 1; }
    command -v npm >/dev/null 2>&1 || { echo "Error: npm is required"; exit 1; }
    command -v docker >/dev/null 2>&1 || echo "Warning: Docker not found (optional)"
    echo "  Python: $($PYTHON --version)"
    echo "  Node:   $(node --version)"
    echo "  Npm:    $(npm --version)"
}

setup_python_venv() {
    echo "[2/5] Setting up Python virtual environment..."
    if [ ! -d ".venv" ]; then
        $PYTHON -m venv .venv
        echo "  Virtual environment created at .venv"
    else
        echo "  Virtual environment already exists"
    fi
    source .venv/bin/activate
    pip install --upgrade pip setuptools wheel
}

install_python_deps() {
    echo "[3/5] Installing Python dependencies..."
    pip install -r backend/requirements.txt
    pip install -r ai-orchestrator/requirements.txt
    pip install -r agents/requirements.txt
    pip install -r test_generation/requirements.txt
    pip install -r api-tests/requirements.txt
    pip install -r prompt-manager/requirements.txt
    pip install -r logging/requirements.txt
}

install_node_deps() {
    echo "[4/5] Installing Node.js dependencies..."
    cd frontend && npm install && cd ..
    cd playwright-tests && npm install && cd ..
}

setup_env() {
    echo "[5/5] Setting up environment files..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo "  Created .env from .env.example"
    else
        echo "  .env already exists"
    fi
    if [ ! -f "config/local.yaml" ]; then
        cp config/base.yaml config/local.yaml
        echo "  Created config/local.yaml from config/base.yaml"
    else
        echo "  config/local.yaml already exists"
    fi
}

check_dependencies
setup_python_venv
install_python_deps
install_node_deps
setup_env

echo ""
echo "================================================"
echo "  Setup complete!"
echo ""
echo "  Quick Start:"
echo "    source .venv/bin/activate"
echo "    make docker-dev        # Start Postgres & Redis"
echo "    make docker-up         # Start all services"
echo "    make test              # Run all tests"
echo "================================================"
