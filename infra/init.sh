
#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║        Local-First Agentic Assistant Setup            ║"
echo "║              Initialization Script v1.0               ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
log_info "Checking prerequisites..."

# Check for Python 3.11+
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    log_error "Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi
log_success "Python $PYTHON_VERSION found"

# Check for Node.js 18+
if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    log_error "Node.js 18 or higher is required. Found: v$NODE_VERSION"
    exit 1
fi
log_success "Node.js $(node -v) found"

# Check for SQLite3
if ! command -v sqlite3 &> /dev/null; then
    log_error "SQLite3 is not installed. Please install SQLite3."
    exit 1
fi
log_success "SQLite3 found"

# Check for Docker (optional but recommended)
if command -v docker &> /dev/null; then
    log_success "Docker found (optional)"
else
    log_warning "Docker not found. Some features may require Docker."
fi

# Load environment variables
log_info "Setting up environment..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        log_success "Created .env file from .env.example"
        log_warning "Please edit .env file to set your configuration"
    else
        log_error ".env.example file not found"
        exit 1
    fi
else
    log_info ".env file already exists"
fi

# Source the .env file
set -a
source .env
set +a

# Create necessary directories
log_info "Creating directory structure..."
mkdir -p data/{logs,audit,user_files,screenshots,embeddings}
mkdir -p /tmp/agent_workspace
log_success "Directories created"

# Setup SQLite database
log_info "Setting up SQLite database..."
if [ ! -f "$DATABASE_PATH" ]; then
    sqlite3 "$DATABASE_PATH" "VACUUM;"
    log_success "Database created at $DATABASE_PATH"
    
    # Create initial schema
    sqlite3 "$DATABASE_PATH" <<EOF
-- Users table (simplified)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    passphrase_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    settings TEXT DEFAULT '{}'
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    title TEXT,
    mode TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER REFERENCES conversations(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    status TEXT DEFAULT 'pending',
    type TEXT NOT NULL,
    params TEXT NOT NULL,
    result TEXT,
    error TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
EOF
    log_success "Database schema created"
else
    log_info "Database already exists at $DATABASE_PATH"
fi

# Setup audit database
log_info "Setting up audit database..."
if [ ! -f "$AUDIT_LOG_PATH" ]; then
    sqlite3 "$AUDIT_LOG_PATH" <<EOF
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource TEXT,
    details TEXT,
    ip_address TEXT,
    user_agent TEXT
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
EOF
    log_success "Audit database created"
else
    log_info "Audit database already exists"
fi

# Install/Setup Ollama
log_info "Setting up Ollama for local LLM..."
if ! command -v ollama &> /dev/null; then
    log_info "Installing Ollama..."
    
    # Detect OS
    OS="$(uname -s)"
    case "${OS}" in
        Linux*)
            curl -fsSL https://ollama.ai/install.sh | sh
            ;;
        Darwin*)
            if command -v brew &> /dev/null; then
                brew install ollama
            else
                log_error "Please install Ollama manually from https://ollama.ai"
                exit 1
            fi
            ;;
        *)
            log_error "Unsupported OS: ${OS}. Please install Ollama manually."
            exit 1
            ;;
    esac
    
    if command -v ollama &> /dev/null; then
        log_success "Ollama installed successfully"
    else
        log_error "Failed to install Ollama"
        exit 1
    fi
else
    log_info "Ollama is already installed"
fi

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    log_info "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    log_success "Ollama service started"
else
    log_info "Ollama service is already running"
fi

# Pull the default model
log_info "Pulling default LLM model ($OLLAMA_MODEL)..."
if ollama pull "$OLLAMA_MODEL" 2>/dev/null; then
    log_success "Model '$OLLAMA_MODEL' ready"
else
    log_warning "Failed to pull model '$OLLAMA_MODEL'. You may need to run 'ollama pull $OLLAMA_MODEL' manually."
fi

# Setup Python virtual environment
log_info "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
log_info "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# Create a temporary requirements file for base dependencies
cat > /tmp/base_requirements.txt <<EOF
# Core dependencies
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Authentication & Security
passlib[argon2]==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
slowapi==0.1.9

# Database
aiosqlite==0.19.0
sqlalchemy==2.0.25

# LLM & Embeddings
ollama==0.1.7
sentence-transformers==2.3.1
tiktoken==0.5.2
openai==1.10.0
anthropic==0.10.0
google-generativeai==0.3.2

# Vector search (we'll use sqlite-vec)
# sqlite-vec will be compiled separately

# Tools & Automation
playwright==1.41.0
aiofiles==23.2.1
python-magic==0.4.27

# Development
black==23.12.1
flake8==7.0.0
pytest==7.4.4
pytest-asyncio==0.23.3
pre-commit==3.6.0

# Utilities
python-dotenv==1.0.0
httpx==0.26.0
pyyaml==6.0.1
rich==13.7.0
EOF

pip install -r /tmp/base_requirements.txt > /dev/null 2>&1
log_success "Python dependencies installed"

# Install Playwright browsers
log_info "Installing Playwright browsers..."
playwright install chromium > /dev/null 2>&1
playwright install-deps > /dev/null 2>&1
log_success "Playwright browsers installed"

# Setup sqlite-vec extension
log_info "Setting up sqlite-vec extension..."
if [ ! -f "data/sqlite-vec.so" ]; then
    # Check if we can compile it
    if command -v gcc &> /dev/null; then
        log_info "Compiling sqlite-vec..."
        cd /tmp
        git clone https://github.com/asg017/sqlite-vec.git > /dev/null 2>&1
        cd sqlite-vec
        make sqlite-vec.so > /dev/null 2>&1
        cp sqlite-vec.so "$OLDPWD/data/"
        cd "$OLDPWD"
        rm -rf /tmp/sqlite-vec
        log_success "sqlite-vec compiled and installed"
    else
        log_warning "GCC not found. sqlite-vec extension will need to be installed manually."
        log_warning "Visit: https://github.com/asg017/sqlite-vec"
    fi
else
    log_info "sqlite-vec already installed"
fi

# Initialize pre-commit hooks
log_info "Setting up pre-commit hooks..."
pre-commit install > /dev/null 2>&1
log_success "Pre-commit hooks installed"

# Create initial admin user
log_info "Creating initial admin user..."
ADMIN_HASH=$(python3 -c "from passlib.context import CryptContext; print(CryptContext(schemes=['argon2']).hash('$ADMIN_PASSPHRASE'))")
sqlite3 "$DATABASE_PATH" "INSERT OR IGNORE INTO users (id, passphrase_hash) VALUES (1, '$ADMIN_HASH');"
log_success "Admin user created (passphrase from .env)"

# Summary
echo
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            Setup completed successfully! 🎉            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo
log_info "Next steps:"
echo "  1. Review and edit the .env file"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run 'make dev' to start development servers"
echo "  4. Visit http://localhost:8000 to access the application"
echo
log_warning "Note: Some features may require additional setup (see docs/)"
echo "Init complete."

