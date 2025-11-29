#!/bin/bash
# Complete Proton VPN Setup Script
# This script: installs Proton VPN, fixes network issues, and initializes

set -e

echo "=========================================="
echo "Complete Proton VPN Setup"
echo "=========================================="
echo ""

# Step 1: Install Proton VPN via apt
echo "Step 1: Installing Proton VPN repository..."
if [ ! -f /tmp/protonvpn-stable-release.deb ]; then
    echo "   Downloading repository package..."
    wget -q https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.3_all.deb -O /tmp/protonvpn-stable-release.deb
fi

echo "   Installing repository..."
sudo dpkg -i /tmp/protonvpn-stable-release.deb

echo ""
echo "Step 2: Updating package lists..."
sudo apt-get update

echo ""
echo "Step 3: Installing Proton VPN CLI..."
sudo apt-get install -y protonvpn-cli

# Step 4: Verify installation
echo ""
echo "Step 4: Verifying installation..."
if ! command -v protonvpn &> /dev/null; then
    echo "❌ Installation failed - protonvpn command not found"
    exit 1
fi

echo "✅ Proton VPN CLI installed: $(protonvpn --version)"

# Step 5: Try to fix network/DNS issues
echo ""
echo "Step 5: Attempting to fix network connectivity..."
echo "   Testing DNS resolution..."

# Try alternative DNS if needed
if ! dig api.protonvpn.com +short | grep -q .; then
    echo "   ⚠️  api.protonvpn.com does not resolve"
    echo "   Trying alternative DNS servers..."
    
    # Try Cloudflare DNS
    if dig @1.1.1.1 api.protonvpn.com +short | grep -q .; then
        echo "   ✅ Resolves with Cloudflare DNS - configuring..."
        sudo resolvectl dns ens18 1.1.1.1 1.0.0.1
        sleep 2
    # Try Google DNS
    elif dig @8.8.8.8 api.protonvpn.com +short | grep -q .; then
        echo "   ✅ Resolves with Google DNS - configuring..."
        sudo resolvectl dns ens18 8.8.8.8 8.8.4.4
        sleep 2
    else
        echo "   ❌ Cannot resolve even with alternative DNS"
        echo "   This indicates network-level blocking"
        echo ""
        echo "   Network blocking detected. Options:"
        echo "   1. Check router settings for VPN blocking"
        echo "   2. Test from different network (mobile hotspot)"
        echo "   3. Contact ISP if they block VPN services"
        echo ""
        echo "   You can still try initialization - it may work:"
        echo "   sudo protonvpn init"
        exit 1
    fi
else
    echo "   ✅ DNS resolution working"
fi

# Step 6: Test API connectivity
echo ""
echo "Step 6: Testing API connectivity..."
if curl -s --connect-timeout 10 https://api.protonvpn.com/vpn/logicals > /dev/null 2>&1; then
    echo "   ✅ Can connect to Proton VPN API!"
    echo ""
    echo "Step 7: Initializing Proton VPN..."
    echo "   Run: sudo protonvpn init"
    echo "   (This will prompt for your Proton VPN credentials)"
    echo ""
    echo "=========================================="
    echo "Setup complete! Next steps:"
    echo "=========================================="
    echo "1. Initialize: sudo protonvpn init"
    echo "2. Login: sudo protonvpn login"
    echo "3. Connect: sudo protonvpn connect --fastest"
    echo ""
else
    echo "   ❌ Cannot connect to Proton VPN API"
    echo ""
    echo "   The network blocking issue persists."
    echo "   You may need to:"
    echo "   - Check router/ISP settings"
    echo "   - Use a different network"
    echo "   - Use manual OpenVPN configs (see PROTON_VPN_FIX.md)"
    echo ""
    echo "   However, you can still try:"
    echo "   sudo protonvpn init"
    echo "   (It may work despite the connectivity test failing)"
    exit 1
fi

