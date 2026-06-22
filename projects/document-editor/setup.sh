#!/bin/bash

# Document Editor - Setup Script
# Run this script to set up the project

echo "Setting up Document Editor..."

# Install dependencies
npm install

# Run tests
echo "Running tests..."
npm test

# Run examples
echo "Running basic editing example..."
npm run example:basic

echo "Running collaborative editing example..."
npm run example:collab

echo "Running version history example..."
npm run example:history

echo "Setup complete!"
