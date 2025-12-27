#!/bin/bash


set -e


# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

if [[ $EUID -eq 0 ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

echo ""
print_status "Updating system packages..."
$SUDO apt-get update -y
$SUDO apt-get upgrade -y

if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    $SUDO apt-get install -y ca-certificates curl gnupg lsb-release
    
    $SUDO mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | $SUDO tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    $SUDO apt-get update -y
    $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    $SUDO usermod -aG docker $USER
    print_status "Docker installed successfully!"
else
    print_status "Docker is already installed"
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_status "Installing Docker Compose..."
    $SUDO curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    $SUDO chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully!"
else
    print_status "Docker Compose is already installed"
fi

print_status "Starting Docker service..."
$SUDO systemctl start docker
$SUDO systemctl enable docker

# Install rsync for better file copying
if ! command -v rsync &> /dev/null; then
    print_status "Installing rsync..."
    $SUDO apt-get install -y rsync
fi

APP_DIR="/opt/vapi-voice-agent"
print_status "Creating application directory at $APP_DIR..."
$SUDO mkdir -p $APP_DIR
$SUDO chown -R $USER:$USER $APP_DIR

if [ -f "docker-compose.yml" ]; then
    print_status "Found docker-compose.yml in current directory"
    print_status "Copying application files (excluding .git and .env)..."
    
    # Use rsync to copy files, excluding .git directory and .env file
    rsync -av --exclude='.git' --exclude='.env' --exclude='*.db' --exclude='__pycache__' --exclude='*.pyc' . $APP_DIR/
    
    print_status "Files copied successfully"
elif [ -f "$APP_DIR/docker-compose.yml" ]; then
    print_status "Application already exists in $APP_DIR"
else
    print_warning "Please copy your application files to $APP_DIR"
    print_warning "Or clone your repository to $APP_DIR"
    echo ""
    echo "Example:"
    echo "  scp -r /path/to/vapi_voice_agent/* ubuntu@your-ec2-ip:$APP_DIR/"
    echo "  OR"
    echo "  git clone your-repo-url $APP_DIR"
    exit 1
fi

cd $APP_DIR

if [ ! -f ".env" ]; then
    print_warning "Creating .env file from template..."
    cat > .env << 'EOF'
# VAPI Configuration
VAPI_API_KEY=965ae1ac-2c85-4ace-8f46-34df5411b87a
VAPI_API_URL=https://api.vapi.ai
# VAPI_PUBLIC_KEY=your_public_key_here
DEFAULT_ASSISTANT_ID=1f97450a-9d2f-4e39-8948-02582a67274b
DEFAULT_PHONE_NUMBER_ID=+918348854111
EOF
    print_warning "Please edit .env file with your actual VAPI credentials!"
    print_warning "Run: nano $APP_DIR/.env"
fi

print_status "Building Docker image..."
$SUDO docker compose build --no-cache

print_status "Starting application..."
$SUDO docker compose up -d

echo ""
print_status "Waiting for application to start..."
sleep 10

if $SUDO docker compose ps | grep -q "Up"; then
    print_status "Application is running!"
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo "=========================================="
    echo ""
    echo "Your VAPI Voice Agent is now running at:"
    echo "  - Local:  http://localhost:8000"
    echo "  - Public: http://$(curl -s ifconfig.me):8000"
    echo ""
    echo "API Documentation: http://$(curl -s ifconfig.me):8000/docs"
    echo "Test Page: http://$(curl -s ifconfig.me):8000/test-call"
    echo ""
    echo "Useful commands:"
    echo "  View logs:     docker compose logs -f"
    echo "  Stop:          docker compose down"
    echo "  Restart:       docker compose restart"
    echo "  Rebuild:       docker compose up -d --build"
    echo ""
else
    print_error "Application failed to start!"
    echo "Check logs with: docker compose logs"
    exit 1
fi

