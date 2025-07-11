#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Telegram Appointment Bot Development Environment${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}📝 Please edit .env file with your API keys before continuing${NC}"
    echo ""
    echo "Required API keys:"
    echo "  - TELEGRAM_BOT_TOKEN (get from @BotFather)"
    echo "  - OPENAI_API_KEY (get from OpenAI)"
    echo ""
    echo "After editing .env, run this script again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies
echo -e "${BLUE}📥 Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Start databases with Docker
echo -e "${BLUE}🗄️  Starting databases...${NC}"
docker-compose -f docker-compose.dev.yml up -d

# Wait for databases to be ready
echo -e "${BLUE}⏳ Waiting for databases to be ready...${NC}"
sleep 10

# Check database health
echo -e "${BLUE}🏥 Checking database health...${NC}"
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose -f docker-compose.dev.yml ps | grep -q "healthy"; then
        echo -e "${GREEN}✅ Databases are healthy${NC}"
        break
    else
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - waiting for databases...${NC}"
        sleep 5
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo -e "${YELLOW}⚠️  Databases may still be starting. Continuing anyway...${NC}"
fi

# Initialize databases
echo -e "${BLUE}🔧 Initializing databases...${NC}"
python3 -c "
import asyncio
import sys
sys.path.append('.')
from app.core.database import create_tables
asyncio.run(create_tables())
print('PostgreSQL tables initialized')
" 2>/dev/null && echo -e "${GREEN}✅ PostgreSQL initialized${NC}" || echo -e "${YELLOW}⚠️  PostgreSQL initialization failed${NC}"

python3 -c "
import asyncio
import sys
sys.path.append('.')
from app.core.graph_db import init_graph_database
asyncio.run(init_graph_database())
print('Neo4j schema initialized')
" 2>/dev/null && echo -e "${GREEN}✅ Neo4j initialized${NC}" || echo -e "${YELLOW}⚠️  Neo4j initialization failed${NC}"

echo ""
echo -e "${GREEN}🎉 Development environment is ready!${NC}"
echo ""
echo -e "${BLUE}🌐 Available services:${NC}"
echo "  - PostgreSQL: localhost:5432"
echo "  - Neo4j Browser: http://localhost:7474 (neo4j/password)"
echo "  - Redis: localhost:6379"
echo "  - ChromaDB: http://localhost:8001"
echo ""
echo -e "${BLUE}🚀 Starting the application...${NC}"
echo "  API will be available at: http://localhost:8000"
echo "  Documentation: http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
echo ""

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000