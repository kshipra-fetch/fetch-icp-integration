#!/bin/bash
set -e

echo "🚀 Setting up devcontainer..."

# Install npm dependencies
echo "📦 Installing npm dependencies..."
cd ic && npm install
cd ..

# Set up dfx identity for codespace
echo "🔑 Setting up dfx identity..."
dfx identity new codespace_dev --storage-mode=plaintext || echo "Identity may already exist"
dfx identity use codespace_dev      
dfx start --background             
dfx stop

echo "✅ Devcontainer setup complete!"