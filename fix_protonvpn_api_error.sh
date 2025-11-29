#!/bin/bash
# Fix "Unknown API error" - Network blocking issue

echo "=========================================="
echo "Fixing Proton VPN API Connection Error"
echo "=========================================="
echo ""

echo "Problem: Cannot reach api.protonvpn.com (network blocking)"
echo ""

# Test current DNS resolution
echo "Step 1: Testing DNS resolution..."
if dig api.protonvpn.com +short | grep -q .; then
    echo "✅ api.protonvpn.com resolves"
    exit 0
else
    echo "❌ api.protonvpn.com does NOT resolve"
fi

echo ""
echo "Step 2: Trying alternative DNS servers..."
# Try Cloudflare DNS
if dig @1.1.1.1 api.protonvpn.com +short | grep -q .; then
    echo "✅ Resolves with Cloudflare DNS (1.1.1.1)"
    echo "   Configuring system DNS..."
    sudo resolvectl dns ens18 1.1.1.1 1.0.0.1
    sleep 2
    echo "   Testing again..."
    if dig api.protonvpn.com +short | grep -q .; then
        echo "✅ DNS fixed! Try login again:"
        echo "   protonvpn-cli login Jcbyberg"
        exit 0
    fi
# Try Google DNS
elif dig @8.8.8.8 api.protonvpn.com +short | grep -q .; then
    echo "✅ Resolves with Google DNS (8.8.8.8)"
    echo "   Configuring system DNS..."
    sudo resolvectl dns ens18 8.8.8.8 8.8.4.4
    sleep 2
    echo "   Testing again..."
    if dig api.protonvpn.com +short | grep -q .; then
        echo "✅ DNS fixed! Try login again:"
        echo "   protonvpn-cli login Jcbyberg"
        exit 0
    fi
else
    echo "❌ Does not resolve even with alternative DNS"
fi

echo ""
echo "Step 3: Testing API connectivity..."
if curl -s --connect-timeout 5 https://api.protonvpn.com > /dev/null 2>&1; then
    echo "✅ Can connect to API!"
    echo "   Try login again: protonvpn-cli login Jcbyberg"
    exit 0
else
    echo "❌ Cannot connect to API"
fi

echo ""
echo "=========================================="
echo "Network Blocking Detected"
echo "=========================================="
echo ""
echo "The network/router/ISP is blocking Proton VPN API endpoints."
echo ""
echo "Solutions:"
echo ""
echo "1. Check Router Settings:"
echo "   - Access router admin (usually 192.168.0.1)"
echo "   - Disable 'VPN blocking' or 'Deep Packet Inspection'"
echo "   - Whitelist *.protonvpn.com and *.proton.me domains"
echo ""
echo "2. Test from Different Network:"
echo "   - Use mobile hotspot"
echo "   - If it works there, the issue is your router/ISP"
echo ""
echo "3. Contact ISP:"
echo "   - Some ISPs block VPN services"
echo "   - Ask them to unblock Proton VPN"
echo ""
echo "4. Use Manual OpenVPN Configs:"
echo "   - Download from: https://account.protonvpn.com/downloads"
echo "   - Use from a network that isn't blocked"
echo "   - Import manually (more complex)"
echo ""
echo "5. Try Again Later:"
echo "   - Sometimes temporary network issues resolve"
echo "   - Or try: protonvpn-cli login Jcbyberg"
echo ""

