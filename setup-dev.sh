#!/bin/bash
set -e

echo "Setting up Python development environment..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}INFO: $1${NC}"
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip3 install --upgrade pip

# Install development dependencies
print_status "Installing development dependencies..."
pip3 install -r lambda_functions/requirements.txt

print_success "Development environment ready!"
echo ""
echo "To activate the environment in future sessions:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  python3 -m pytest tests/ -v"
echo ""
echo "To deploy:"
echo "  ./deploy.sh"