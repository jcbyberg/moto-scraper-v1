#!/bin/bash
# Script to fix Proton VPN network blocking issues
# This attempts multiple workarounds for DNS/network blocking

set -e

echo "=========================================="
echo "Proton VPN Network Blocking Fix"
echo "=========================================="
echo ""

# Check if protonvpn is installed
if ! command -v protonvpn &> /dev/null; then
    echo "❌ Proton VPN CLI is not installed."
    echo "   Please run ./install_protonvpn.sh first"
    exit 1
fi

echo "Step 1: Checking current DNS resolution..."
if dig api.protonvpn.com +short | grep -q .; then
    echo "✅ api.protonvpn.com resolves correctly"
    exit 0
else
    echo "❌ api.protonvpn.com does not resolve"
fi

echo ""
echo "Step 2: Testing alternative DNS servers..."
if dig @1.1.1.1 api.protonvpn.com +short | grep -q .; then
    echo "✅ Resolves with Cloudflare DNS (1.1.1.1)"
    echo "   Configuring system to use Cloudflare DNS..."
    sudo resolvectl dns ens18 1.1.1.1 1.0.0.1
    echo "   Waiting 2 seconds for DNS to update..."
    sleep 2
elif dig @8.8.8.8 api.protonvpn.com +short | grep -q .; then
    echo "✅ Resolves with Google DNS (8.8.8.8)"
    echo "   Configuring system to use Google DNS..."
    sudo resolvectl dns ens18 8.8.8.8 8.8.4.4
    echo "   Waiting 2 seconds for DNS to update..."
    sleep 2
else
    echo "❌ Does not resolve with alternative DNS servers"
    echo "   This suggests network-level blocking"
fi

echo ""
echo "Step 3: Checking firewall status..."
if command -v ufw &> /dev/null; then
    FIREWALL_STATUS=$(sudo ufw status | head -1)
    echo "   Firewall: $FIREWALL_STATUS"
    if echo "$FIREWALL_STATUS" | grep -qi "active"; then
        echo "   ⚠️  Firewall is active - ensuring HTTPS outbound is allowed..."
        sudo ufw allow out 443/tcp 2>/dev/null || true
    fi
fi

echo ""
echo "Step 4: Testing connectivity..."
if curl -s --connect-timeout 5 https://api.protonvpn.com/vpn/logicals > /dev/null 2>&1; then
    echo "✅ Can connect to Proton VPN API!"
    echo ""
    echo "You can now run: sudo protonvpn init"
    exit 0
else
    echo "❌ Still cannot connect to Proton VPN API"
    echo ""
    echo "Possible causes:"
    echo "  1. Router/ISP is blocking Proton VPN domains"
    echo "  2. Network-level firewall blocking"
    echo "  3. DNS filtering at network level"
    echo ""
    echo "Solutions:"
    echo "  1. Check router settings for VPN blocking"
    echo "  2. Test from a different network (mobile hotspot)"
    echo "  3. Contact your ISP if they block VPN services"
    echo "  4. Use manual OpenVPN config download (see PROTON_VPN_FIX.md)"
    exit 1
fi

