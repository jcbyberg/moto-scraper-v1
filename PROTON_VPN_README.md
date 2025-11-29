# Proton VPN Installation Scripts

This directory contains scripts and documentation for installing and troubleshooting Proton VPN CLI on Linux systems.

## Quick Start

### Installation
```bash
./install_protonvpn_now.sh
```

This script will:
1. Fix expired GPG keys
2. Install Proton VPN CLI via apt repository
3. Verify installation

### Usage (No sudo needed!)
```bash
# Login
protonvpn-cli login your_username

# Connect
protonvpn-cli connect --fastest

# Status
protonvpn-cli status

# Disconnect
protonvpn-cli disconnect
```

## Files

### Installation Scripts
- `install_protonvpn.sh` - Main installation script with GPG key handling
- `install_protonvpn_now.sh` - Quick install (fixes expired keys automatically)
- `setup_protonvpn_complete.sh` - Complete setup with network diagnostics

### Fix Scripts
- `fix_protonvpn_dbus.sh` - Fixes D-Bus session bus errors
- `fix_protonvpn_api_error.sh` - Diagnoses and fixes API connection errors
- `fix_protonvpn_network.sh` - Network blocking diagnostics
- `fix_expired_gpg_key.sh` - Fixes expired GPG key issues

### Documentation
- `PROTON_VPN_STATUS.md` - Current status and quick reference
- `PROTON_VPN_FIX.md` - Comprehensive troubleshooting guide
- `PROTON_VPN_SETUP_INSTRUCTIONS.md` - Step-by-step setup instructions

## Common Issues

### 1. Expired GPG Key
**Error**: `NO_PUBKEY EDA3E22630349F1C` or `repository is not signed`

**Fix**: Run `./install_protonvpn_now.sh` or `./fix_expired_gpg_key.sh`

### 2. D-Bus Error
**Error**: `Environment variable DBUS_SESSION_BUS_ADDRESS is unset`

**Fix**: Don't use `sudo` - Proton VPN CLI v3.13.0 doesn't need it!

### 3. Unknown API Error
**Error**: `Unknown API error. Please retry or contact support.`

**Fix**: Network blocking - see `PROTON_VPN_FIX.md` for solutions

### 4. Network Blocking
**Symptom**: Cannot resolve `api.protonvpn.com`

**Solutions**:
1. Fix router settings (disable VPN blocking)
2. Test from different network
3. Try DNS fix: `sudo resolvectl dns ens18 1.1.1.1 1.0.0.1`

## Requirements

- Ubuntu/Debian-based Linux
- NetworkManager (usually pre-installed)
- OpenVPN (installed automatically)
- Internet connection (to reach Proton VPN API)

## License

These scripts are provided as-is for convenience. Proton VPN CLI is subject to Proton VPN's terms of service.

## Support

For Proton VPN issues:
- Official support: https://protonvpn.com/support
- CLI documentation: https://protonvpn.com/support/linux-cli/

