#!/bin/bash

# Setup script for blockchain node (BigchainDB or Multichain)

echo "Healthcare Blockchain - Blockchain Setup"
echo "=========================================="

# Check which blockchain provider to use
read -p "Which blockchain provider? (bigchaindb/multichain) [bigchaindb]: " provider
provider=${provider:-bigchaindb}

if [ "$provider" == "bigchaindb" ]; then
    echo "Setting up BigchainDB..."
    
    # Check if BigchainDB is installed
    if ! command -v bigchaindb &> /dev/null; then
        echo "Installing BigchainDB..."
        pip install bigchaindb-driver
    fi
    
    echo "Starting BigchainDB node..."
    echo "Note: BigchainDB setup requires additional configuration."
    echo "Please refer to: https://docs.bigchaindb.com/projects/server/en/latest/install/index.html"
    
elif [ "$provider" == "multichain" ]; then
    echo "Setting up Multichain..."
    
    # Check OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v multichaind &> /dev/null; then
            echo "Installing Multichain via Homebrew..."
            brew install multichain
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if ! command -v multichaind &> /dev/null; then
            echo "Installing Multichain..."
            wget https://www.multichain.com/download/multichain-latest.tar.gz
            tar -xvf multichain-latest.tar.gz
            cd multichain-*
            sudo ./setup.sh
        fi
    fi
    
    echo "Creating Multichain..."
    read -p "Chain name [healthcare-chain]: " chain_name
    chain_name=${chain_name:-healthcare-chain}
    
    if [ ! -d "$HOME/.multichain/$chain_name" ]; then
        multichain-util create "$chain_name"
        echo "Starting Multichain daemon..."
        multichaind "$chain_name" -daemon
        echo "Multichain started! Chain data at: $HOME/.multichain/$chain_name"
    else
        echo "Chain already exists. Starting daemon..."
        multichaind "$chain_name" -daemon
    fi
    
else
    echo "Invalid provider. Please choose 'bigchaindb' or 'multichain'"
    exit 1
fi

echo ""
echo "Blockchain setup complete!"
echo "Update your .env file with the correct BLOCKCHAIN_NODE URL"

