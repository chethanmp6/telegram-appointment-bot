# Quick Start - Local Development

## 🚀 Super Quick Start (5 minutes)

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone https://github.com/chethanmp6/telegram-appointment-bot.git
cd telegram-appointment-bot

# Quick setup (automated)
./setup-local.sh
```

### Step 2: Configure API Keys
Edit `.env` file with your API keys:
```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
OPENAI_API_KEY=your_openai_api_key

# Optional
ANTHROPIC_API_KEY=your_anthropic_key
PINECONE_API_KEY=your_pinecone_key
```

### Step 3: Start Development
```bash
# Start everything (databases + app)
./start-dev.sh
```

That's it! Your bot is running at http://localhost:8000

## 📖 Getting API Keys

### Telegram Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token

### OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Copy the API key

## 🔧 Manual Setup (if automated script fails)

### 1. Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Databases
```bash
# Start only databases
docker-compose -f docker-compose.dev.yml up -d

# Check if healthy
docker-compose -f docker-compose.dev.yml ps
```

### 3. Initialize Databases
```bash
# Initialize PostgreSQL
python -c "from app.core.database import create_tables; import asyncio; asyncio.run(create_tables())"

# Initialize Neo4j
python -c "from app.core.graph_db import init_graph_database; import asyncio; asyncio.run(init_graph_database())"
```

### 4. Start Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 Access Points

After starting:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Neo4j Browser**: http://localhost:7474 (neo4j/password)
- **ChromaDB**: http://localhost:8001

## 🧪 Testing Your Setup

### Health Check
```bash
curl http://localhost:8000/health
```

### Create Test Data
```bash
# Create a staff member
curl -X POST http://localhost:8000/api/v1/appointments/staff \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Smith",
    "email": "dr.smith@clinic.com",
    "phone": "+1-555-0123",
    "specializations": ["consultation"],
    "working_hours": {
      "monday": {"start": "09:00", "end": "17:00"},
      "tuesday": {"start": "09:00", "end": "17:00"}
    }
  }'
```

### Test Telegram Webhook
```bash
curl -X POST http://localhost:8000/api/v1/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 1,
    "message": {
      "message_id": 1,
      "from": {"id": 123, "first_name": "Test", "is_bot": false},
      "chat": {"id": 123, "type": "private"},
      "date": 1641234567,
      "text": "Hello"
    }
  }'
```

## 🔄 Development Workflow

### Making Changes
- Application auto-reloads when you save files
- Database changes require restarting containers
- Environment changes require app restart

### Useful Commands
```bash
# Stop databases
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs

# Reset databases (removes all data)
docker-compose -f docker-compose.dev.yml down -v

# Start with admin interfaces
docker-compose -f docker-compose.dev.yml --profile admin up -d
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Issues
```bash
# Check database status
docker-compose -f docker-compose.dev.yml ps

# Restart databases
docker-compose -f docker-compose.dev.yml restart
```

### Virtual Environment Issues
```bash
# Remove and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📚 Next Steps

1. **Configure your Telegram bot** - Test with real messages
2. **Add your business data** - Staff, services, appointments
3. **Customize the bot** - Modify conversation flows
4. **Deploy to production** - See `AZURE_DEPLOYMENT.md`

## 🆘 Need Help?

- **Full Documentation**: `LOCAL_DEVELOPMENT.md`
- **Azure Deployment**: `AZURE_DEPLOYMENT.md`
- **API Reference**: http://localhost:8000/docs (when running)

Happy coding! 🎉