#!/bin/bash
set -e

echo "--- Checking Memory/Swap ---"

# Check if swap already exists
if [ -f /swapfile ]; then
    echo "Swap file already exists. Skipping creation."
else
    echo "Creating 2GB Swap file..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    
    # Tuning
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' | tee -a /etc/sysctl.conf
    
    echo "Swap created successfully."
fi

free -h
