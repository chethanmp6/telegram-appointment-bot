# 🤖 Telegram Appointment Booking Bot

A comprehensive AI-powered appointment booking system built with FastAPI, featuring multi-database architecture, agentic RAG, and graph-based intelligence.

## 🌟 Features

### 🧠 **Intelligent AI Agent**
- **Natural Language Processing**: Book appointments using conversational language
- **Function Calling**: OpenAI/Anthropic LLM integration with intelligent function execution
- **Multi-turn Conversations**: Context-aware dialogue management
- **Smart Recommendations**: Graph-based personalized suggestions

### 🏗️ **Multi-Database Architecture**
- **PostgreSQL**: Transactional data (appointments, customers, services)
- **Neo4j**: Relationship graphs (preferences, recommendations, service dependencies)
- **Vector Database**: Knowledge embeddings (Pinecone/ChromaDB/Weaviate)
- **Redis**: Caching and background task queues

### 🔍 **Agentic RAG System**
- **Semantic Search**: Vector-based knowledge retrieval
- **Graph Intelligence**: Relationship-aware information processing
- **Context Enrichment**: Dynamic knowledge integration
- **Intelligent Agents**: Autonomous information gathering and processing

### 📱 **Telegram Integration**
- **Webhook Support**: Real-time message processing
- **Interactive Keyboards**: Quick actions and responses
- **Conversation State Management**: Persistent user sessions
- **Rich Media Support**: Text, buttons, and inline responses

### ☁️ **Multi-Cloud Deployment**
- **AWS**: ECS Fargate + RDS + ElastiCache
- **Google Cloud**: Cloud Run + Cloud SQL + Memorystore
- **Azure**: Container Instances + Database + Redis Cache
- **Kubernetes**: Universal deployment across any cloud

## 🚀 Quick Start

### Option 1: AWS Deployment (30 minutes)
```bash
git clone https://github.com/yourusername/appointment-manager.git
cd appointment-manager
aws configure
./deployment/aws/deploy.sh prod
```

### Option 2: Google Cloud Deployment (30 minutes)
```bash
git clone https://github.com/yourusername/appointment-manager.git
cd appointment-manager
gcloud auth login
./deployment/gcp/deploy.sh prod YOUR_PROJECT_ID
```

### Option 3: Local Development
```bash
git clone https://github.com/yourusername/appointment-manager.git
cd appointment-manager
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram      │───▶│   FastAPI        │───▶│   LLM Service   │
│   Bot           │    │   Backend        │    │   (OpenAI)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Intelligent    │
                       │   Agent          │
                       └──────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ PostgreSQL   │ │    Neo4j     │ │  Vector DB   │
        │ (Transact)   │ │  (Graph)     │ │   (RAG)      │
        └──────────────┘ └──────────────┘ └──────────────┘
```

## 📋 Prerequisites

### Required Accounts
- **Telegram Bot Token** (from @BotFather)
- **OpenAI API Key** or **Anthropic API Key**
- **Cloud Provider Account** (AWS/GCP/Azure)
- **Neo4j AuraDB** (recommended) or self-hosted Neo4j
- **Vector Database** (Pinecone recommended)

### Required Tools
- Docker & Docker Compose
- Python 3.11+
- Cloud CLI (AWS CLI / gcloud / Azure CLI)
- kubectl (for Kubernetes deployments)

## 🔧 Configuration

### Environment Variables
```bash
# Core Application
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
BUSINESS_NAME="Your Business Name"

# Databases
POSTGRES_HOST=localhost
NEO4J_URI=bolt://localhost:7687
REDIS_HOST=localhost

# Vector Database
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=your_pinecone_api_key

# See .env.example for complete configuration
```

## 🎯 API Endpoints

### Health & Status
- `GET /health` - System health check
- `GET /` - API information

### Appointments
- `POST /api/v1/appointments` - Book appointment
- `GET /api/v1/appointments/customer/{id}` - Get customer appointments
- `POST /api/v1/appointments/availability` - Check availability

### Knowledge Base
- `POST /api/v1/knowledge/search` - Search knowledge base
- `POST /api/v1/knowledge/documents/upload` - Upload documents

### Graph Intelligence
- `GET /api/v1/graph/customers/{id}/recommendations` - Get recommendations
- `POST /api/v1/graph/customers/{id}/preferences` - Update preferences

### Telegram
- `POST /webhook/{secret}` - Telegram webhook endpoint

## 🧪 Testing

### Run Tests
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest app/tests/ -v

# Run with coverage
pytest app/tests/ --cov=app --cov-report=html
```

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## 🚀 Deployment

### Quick Deployment

#### AWS (ECS + RDS)
```bash
./deployment/aws/deploy.sh prod
```

#### Google Cloud (Cloud Run)
```bash
./deployment/gcp/deploy.sh prod PROJECT_ID
```

#### Kubernetes
```bash
kubectl apply -f deployment/kubernetes/
```

### CI/CD Pipeline
The included GitHub Actions workflow provides:
- Automated testing and linting
- Security scanning
- Multi-cloud deployment
- Environment-specific deployments

See [Deployment Guide](deployment/DEPLOYMENT_GUIDE.md) for detailed instructions.

## 📊 Monitoring & Observability

### Health Checks
- Application: `/health`
- Database: `/api/v1/graph/health`
- Knowledge Base: `/api/v1/knowledge/health`

### Logging
- Structured JSON logging
- Cloud-native log aggregation
- Request/response tracing
- Error tracking and alerting

### Metrics
- Response time monitoring
- Database performance tracking
- LLM usage analytics
- Business metrics (bookings, cancellations)

## 🔐 Security

### Authentication & Authorization
- API key management via cloud secret stores
- Telegram webhook verification
- Rate limiting and abuse prevention

### Data Security
- Encryption at rest and in transit
- Secure database connections
- Secret management best practices
- GDPR compliance considerations

### Network Security
- VPC/VNET isolation
- Security groups and firewall rules
- Private database access
- HTTPS/TLS everywhere

## 🎛️ Configuration

### Business Logic
```python
# Customize business rules in app/core/config.py
BUSINESS_TIMEZONE = "UTC"
DEFAULT_APPOINTMENT_DURATION = 60  # minutes
BOOKING_ADVANCE_DAYS = 30
CANCELLATION_HOURS = 24
```

### LLM Function Calling
The system supports these intelligent functions:
- `check_availability()` - Real-time slot checking
- `book_appointment()` - Smart appointment creation
- `search_knowledge_base()` - RAG-powered information
- `recommend_services()` - Graph-based suggestions
- `get_customer_preferences()` - Personalization data

### Knowledge Base
Upload business documents via API:
```bash
curl -X POST "/api/v1/knowledge/documents/upload" \
  -F "files=@business-policies.pdf" \
  -F "document_type=policy"
```

## 🔄 Scaling

### Horizontal Scaling
- **AWS**: ECS service auto-scaling
- **GCP**: Cloud Run automatic scaling
- **Kubernetes**: Horizontal Pod Autoscaler (HPA)

### Database Scaling
- **PostgreSQL**: Read replicas and connection pooling
- **Neo4j**: Clustering and read replicas
- **Redis**: Clustering for high availability

### Performance Optimization
- Vector database indexing
- Graph query optimization
- LLM response caching
- Database query optimization

## 🛠️ Development

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/yourusername/appointment-manager.git
cd appointment-manager

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d

# Run application
uvicorn app.main:app --reload
```

### Project Structure
```
app/
├── main.py              # FastAPI application
├── core/                # Core configuration and database
├── services/            # Business logic services
├── api/                 # API route handlers  
├── models/              # Database and API schemas
└── utils/               # Utility functions

deployment/
├── aws/                 # AWS deployment files
├── gcp/                 # Google Cloud deployment
├── azure/               # Azure deployment
└── kubernetes/          # Kubernetes manifests
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📚 Documentation

- **[Quick Start Guide](deployment/QUICK_START.md)** - Get running in 30 minutes
- **[Deployment Guide](deployment/DEPLOYMENT_GUIDE.md)** - Comprehensive deployment instructions
- **[CLAUDE.md](CLAUDE.md)** - Development guidance for Claude Code
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs

## 🤝 Support

### Getting Help
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and questions
- **Documentation**: Comprehensive guides and examples

### Professional Support
- Cloud deployment consulting
- Custom feature development
- Enterprise support contracts
- Training and workshops

## 💰 Cost Estimates

| Cloud Provider | Development | Production | Enterprise |
|----------------|-------------|------------|------------|
| **AWS** | $50-100/month | $200-500/month | $500-1000+/month |
| **Google Cloud** | $30-80/month | $150-400/month | $400-800+/month |
| **Azure** | $40-90/month | $180-450/month | $450-900+/month |

*Costs vary based on usage, region, and specific configuration*

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Acknowledgments

- **FastAPI**: Modern Python web framework
- **Telegram Bot API**: Messaging platform integration
- **OpenAI/Anthropic**: LLM providers
- **Neo4j**: Graph database technology
- **Cloud Providers**: AWS, GCP, Azure infrastructure

---

## 🚀 Ready to Deploy?

Choose your preferred deployment method:

```bash
# AWS (Recommended for Enterprise)
./deployment/aws/deploy.sh prod

# Google Cloud (Recommended for Startups)  
./deployment/gcp/deploy.sh prod YOUR_PROJECT_ID

# Kubernetes (Multi-cloud)
kubectl apply -f deployment/kubernetes/
```

Your intelligent appointment booking bot will be live in minutes! 🎯