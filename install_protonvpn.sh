#!/bin/bash
# Proton VPN CLI Official Installation Script
# Run this script to properly install Proton VPN CLI via apt repository

set -e  # Exit on error

echo "=========================================="
echo "Proton VPN CLI Official Installation"
echo "=========================================="
echo ""

# Step 1: Install repository package
echo "Step 1: Installing Proton VPN repository..."
if [ ! -f /tmp/protonvpn-stable-release.deb ]; then
    echo "   Downloading repository package..."
    wget -q https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.3_all.deb -O /tmp/protonvpn-stable-release.deb
fi
sudo dpkg -i /tmp/protonvpn-stable-release.deb

# Step 2: Import GPG key (required for repository verification)
echo ""
echo "Step 2: Importing Proton VPN GPG key..."
# Check if key is already imported (modern method)
KEY_IMPORTED=false
if [ -f /etc/apt/trusted.gpg.d/protonvpn-stable-release.gpg ] || \
   [ -f /usr/share/keyrings/protonvpn-stable-release.gpg ] || \
   (sudo apt-key list 2>/dev/null | grep -q "EDA3E22630349F1C" 2>/dev/null); then
    echo "   ✅ GPG key already imported"
    KEY_IMPORTED=true
fi

if [ "$KEY_IMPORTED" = false ]; then
    echo "   Downloading GPG key..."
    # Try modern method first (Ubuntu 22.04+)
    if wget -qO- https://repo.protonvpn.com/debian/public_key.asc 2>/dev/null | \
       sudo gpg --dearmor -o /usr/share/keyrings/protonvpn-stable-release.gpg 2>/dev/null; then
        echo "   ✅ GPG key imported (modern method)"
        KEY_IMPORTED=true
    # Fallback to apt-key (older Ubuntu versions)
    elif sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys EDA3E22630349F1C 2>/dev/null; then
        echo "   ✅ GPG key imported (keyserver method)"
        KEY_IMPORTED=true
    elif sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EDA3E22630349F1C 2>/dev/null; then
        echo "   ✅ GPG key imported (alternative keyserver)"
        KEY_IMPORTED=true
    else
        echo "   ⚠️  Could not automatically import GPG key"
        echo "   You may need to import it manually:"
        echo "   wget -qO- https://repo.protonvpn.com/debian/public_key.asc | sudo apt-key add -"
    fi
fi

# Step 3: Update package lists
echo ""
echo "Step 3: Updating package lists..."
sudo apt-get update

# Step 4: Install Proton VPN CLI
echo ""
echo "Step 4: Installing Proton VPN CLI..."
sudo apt-get install -y protonvpn-cli

# Step 5: Verify installation
echo ""
echo "Step 5: Verifying installation..."
if command -v protonvpn &> /dev/null; then
    echo "✅ Proton VPN CLI installed successfully!"
    protonvpn --version
    echo ""
    echo "Next steps:"
    echo "1. Initialize: sudo protonvpn init"
    echo "2. Login: sudo protonvpn login"
    echo "3. Connect: sudo protonvpn connect --fastest"
else
    echo "❌ Installation failed - protonvpn command not found"
    exit 1
fi

# Cleanup
echo ""
echo "Cleaning up temporary files..."
rm -f /tmp/protonvpn-stable-release.deb

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="

