#!/bin/bash

# ============================================================================
# Agent Foundry Development Setup Script
# One-command setup for local development
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${NC}ℹ${NC} $1"
}

# ============================================================================
# Prerequisites Check
# ============================================================================

echo ""
echo "======================================================================"
echo "  Agent Foundry - Development Setup"
echo "======================================================================"
echo ""

print_info "Checking prerequisites..."

# Check Docker
if command -v docker &> /dev/null; then
    print_success "Docker is installed ($(docker --version | cut -d' ' -f3))"
else
    print_error "Docker is not installed"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    print_success "Docker Compose is installed"
else
    print_error "Docker Compose is not installed"
    echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check Python (optional for local development)
if command -v python3 &> /dev/null; then
    print_success "Python 3 is installed ($(python3 --version | cut -d' ' -f2))"
else
    print_warning "Python 3 is not installed (optional for local development)"
fi

# Check Node.js (optional for local development)
if command -v node &> /dev/null; then
    print_success "Node.js is installed ($(node --version))"
else
    print_warning "Node.js is not installed (optional for local development)"
fi

echo ""

# ============================================================================
# Environment Setup
# ============================================================================

print_info "Setting up environment..."

# Check for .env file
if [ ! -f "backend/.env" ]; then
    print_warning ".env file not found, creating from .env.example"
    
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        print_success "Created backend/.env from .env.example"
        print_warning "Please edit backend/.env and add your ANTHROPIC_API_KEY"
        echo ""
        echo "Required:"
        echo "  - ANTHROPIC_API_KEY=sk-ant-..."
        echo ""
        echo "Optional:"
        echo "  - FASTINO_API_KEY"
        echo "  - FREEPIK_API_KEY"
        echo "  - FRONTEGG_API_KEY"
        echo "  - AIRIA_API_KEY"
        echo "  - RAINDROP_API_KEY"
        echo ""
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_success ".env file exists"
fi

# Check if ANTHROPIC_API_KEY is set
if grep -q "ANTHROPIC_API_KEY=sk-ant-" backend/.env; then
    print_success "ANTHROPIC_API_KEY appears to be configured"
elif grep -q "ANTHROPIC_API_KEY=$" backend/.env || grep -q "ANTHROPIC_API_KEY=\.\.\." backend/.env; then
    print_error "ANTHROPIC_API_KEY is not configured in backend/.env"
    echo "Please add your Anthropic API key to backend/.env"
    echo "Get your key from: https://console.anthropic.com/"
    exit 1
else
    print_warning "Could not verify ANTHROPIC_API_KEY configuration"
fi

echo ""

# ============================================================================
# Docker Setup
# ============================================================================

print_info "Starting Docker services..."

# Build and start services
if docker-compose up -d --build; then
    print_success "Docker services started"
else
    print_error "Failed to start Docker services"
    exit 1
fi

echo ""

# ============================================================================
# Health Checks
# ============================================================================

print_info "Waiting for services to be healthy..."

# Wait for postgres
echo -n "Waiting for PostgreSQL..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U agent -d agentfoundry &> /dev/null; then
        echo ""
        print_success "PostgreSQL is healthy"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo ""
    print_error "PostgreSQL failed to start"
    docker-compose logs postgres
    exit 1
fi

# Wait for redis
echo -n "Waiting for Redis..."
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        echo ""
        print_success "Redis is healthy"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo ""
    print_error "Redis failed to start"
    docker-compose logs redis
    exit 1
fi

# Wait for backend
echo -n "Waiting for Backend API..."
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -sf http://localhost:8000/health &> /dev/null; then
        echo ""
        print_success "Backend API is healthy"
        break
    fi
    echo -n "."
    sleep 3
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo ""
    print_warning "Backend API may not be ready yet"
    print_info "Check logs with: docker-compose logs backend"
fi

# Wait for frontend
echo -n "Waiting for Frontend..."
attempt=0
while [ $attempt -lt 20 ]; do
    if curl -sf http://localhost:3000 &> /dev/null; then
        echo ""
        print_success "Frontend is healthy"
        break
    fi
    echo -n "."
    sleep 3
    attempt=$((attempt + 1))
done

if [ $attempt -eq 20 ]; then
    echo ""
    print_warning "Frontend may not be ready yet"
    print_info "Check logs with: docker-compose logs frontend"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "======================================================================"
echo "  Setup Complete! 🎉"
echo "======================================================================"
echo ""
echo "Services:"
echo "  • Backend API:  http://localhost:8000"
echo "  • API Docs:     http://localhost:8000/docs"
echo "  • Frontend:     http://localhost:3000"
echo "  • PostgreSQL:   localhost:5432"
echo "  • Redis:        localhost:6379"
echo ""
echo "Useful commands:"
echo "  • View logs:           docker-compose logs -f [service]"
echo "  • Stop services:       docker-compose down"
echo "  • Restart service:     docker-compose restart [service]"
echo "  • Run tests:           docker-compose exec backend pytest"
echo "  • Access database:     docker-compose exec postgres psql -U agent -d agentfoundry"
echo "  • Access Redis CLI:    docker-compose exec redis redis-cli"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Check API documentation at http://localhost:8000/docs"
echo "  3. Run the demo: docker-compose exec backend python demos/blog_generator.py"
echo ""

print_success "Happy coding! 🚀"
echo ""
