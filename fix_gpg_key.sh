#!/bin/bash
# Quick fix for Proton VPN GPG key issue
# Run this to import the missing GPG key and complete installation

set -e

echo "=========================================="
echo "Proton VPN GPG Key Fix"
echo "=========================================="
echo ""

echo "Step 1: Importing GPG key..."
# Try modern method first
if wget -qO- https://repo.protonvpn.com/debian/public_key.asc 2>/dev/null | \
   sudo gpg --dearmor -o /usr/share/keyrings/protonvpn-stable-release.gpg 2>/dev/null; then
    echo "✅ GPG key imported (modern method)"
elif sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys EDA3E22630349F1C 2>/dev/null; then
    echo "✅ GPG key imported (keyserver method)"
elif wget -qO- https://repo.protonvpn.com/debian/public_key.asc 2>/dev/null | sudo apt-key add - 2>/dev/null; then
    echo "✅ GPG key imported (direct method)"
else
    echo "❌ Failed to import GPG key automatically"
    echo ""
    echo "Try manually:"
    echo "  wget -qO- https://repo.protonvpn.com/debian/public_key.asc | sudo apt-key add -"
    exit 1
fi

echo ""
echo "Step 2: Updating package lists..."
sudo apt-get update

echo ""
echo "Step 3: Installing Proton VPN CLI..."
sudo apt-get install -y protonvpn-cli

echo ""
echo "Step 4: Verifying installation..."
if command -v protonvpn &> /dev/null; then
    echo "✅ Proton VPN CLI installed successfully!"
    protonvpn --version
    echo ""
    echo "Next steps:"
    echo "1. Fix network/DNS: sudo resolvectl dns ens18 1.1.1.1 1.0.0.1"
    echo "2. Initialize: sudo protonvpn init"
    echo "3. Login: sudo protonvpn login"
else
    echo "❌ Installation failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "GPG key fix complete!"
echo "=========================================="


