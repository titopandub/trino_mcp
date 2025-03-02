#!/bin/bash
set -e

# Setup colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Trino MCP Server Test Runner${NC}"
echo "==============================="

# Check for virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}No virtual environment detected.${NC}"
    
    # Check if venv exists
    if [ -d "venv" ]; then
        echo -e "${GREEN}Activating existing virtual environment...${NC}"
        source venv/bin/activate
    else
        echo -e "${YELLOW}Creating new virtual environment...${NC}"
        python -m venv venv
        source venv/bin/activate
        echo -e "${GREEN}Installing dependencies...${NC}"
        pip install -e ".[dev]"
    fi
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check for Trino availability
echo -e "${YELLOW}Checking Trino availability...${NC}"

TRINO_HOST=${TEST_TRINO_HOST:-localhost}
TRINO_PORT=${TEST_TRINO_PORT:-9095}

if command_exists curl; then
    if curl -s -o /dev/null -w "%{http_code}" http://${TRINO_HOST}:${TRINO_PORT}/v1/info | grep -q "200"; then
        echo -e "${GREEN}Trino is available at ${TRINO_HOST}:${TRINO_PORT}${NC}"
    else
        echo -e "${RED}WARNING: Trino does not appear to be available at ${TRINO_HOST}:${TRINO_PORT}.${NC}"
        echo -e "${YELLOW}Some tests may be skipped or fail.${NC}"
        echo -e "${YELLOW}You may need to start Trino with Docker: docker-compose up -d${NC}"
        missing_trino=true
    fi
else
    echo -e "${YELLOW}curl not found, skipping Trino availability check${NC}"
fi

# Run the tests
echo -e "${YELLOW}Running unit tests...${NC}"
pytest tests/ -v --exclude=tests/integration

echo ""
echo -e "${YELLOW}Running integration tests...${NC}"
echo -e "${YELLOW}(These may be skipped if Docker is not available)${NC}"
pytest tests/integration/ -v

echo ""
echo -e "${GREEN}All tests completed!${NC}" 