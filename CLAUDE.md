# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Telegram appointment booking bot built with FastAPI, featuring:
- **Multi-database architecture**: PostgreSQL, Neo4j, and vector databases
- **Agentic RAG system**: Intelligent knowledge retrieval with graph intelligence
- **LLM integration**: OpenAI/Anthropic with function calling
- **Graph-based recommendations**: Personalized suggestions using relationship analysis

## Architecture

### Core Components
- **FastAPI Backend** (`app/main.py`): Async API with dependency injection
- **Telegram Bot** (`app/services/telegram_service.py`): Natural language conversation handling
- **LLM Service** (`app/services/llm_service.py`): Function calling with OpenAI/Anthropic
- **RAG Service** (`app/services/rag_service.py`): Vector search with graph intelligence
- **Graph Database** (`app/core/graph_db.py`): Neo4j for relationship modeling
- **Appointment Service** (`app/services/appointment_service.py`): Multi-database coordination

### Database Architecture
- **PostgreSQL**: Transactional data (appointments, customers, services)
- **Neo4j**: Relationship graphs (preferences, recommendations, service dependencies)
- **Vector DB**: Knowledge embeddings (Pinecone/ChromaDB/Weaviate)

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys and database settings

# Start with Docker
docker-compose up -d

# Or run locally (requires databases to be running)
uvicorn app.main:app --reload
```

### Database Management
```bash
# Initialize PostgreSQL tables
python -c "from app.core.database import create_tables; import asyncio; asyncio.run(create_tables())"

# Initialize Neo4j schema
python -c "from app.core.graph_db import init_graph_database; import asyncio; asyncio.run(init_graph_database())"

# Reset databases (development only)
curl -X POST http://localhost:8000/debug/reset-database
```

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Test Telegram webhook
curl -X POST http://localhost:8000/api/v1/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": {"text": "hello", "from": {"id": 123}}}'
```

## Key Features

### Intelligent Conversation Flow
- Natural language understanding for appointment booking
- Context-aware responses using graph relationships
- Multi-turn conversation state management
- Personalized recommendations based on customer history

### Multi-Database Integration
- **Transactional consistency**: PostgreSQL for critical data
- **Relationship intelligence**: Neo4j for preferences and recommendations
- **Semantic search**: Vector database for knowledge retrieval
- **Coordinated operations**: Atomic updates across all systems

### Function Calling
The LLM can execute these functions:
- `check_availability()` - Real-time slot checking
- `book_appointment()` - Create appointments with validation
- `search_knowledge_base()` - RAG-powered information retrieval
- `get_customer_preferences()` - Graph-based personalization
- `recommend_services()` - AI-driven service suggestions

## Configuration

### Required Environment Variables
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: LLM access
- `TELEGRAM_BOT_TOKEN`: Bot authentication
- `POSTGRES_*`: Database connection settings
- `NEO4J_*`: Graph database settings
- `VECTOR_DB_PROVIDER`: Pinecone/Chroma/Weaviate choice

### Business Configuration
- `BUSINESS_NAME`: Your business name
- `CANCELLATION_HOURS`: Policy enforcement
- `BOOKING_ADVANCE_DAYS`: Availability window
- `DEFAULT_APPOINTMENT_DURATION`: Service defaults

## Service Dependencies

### Service Initialization Order
1. Database connections (PostgreSQL, Neo4j, Redis)
2. Vector database and embeddings
3. LLM service with function definitions
4. RAG service with graph integration
5. Telegram bot with conversation management

### Inter-Service Communication
- **LLM ↔ Appointment Service**: Function calling for bookings
- **RAG ↔ Graph DB**: Knowledge enrichment with relationships
- **Telegram ↔ All Services**: Coordinated through intelligent agent
- **Graph ↔ PostgreSQL**: Synchronized updates for consistency

## Testing Strategy

### Unit Tests
```bash
pytest app/tests/unit/ -v
```

### Integration Tests
```bash
pytest app/tests/integration/ -v
```

### End-to-End Tests
```bash
pytest app/tests/e2e/ -v
```

## Monitoring and Observability

### Health Checks
- `/health`: Overall system status
- `/api/v1/graph/health`: Neo4j connectivity
- `/api/v1/knowledge/health`: RAG system status

### Logging
- Structured JSON logging
- Service-specific log levels
- Request/response tracing
- Error aggregation

## Production Deployment

### Docker Deployment
```bash
# Production stack
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up --scale celery_worker=3
```

### Environment Setup
- Use production database credentials
- Configure webhook URLs for Telegram
- Set up SSL certificates for HTTPS
- Configure monitoring and alerting

## Common Issues

### Database Connection Errors
- Check PostgreSQL connection strings
- Verify Neo4j authentication
- Ensure vector database is accessible

### LLM Function Calling Issues
- Validate API keys and quotas
- Check function parameter schemas
- Review error logs for timeout issues

### Graph Query Performance
- Monitor query execution times
- Use appropriate indexes
- Optimize relationship traversals

## Development Best Practices

### Code Organization
- Follow async/await patterns throughout
- Use dependency injection for services
- Implement proper error handling
- Maintain clear separation of concerns

### Database Operations
- Use transactions for multi-table operations
- Coordinate PostgreSQL and Neo4j updates
- Handle connection pooling appropriately
- Implement proper retry logic

### Security Considerations
- Never log sensitive information
- Validate all user inputs
- Use parameterized queries
- Secure API endpoints appropriately