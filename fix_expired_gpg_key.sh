#!/bin/bash
# Fix expired Proton VPN GPG key
# The key expired on 2024-05-01, we need to download a fresh one

set -e

echo "=========================================="
echo "Fixing Expired Proton VPN GPG Key"
echo "=========================================="
echo ""

echo "Step 1: Downloading fresh GPG key from Proton VPN..."
# Download the public key
wget -qO /tmp/protonvpn-key.asc https://repo.protonvpn.com/debian/public_key.asc

if [ ! -f /tmp/protonvpn-key.asc ]; then
    echo "❌ Failed to download GPG key"
    exit 1
fi

echo "✅ Key downloaded"

echo ""
echo "Step 2: Importing GPG key to keyring..."
# Remove old expired keyring if it exists
sudo rm -f /usr/share/keyrings/protonvpn-stable-archive-keyring.gpg

# Import new key using modern method
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/protonvpn-stable-archive-keyring.gpg --import /tmp/protonvpn-key.asc

# Verify the key was imported
if [ -f /usr/share/keyrings/protonvpn-stable-archive-keyring.gpg ]; then
    echo "✅ GPG key imported successfully"
    
    # Check if key is valid (not expired)
    KEY_EXPIRY=$(gpg --no-default-keyring --keyring /usr/share/keyrings/protonvpn-stable-archive-keyring.gpg --list-keys 2>/dev/null | grep -i expire | head -1)
    echo "   Key info: $KEY_EXPIRY"
else
    echo "❌ Failed to import GPG key"
    exit 1
fi

echo ""
echo "Step 3: Verifying repository configuration..."
# Check if repository source file references the keyring correctly
if grep -q "signed-by=/usr/share/keyrings/protonvpn-stable-archive-keyring.gpg" /etc/apt/sources.list.d/protonvpn-stable.list; then
    echo "✅ Repository configuration is correct"
else
    echo "⚠️  Repository configuration may need updating"
    echo "   Current config:"
    cat /etc/apt/sources.list.d/protonvpn-stable.list
fi

echo ""
echo "Step 4: Updating package lists..."
sudo apt-get update

echo ""
echo "Step 5: Installing Proton VPN CLI..."
sudo apt-get install -y protonvpn-cli

echo ""
echo "Step 6: Verifying installation..."
if command -v protonvpn &> /dev/null; then
    echo "✅ Proton VPN CLI installed successfully!"
    protonvpn --version
    echo ""
    echo "Next steps:"
    echo "1. Fix DNS: sudo resolvectl dns ens18 1.1.1.1 1.0.0.1"
    echo "2. Initialize: sudo protonvpn init"
    echo "3. Login: sudo protonvpn login"
else
    echo "❌ Installation failed"
    exit 1
fi

# Cleanup
rm -f /tmp/protonvpn-key.asc

echo ""
echo "=========================================="
echo "GPG key fix complete!"
echo "=========================================="


