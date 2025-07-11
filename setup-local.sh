#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up Telegram Appointment Bot for Local Development${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if required tools are installed
check_requirements() {
    print_info "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11 or higher."
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    print_status "Python $python_version found"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed. You can install it from https://www.docker.com/products/docker-desktop/"
        print_info "Docker is recommended for easy database setup"
    else
        print_status "Docker found"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose is not installed"
    else
        print_status "Docker Compose found"
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install Git."
        exit 1
    fi
    print_status "Git found"
}

# Create virtual environment
setup_python_env() {
    print_info "Setting up Python environment..."
    
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    print_status "Python dependencies installed"
}

# Setup environment file
setup_env_file() {
    print_info "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        print_info "Creating .env file from template..."
        cp .env.example .env
        print_status ".env file created"
        
        print_warning "Please edit .env file with your API keys:"
        print_info "  - TELEGRAM_BOT_TOKEN: Get from @BotFather on Telegram"
        print_info "  - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys"
        print_info "  - PINECONE_API_KEY: Get from https://app.pinecone.io/ (optional)"
        print_info "  - ANTHROPIC_API_KEY: Get from https://console.anthropic.com/ (optional)"
        echo ""
        print_info "For development, you can keep the default database settings"
    else
        print_status ".env file already exists"
    fi
}

# Setup databases with Docker
setup_databases() {
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        print_info "Setting up databases with Docker..."
        
        # Start only the database services
        print_info "Starting PostgreSQL, Redis, Neo4j, and ChromaDB..."
        docker-compose up -d postgres redis neo4j chromadb
        
        print_info "Waiting for databases to be ready..."
        sleep 30
        
        # Check if databases are healthy
        if docker-compose ps | grep -q "healthy"; then
            print_status "Databases are running and healthy"
        else
            print_warning "Databases may still be starting up. Please wait a few more minutes."
        fi
        
        print_info "Database URLs:"
        print_info "  - PostgreSQL: localhost:5432"
        print_info "  - Redis: localhost:6379"
        print_info "  - Neo4j Browser: http://localhost:7474"
        print_info "  - ChromaDB: http://localhost:8001"
        
        print_info "Neo4j credentials: neo4j/password"
        
    else
        print_warning "Docker not available. You'll need to install databases manually."
        print_info "See LOCAL_DEVELOPMENT.md for manual installation instructions."
    fi
}

# Initialize database tables
init_databases() {
    print_info "Initializing database tables..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Wait a bit more for databases to be ready
    sleep 10
    
    # Initialize PostgreSQL tables
    print_info "Creating PostgreSQL tables..."
    python3 -c "
import asyncio
import sys
sys.path.append('.')
from app.core.database import create_tables
asyncio.run(create_tables())
print('PostgreSQL tables created successfully')
" 2>/dev/null && print_status "PostgreSQL tables created" || print_warning "PostgreSQL initialization failed (database may not be ready)"
    
    # Initialize Neo4j schema
    print_info "Creating Neo4j schema..."
    python3 -c "
import asyncio
import sys
sys.path.append('.')
from app.core.graph_db import init_graph_database
asyncio.run(init_graph_database())
print('Neo4j schema created successfully')
" 2>/dev/null && print_status "Neo4j schema created" || print_warning "Neo4j initialization failed (database may not be ready)"
}

# Create sample data
create_sample_data() {
    print_info "Creating sample data..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Create sample data script
    cat > create_sample_data.py << 'EOF'
import asyncio
import sys
sys.path.append('.')
from app.services.appointment_service import AppointmentService
from app.core.database import get_async_session
from app.core.graph_db import get_graph_db

async def create_sample_data():
    async with get_async_session() as session:
        appointment_service = AppointmentService(session, await get_graph_db())
        
        # Create sample staff
        try:
            staff_data = {
                "name": "Dr. Sarah Johnson",
                "email": "sarah.johnson@clinic.com",
                "phone": "+1-555-0123",
                "specializations": ["consultation", "general_practice"],
                "working_hours": {
                    "monday": {"start": "09:00", "end": "17:00"},
                    "tuesday": {"start": "09:00", "end": "17:00"},
                    "wednesday": {"start": "09:00", "end": "17:00"},
                    "thursday": {"start": "09:00", "end": "17:00"},
                    "friday": {"start": "09:00", "end": "17:00"}
                },
                "is_available": True
            }
            
            staff = await appointment_service.create_staff(staff_data)
            print(f"Created staff: {staff.name}")
            
            # Create sample service
            service_data = {
                "name": "General Consultation",
                "description": "General medical consultation",
                "duration": 30,
                "price": 100.0,
                "category": "Medical",
                "is_active": True
            }
            
            service = await appointment_service.create_service(service_data)
            print(f"Created service: {service.name}")
            
        except Exception as e:
            print(f"Error creating sample data: {e}")

if __name__ == "__main__":
    asyncio.run(create_sample_data())
EOF
    
    python3 create_sample_data.py && print_status "Sample data created" || print_warning "Sample data creation failed"
    rm create_sample_data.py
}

# Main setup process
main() {
    echo -e "${BLUE}Starting local development setup...${NC}"
    echo ""
    
    # Check if we're in the right directory
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found. Please run this script from the project root directory."
        exit 1
    fi
    
    check_requirements
    echo ""
    
    setup_python_env
    echo ""
    
    setup_env_file
    echo ""
    
    setup_databases
    echo ""
    
    # Wait for user to configure API keys
    if [ ! -f ".env" ] || ! grep -q "sk-" .env; then
        print_warning "Please configure your API keys in .env file before proceeding."
        print_info "Edit .env file with your actual API keys, then run:"
        print_info "  source venv/bin/activate"
        print_info "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
        echo ""
        print_info "You can also continue with database initialization:"
        print_info "  ./setup-local.sh --init-db"
        exit 0
    fi
    
    init_databases
    echo ""
    
    create_sample_data
    echo ""
    
    print_status "Local development setup complete! 🎉"
    echo ""
    print_info "To start the development server:"
    print_info "  source venv/bin/activate"
    print_info "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    print_info "Your application will be available at:"
    print_info "  - API: http://localhost:8000"
    print_info "  - Documentation: http://localhost:8000/docs"
    print_info "  - Health Check: http://localhost:8000/health"
    echo ""
    print_info "Database interfaces:"
    print_info "  - Neo4j Browser: http://localhost:7474 (neo4j/password)"
    print_info "  - ChromaDB: http://localhost:8001"
    echo ""
    print_info "For more information, see LOCAL_DEVELOPMENT.md"
}

# Handle command line arguments
if [ "$1" = "--init-db" ]; then
    source venv/bin/activate
    init_databases
    create_sample_data
    exit 0
fi

# Run main setup
main