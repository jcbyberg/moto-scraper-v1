# Proton VPN Installation Fix

## Current Status
- ✅ Proton VPN CLI is installed (v2.2.11) at `/home/josh/.local/bin/protonvpn`
- ✅ OpenVPN is installed
- ❌ **CRITICAL**: Cannot reach Proton VPN API - DNS resolution fails and connections timeout
- ❌ Initialization incomplete - HTTP 422 error due to network blocking
- ⚠️ NetworkManager not found (may be required for some features)

## The Root Problem
**Network Blocking**: Your system cannot reach `api.protonvpn.com`:
- DNS resolution fails (domain doesn't resolve)
- Direct IP connections timeout after 2+ minutes
- This suggests network/router/ISP blocking of Proton VPN endpoints

The HTTP 422 error is a symptom - the CLI cannot connect to Proton VPN's API to download server configurations.

## Solutions

### Solution 1: Fix Network Blocking (Recommended First)

#### Check Firewall Rules
```bash
# Check if firewall is blocking outbound connections
sudo ufw status verbose
sudo iptables -L OUTPUT -n -v | head -20

# If firewall is active, allow outbound HTTPS
sudo ufw allow out 443/tcp
```

#### Check Router/Network Settings
- Access your router's admin panel (usually `192.168.0.1` or `192.168.1.1`)
- Check if VPN blocking is enabled
- Look for "VPN blocking", "Deep Packet Inspection", or "Content Filtering"
- Temporarily disable these features to test

#### Try Alternative DNS Servers
```bash
# Test with different DNS servers
dig @1.1.1.1 api.protonvpn.com
dig @8.8.8.8 api.protonvpn.com

# If those work, configure system to use them
sudo resolvectl dns ens18 1.1.1.1 8.8.8.8
```

#### Check ISP Blocking
Some ISPs block VPN services. Test from a different network (mobile hotspot, different location) to confirm.

### Solution 2: Manual Configuration (Workaround)

If you cannot reach the API, you can manually download OpenVPN configs:

1. **Download configs from another network**:
   - Visit https://account.protonvpn.com/downloads
   - Download OpenVPN configuration files
   - Transfer them to this server

2. **Manual setup**:
```bash
# Create OpenVPN config directory
sudo mkdir -p /etc/openvpn/client

# Copy downloaded .ovpn files to /etc/openvpn/client/
sudo cp ~/Downloads/*.ovpn /etc/openvpn/client/

# Create Proton VPN config directory
mkdir -p ~/.config/protonvpn

# You'll still need to configure authentication
```

### Solution 3: Use Official Proton VPN App

The official Proton VPN Linux app may work better than CLI:

```bash
# Download from Proton VPN website
# Visit: https://protonvpn.com/support/linux-vpn-setup/
# Or use the official repository method
```

### Solution 4: Run Initialization (After Network Fix)

Once network blocking is resolved, run:

```bash
sudo protonvpn init
```

This will:
- Download Proton VPN server configurations from API
- Set up OpenVPN config files in `/etc/openvpn/`
- Create configuration in `~/.config/protonvpn/`

### Step 2: Login to Your Account
After initialization, log in with your Proton VPN credentials:

```bash
sudo protonvpn login
```

You'll need:
- Your Proton VPN username (usually your Proton account email)
- Your Proton VPN password

### Step 3: Test Connection
Once logged in, test the connection:

```bash
# Check status
sudo protonvpn status

# Connect to fastest server
sudo protonvpn connect --fastest

# Or connect to a specific country
sudo protonvpn connect --cc US
```

## Alternative: Install NetworkManager (Optional)
If you encounter issues with network configuration, you may need NetworkManager:

```bash
sudo apt update
sudo apt install network-manager network-manager-openvpn
sudo systemctl enable NetworkManager
sudo systemctl start NetworkManager
```

## Common Issues

### Issue: "The program was not executed as root"
**Solution**: Always use `sudo` with protonvpn commands:
```bash
sudo protonvpn <command>
```

### Issue: HTTP 422 Error During Init
**Root Cause**: Cannot reach Proton VPN API (network blocking)
**Diagnosis**:
```bash
# Test DNS resolution
dig api.protonvpn.com
host api.protonvpn.com

# Test connectivity
curl -v https://api.protonvpn.com/vpn/logicals
ping -c 3 api.protonvpn.com
```

**Solutions**:
1. Check firewall: `sudo ufw status`
2. Check router VPN blocking settings
3. Try different DNS servers
4. Test from different network (mobile hotspot)
5. Use manual config download (see Solution 2 above)

### Issue: "There has been no profile initialized yet"
**Solution**: Run `sudo protonvpn init` first (after fixing network issues)

### Issue: DNS Resolution Fails
**Symptoms**: `Could not resolve host: api.protonvpn.com`
**Solutions**:
```bash
# Try different DNS servers
sudo resolvectl dns ens18 1.1.1.1 8.8.8.8

# Or edit /etc/resolv.conf (if not using systemd-resolved)
sudo nano /etc/resolv.conf
# Add: nameserver 1.1.1.1
#      nameserver 8.8.8.8
```

### Issue: Connection Timeout
**Symptoms**: Connection to Proton VPN API times out after 2+ minutes
**Possible causes**:
1. Firewall blocking outbound HTTPS (port 443)
2. Router blocking VPN services
3. ISP blocking Proton VPN IPs
4. Network routing issues

**Troubleshooting**:
```bash
# Check firewall
sudo ufw status verbose
sudo iptables -L OUTPUT -n -v

# Check routing
ip route show
traceroute api.protonvpn.com

# Test from different network
# (Use mobile hotspot or different location)
```

## Quick Reference Commands

```bash
# Initialize (one-time setup)
sudo protonvpn init

# Login
sudo protonvpn login

# Connect
sudo protonvpn connect --fastest
sudo protonvpn connect --cc US
sudo protonvpn connect --p2p  # For P2P servers
sudo protonvpn connect --tor  # For Tor servers

# Disconnect
sudo protonvpn disconnect

# Status
sudo protonvpn status

# Reconnect
sudo protonvpn reconnect

# Refresh server list
sudo protonvpn refresh
```

## For Your Motorcycle Scraper Project
Once Proton VPN is working, you can use it to avoid IP blocks when crawling:

```bash
# Connect before running crawler
sudo protonvpn connect --fastest

# Run your crawler
python scripts/full_site_crawler.py https://example-oem.com

# Disconnect when done
sudo protonvpn disconnect
```

## Next Steps (In Order)

1. **Diagnose Network Blocking**:
   ```bash
   # Test DNS
   dig api.protonvpn.com
   
   # Test connectivity
   curl -v https://api.protonvpn.com/vpn/logicals
   ```

2. **Fix Network Issues**:
   - Check firewall: `sudo ufw status`
   - Check router settings for VPN blocking
   - Try alternative DNS servers
   - Test from different network if possible

3. **After Network is Fixed**:
   ```bash
   sudo protonvpn init
   sudo protonvpn login
   sudo protonvpn connect --fastest
   ```

4. **If Network Cannot Be Fixed**:
   - Use manual OpenVPN config download (Solution 2)
   - Or use official Proton VPN app instead of CLI
   - Or use a different VPN service that isn't blocked

## Current Diagnosis Results
- ❌ `api.protonvpn.com` DNS resolution: **FAILED**
- ❌ Direct IP connection (185.159.157.10:443): **TIMEOUT** (2+ minutes)
- ✅ General internet connectivity: **WORKING** (google.com resolves and connects)
- ✅ DNS service: **WORKING** (using 8.8.8.8, 8.8.4.4)

**Conclusion**: Network/router/ISP is likely blocking Proton VPN API endpoints. Fix network blocking first before attempting initialization.

