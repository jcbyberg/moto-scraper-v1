# Proton VPN Setup Instructions

## Current Status
- ✅ Old installations removed (pipx and pip)
- ❌ **Network blocking detected**: `api.protonvpn.com` does not resolve via DNS
- ⚠️ Proton VPN CLI not yet installed via apt

## The Network Blocking Issue

**Problem**: `api.protonvpn.com` cannot be resolved, even with alternative DNS servers (1.1.1.1, 8.8.8.8). This suggests:
- Router-level VPN blocking
- ISP-level blocking
- Network firewall blocking

## Step-by-Step Setup

### Step 1: Install Proton VPN CLI (if not already done)

Run the installation script:
```bash
./install_protonvpn.sh
```

Or manually:
```bash
# Repository package should already be in /tmp/
sudo dpkg -i /tmp/protonvpn-stable-release.deb
sudo apt-get update
sudo apt-get install -y protonvpn-cli
```

### Step 2: Attempt Network Fix

Try these commands in order:

**Option A: Configure Alternative DNS**
```bash
# Try Cloudflare DNS
sudo resolvectl dns ens18 1.1.1.1 1.0.0.1
sleep 2
dig api.protonvpn.com +short

# If that doesn't work, try Google DNS
sudo resolvectl dns ens18 8.8.8.8 8.8.4.4
sleep 2
dig api.protonvpn.com +short
```

**Option B: Check Firewall**
```bash
# Check if firewall is blocking
sudo ufw status verbose

# If firewall is active, allow HTTPS outbound
sudo ufw allow out 443/tcp
```

**Option C: Test from Different Network**
- Connect via mobile hotspot
- Test if `api.protonvpn.com` resolves
- If it works, the issue is your router/ISP

### Step 3: Initialize Proton VPN

**Even if DNS doesn't resolve, try initialization** - it may work:

```bash
sudo protonvpn init
```

This will:
1. Prompt for your Proton VPN username (usually your Proton account email)
2. Prompt for your Proton VPN password
3. Ask for default protocol (TCP or UDP)
4. Attempt to download server configurations

**If initialization fails with HTTP 422 or connection error:**
- The network blocking is preventing API access
- See "Workarounds" section below

### Step 4: Login (After Successful Init)

```bash
sudo protonvpn login
```

### Step 5: Test Connection

```bash
# Check status
sudo protonvpn status

# Connect to fastest server
sudo protonvpn connect --fastest

# Or connect to specific country
sudo protonvpn connect --cc US
```

## Workarounds if Network Blocking Persists

### Workaround 1: Manual OpenVPN Config Download

1. **From a different network** (mobile hotspot, different location):
   - Visit: https://account.protonvpn.com/downloads
   - Download OpenVPN configuration files (.ovpn)
   - Transfer to this server

2. **Manual setup**:
```bash
# Create directories
sudo mkdir -p /etc/openvpn/client
mkdir -p ~/.config/protonvpn

# Copy .ovpn files
sudo cp ~/Downloads/*.ovpn /etc/openvpn/client/

# You'll still need to configure authentication
# This is more complex - see Proton VPN documentation
```

### Workaround 2: Use Official Proton VPN App

The official GUI app may work better:
```bash
# After installing repository (Step 1)
sudo apt-get install -y proton-vpn-gnome-desktop
```

### Workaround 3: Router Configuration

If you have access to your router:
1. Access router admin (usually `192.168.0.1` or `192.168.1.1`)
2. Look for:
   - "VPN blocking" or "VPN passthrough"
   - "Deep Packet Inspection (DPI)"
   - "Content Filtering"
3. Disable VPN blocking temporarily to test
4. Whitelist `api.protonvpn.com` and `*.protonvpn.com` domains

## Quick Reference

```bash
# Installation
./install_protonvpn.sh

# Network fix attempt
sudo resolvectl dns ens18 1.1.1.1 1.0.0.1

# Initialize
sudo protonvpn init

# Login
sudo protonvpn login

# Connect
sudo protonvpn connect --fastest

# Status
sudo protonvpn status

# Disconnect
sudo protonvpn disconnect
```

## Diagnosis Commands

```bash
# Test DNS resolution
dig api.protonvpn.com
dig @1.1.1.1 api.protonvpn.com
dig @8.8.8.8 api.protonvpn.com

# Test connectivity
curl -v https://api.protonvpn.com/vpn/logicals

# Check current DNS
resolvectl status

# Check firewall
sudo ufw status verbose
sudo iptables -L OUTPUT -n -v | head -20
```

## Expected Behavior

**If network blocking is fixed:**
- `dig api.protonvpn.com` returns an IP address
- `curl https://api.protonvpn.com/vpn/logicals` returns JSON data
- `sudo protonvpn init` completes successfully

**If network blocking persists:**
- DNS queries return empty
- curl times out or fails
- `sudo protonvpn init` may fail with HTTP 422 or connection error
- You'll need to use workarounds or fix router/ISP blocking

## Next Steps

1. **First**: Run `./install_protonvpn.sh` to install Proton VPN CLI
2. **Second**: Try DNS fix commands above
3. **Third**: Run `sudo protonvpn init` and see if it works
4. **If it fails**: Use workarounds or contact your ISP/router admin

## Files Created

- `install_protonvpn.sh` - Installation script
- `setup_protonvpn_complete.sh` - Complete setup (install + network fix)
- `fix_protonvpn_network.sh` - Network fix only
- `PROTON_VPN_FIX.md` - Detailed troubleshooting guide
- `PROTON_VPN_SETUP_INSTRUCTIONS.md` - This file

