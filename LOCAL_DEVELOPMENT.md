# Local Development Setup Guide

## Overview
This guide will help you set up the Telegram Appointment Bot for local development on your machine.

## Prerequisites

### Required Software
- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 13+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **Redis** - [Download Redis](https://redis.io/download)
- **Git** - [Download Git](https://git-scm.com/downloads)

### Optional (Recommended)
- **Docker & Docker Compose** - [Download Docker](https://www.docker.com/products/docker-desktop/)
- **Neo4j Desktop** - [Download Neo4j](https://neo4j.com/download/) (or use AuraDB)

## Quick Start with Docker (Recommended)

### 1. Clone the Repository
```bash
git clone https://github.com/chethanmp6/telegram-appointment-bot.git
cd telegram-appointment-bot
```

### 2. Create Environment File
```bash
cp .env.example .env
```

### 3. Configure Environment Variables
Edit `.env` file with your settings:
```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=appointment_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=appointment_db

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Neo4j Configuration (use AuraDB or local)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# API Keys
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
PINECONE_API_KEY=your_pinecone_api_key    # Optional

# Vector Database
VECTOR_DB_PROVIDER=pinecone  # or chroma, weaviate

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### 4. Start Services with Docker Compose
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis cache
- Neo4j database (optional)
- Application server

### 5. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 6. Initialize Databases
```bash
# Initialize PostgreSQL tables
python -c "from app.core.database import create_tables; import asyncio; asyncio.run(create_tables())"

# Initialize Neo4j schema (if using local Neo4j)
python -c "from app.core.graph_db import init_graph_database; import asyncio; asyncio.run(init_graph_database())"
```

### 7. Start the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Manual Setup (Without Docker)

### 1. Install PostgreSQL
```bash
# macOS with Homebrew
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Windows
# Download and install from https://www.postgresql.org/download/windows/
```

### 2. Create Database and User
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE appointment_db;
CREATE USER appointment_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE appointment_db TO appointment_user;

# Exit PostgreSQL
\q
```

### 3. Install Redis
```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Windows
# Download from https://redis.io/download or use WSL
```

### 4. Install Neo4j (Optional - Local)
```bash
# macOS with Homebrew
brew install neo4j
brew services start neo4j

# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j

# Windows
# Download Neo4j Desktop from https://neo4j.com/download/
```

### 5. Configure Neo4j
```bash
# Start Neo4j and access at http://localhost:7474
# Default credentials: neo4j/neo4j
# Change password on first login
```

## Environment Configuration

### Create `.env` File
```bash
# Application Settings
APP_NAME=Telegram Appointment Bot
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=appointment_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=appointment_db

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# API Keys (Required)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key

# Optional API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key
PINECONE_API_KEY=your_pinecone_api_key

# Vector Database Provider
VECTOR_DB_PROVIDER=pinecone  # Options: pinecone, chroma, weaviate

# Business Configuration
BUSINESS_NAME=Your Business Name
CANCELLATION_HOURS=24
BOOKING_ADVANCE_DAYS=30
DEFAULT_APPOINTMENT_DURATION=60

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### Get API Keys

#### Telegram Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token

#### OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Copy the API key

#### Pinecone API Key (Optional)
1. Go to [Pinecone Console](https://app.pinecone.io/)
2. Create account and project
3. Copy API key from dashboard

## Running the Application

### 1. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
# Create database tables
python -c "from app.core.database import create_tables; import asyncio; asyncio.run(create_tables())"

# Initialize Neo4j schema
python -c "from app.core.graph_db import init_graph_database; import asyncio; asyncio.run(init_graph_database())"
```

### 3. Start the Application
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access the Application
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Main Application**: http://localhost:8000/

## Testing the Setup

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-11T...",
  "database": true,
  "graph_db": true,
  "vector_db": true,
  "llm_service": true,
  "telegram_bot": true
}
```

### 2. Test Telegram Webhook
```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/api/v1/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 12345,
    "message": {
      "message_id": 1,
      "from": {
        "id": 123456789,
        "first_name": "Test",
        "is_bot": false
      },
      "chat": {
        "id": 123456789,
        "type": "private"
      },
      "date": 1641234567,
      "text": "Hello"
    }
  }'
```

### 3. Create Test Data
```bash
# Create staff member
curl -X POST http://localhost:8000/api/v1/appointments/staff \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Smith",
    "email": "dr.smith@clinic.com",
    "phone": "+1-555-0123",
    "specializations": ["consultation", "general"],
    "working_hours": {
      "monday": {"start": "09:00", "end": "17:00"},
      "tuesday": {"start": "09:00", "end": "17:00"},
      "wednesday": {"start": "09:00", "end": "17:00"},
      "thursday": {"start": "09:00", "end": "17:00"},
      "friday": {"start": "09:00", "end": "17:00"}
    }
  }'

# Create service
curl -X POST http://localhost:8000/api/v1/appointments/services \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Consultation",
    "description": "General consultation",
    "duration": 30,
    "price": 50.0,
    "category": "Medical"
  }'
```

## Development Workflow

### 1. Making Changes
```bash
# The application will auto-reload when you save changes
# No need to restart the server in development mode
```

### 2. Database Migrations
```bash
# If you modify database models, create new tables
python -c "from app.core.database import create_tables; import asyncio; asyncio.run(create_tables())"
```

### 3. Testing
```bash
# Run tests
pytest

# Run specific test file
pytest app/tests/test_appointments.py

# Run with coverage
pytest --cov=app
```

### 4. Linting and Formatting
```bash
# Format code
black app/

# Check linting
flake8 app/

# Type checking
mypy app/
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Check connection
psql -U appointment_user -d appointment_db -h localhost
```

#### 2. Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# Check Redis status
sudo systemctl status redis-server  # Linux
brew services list | grep redis  # macOS
```

#### 3. Neo4j Connection Error
```bash
# Check Neo4j status
sudo systemctl status neo4j  # Linux
brew services list | grep neo4j  # macOS

# Access Neo4j browser
# http://localhost:7474
```

#### 4. Import Errors
```bash
# Make sure you're in the project directory
cd /path/to/telegram-appointment-bot

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 5. Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>
```

## VS Code Setup (Recommended)

### 1. Install Extensions
- Python
- Python Docstring Generator
- Black Formatter
- SQLTools
- Redis Explorer

### 2. Configure Settings
Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### 3. Configure Launch Configuration
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Development",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "jinja": true,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

## Production Deployment

For production deployment, refer to:
- `AZURE_DEPLOYMENT.md` for Azure deployment
- `docker-compose.prod.yml` for Docker production setup

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs: `tail -f logs/app.log`
3. Check health endpoint: `curl http://localhost:8000/health`
4. Verify environment variables are set correctly

Happy coding! 🚀