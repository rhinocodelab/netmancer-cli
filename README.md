# Netmancer for CloudX OS

Netmancer is a command-line tool for managing network interfaces on CloudX OS. It provides a simple and intuitive way to configure network settings using INI configuration files and generates Netplan YAML configurations.



## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/netmancer.git
cd netmancer

# Install the package
pip install -e .
```

## Commands

### List Network Interfaces

Lists all available network interfaces on the system.

```bash
netmancer list-network-interfaces
```

Example output:
```json
[
  {
    "name": "enp3s0",
    "type": "ethernet",
    "state": "connected",
    "ip": "10.10.10.2",
    "subnet": "255.255.255.0",
    "gateway": "10.10.10.1"
  },
  {
    "name": "wlan0",
    "type": "wifi",
    "state": "disconnected",
    "ip": "",
    "subnet": "",
    "gateway": ""
  }
]
```

### Show Interface Information

Displays detailed information about a specific network interface.

```bash
netmancer show-info <interface>
```

Example:
```bash
netmancer show-info enp3s0
```

Example output:
```json
{
  "name": "enp3s0",
  "type": "ethernet",
  "state": "connected",
  "ip": "10.10.10.2",
  "subnet": "255.255.255.0",
  "gateway": "10.10.10.1",
  "dns": ["10.10.10.1", "8.8.8.8"],
  "mac": "00:11:22:33:44:55",
  "speed": "1000 Mb/s"
}
```

### Show DHCP Information

Displays DHCP information for a specific network interface.

```bash
netmancer dhcp-info <interface>
```

Example:
```bash
netmancer dhcp-info enp3s0
```

Example output:
```json
{
  "dhcp4": true,
  "dhcp6": true,
  "ip": "10.10.10.2",
  "subnet": "255.255.255.0",
  "gateway": "10.10.10.1",
  "dns": ["10.10.10.1", "8.8.8.8"],
  "lease_time": "86400",
  "expiry": "2023-04-20 12:34:56"
}
```

### Show Interface Status

Displays the current status of a network interface.

```bash
netmancer interface-status <interface>
```

Example:
```bash
netmancer interface-status enp3s0
```

Example output:
```json
{
  "name": "enp3s0",
  "type": "ethernet",
  "state": "connected",
  "ip": "10.10.10.2",
  "subnet": "255.255.255.0",
  "gateway": "10.10.10.1",
  "dns": ["10.10.10.1", "8.8.8.8"],
  "mac": "00:11:22:33:44:55",
  "speed": "1000 Mb/s",
  "dhcp4": true,
  "dhcp6": true
}
```

### Apply Network Configuration

Applies network settings from an INI configuration file.

```bash
netmancer network-apply <ini_file> [--output OUTPUT] [--apply]
```

Options:
- `--output, -o`: Save Netplan YAML to a file (default: `/etc/netplan/99-netmancer-<interface>.yaml` for ethernet or `/etc/netplan/100-netmancer-<interface>.yaml` for wireless)
- `--apply, -a`: Apply the configuration immediately

Example:
```bash
netmancer network-apply config.ini --output /etc/netplan/99-netmancer-enp3s0.yaml --apply
```

## INI Configuration Format

### Ethernet Configuration (DHCP)

```ini
[general]
interface=enp3s0
dhcp=true
```

### Ethernet Configuration (Static IP)

```ini
[general]
interface=enp3s0
dhcp=false

[address]
ip=10.10.10.2
subnet=255.255.255.0
gateway=10.10.10.1
dns=10.10.10.1,8.8.8.8
```

### Wireless Configuration (DHCP)

```ini
[general]
interface=wlan0
dhcp=true

[wifi]
ssid=MyWiFi
password=MyPassword
```

### Wireless Configuration (Static IP)

```ini
[general]
interface=wlan0
dhcp=false

[address]
ip=192.168.1.100
subnet=255.255.255.0
gateway=192.168.1.1
dns=192.168.1.1,8.8.8.8

[wifi]
ssid=MyWiFi
password=MyPassword
```

## Notes

- For wireless interfaces, the `[wifi]` section with SSID and password is mandatory.
- When DHCP is set to false, the `[address]` section with IP, subnet, and gateway is mandatory.
- Subnet can be specified in either CIDR notation (e.g., "24") or subnet mask format (e.g., "255.255.255.0").
- The generated Netplan YAML files follow the naming convention:
  - Ethernet: `/etc/netplan/99-netmancer-<interface>.yaml`
  - Wireless: `/etc/netplan/100-netmancer-<interface>.yaml`

## Logging

Netmancer logs all command executions to `log/netmancer.log`. Each log entry includes:
- Timestamp
- Command name
- Message

Example log entries:
```
2023-04-19 23:54:06 list-network-interfaces Executing command
2023-04-19 23:54:58 list-network-interfaces Output saved to interfaces.json
```

## CloudX OS Integration

Netmancer is designed to work seamlessly with CloudX OS's network management system. It integrates with the following CloudX OS components:

- **Netplan**: Generates Netplan YAML configurations that are compatible with CloudX OS
- **NetworkManager**: Uses NetworkManager for interface detection and status information
- **System Logging**: Integrates with CloudX OS's logging system

## License

This project is licensed under the MIT License - see the LICENSE file for details. 