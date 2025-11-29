#!/bin/bash
# Complete Proton VPN installation - fixes expired key and installs CLI

set -e

echo "=========================================="
echo "Installing Proton VPN CLI"
echo "=========================================="
echo ""

echo "Step 1: Fixing expired GPG key..."
# Download fresh key
wget -qO /tmp/protonvpn-key.asc https://repo.protonvpn.com/debian/public_key.asc

# Remove old expired keyring
sudo rm -f /usr/share/keyrings/protonvpn-stable-archive-keyring.gpg

# Import new key
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/protonvpn-stable-archive-keyring.gpg --import /tmp/protonvpn-key.asc

echo "✅ GPG key updated"

echo ""
echo "Step 2: Updating package lists..."
sudo apt-get update

echo ""
echo "Step 3: Installing Proton VPN CLI..."
sudo apt-get install -y protonvpn-cli

echo ""
echo "Step 4: Verifying installation..."
if command -v protonvpn-cli &> /dev/null; then
    echo "✅ Proton VPN CLI installed successfully!"
    protonvpn-cli --version
    echo ""
    echo "=========================================="
    echo "Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Fix DNS (optional): sudo resolvectl dns ens18 1.1.1.1 1.0.0.1"
    echo "2. Initialize: sudo protonvpn-cli init"
    echo "3. Login: sudo protonvpn-cli login"
    echo "4. Connect: sudo protonvpn-cli connect --fastest"
else
    echo "❌ Installation failed - protonvpn command not found"
    exit 1
fi

# Cleanup
rm -f /tmp/protonvpn-key.asc

