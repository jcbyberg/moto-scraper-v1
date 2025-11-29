#!/bin/bash
# Fix D-Bus session bus issue with Proton VPN CLI

echo "=========================================="
echo "Proton VPN D-Bus Fix"
echo "=========================================="
echo ""

echo "Important: Proton VPN CLI v3.13.0 does NOT require sudo for most operations!"
echo ""
echo "The error occurs because sudo doesn't preserve D-Bus session bus environment."
echo ""
echo "Solution: Run Proton VPN CLI WITHOUT sudo"
echo ""

# Check if user is in the right groups
if groups | grep -q "netdev\|network"; then
    echo "✅ User has network permissions"
else
    echo "⚠️  User may need network permissions"
    echo "   (This is usually not required for Proton VPN CLI)"
fi

echo ""
echo "=========================================="
echo "Correct Usage:"
echo "=========================================="
echo ""
echo "❌ WRONG: sudo protonvpn-cli connect --fastest"
echo "✅ CORRECT: protonvpn-cli connect --fastest"
echo ""
echo "Commands that work WITHOUT sudo:"
echo "  protonvpn-cli login"
echo "  protonvpn-cli connect --fastest"
echo "  protonvpn-cli status"
echo "  protonvpn-cli disconnect"
echo ""
echo "If you MUST use sudo (not recommended), export D-Bus:"
echo "  export DBUS_SESSION_BUS_ADDRESS=\"unix:path=/run/user/\$(id -u)/bus\""
echo "  sudo -E protonvpn-cli connect --fastest"
echo ""

