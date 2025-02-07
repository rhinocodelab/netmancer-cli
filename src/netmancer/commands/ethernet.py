# src/netmancer/commands/ethernet.py

import sqlite3
import subprocess
import yaml
import json
import time
from pathlib import Path


CONFIG_DIR = Path("/etc/netplan")
DHCP_CONFIG_PATH = CONFIG_DIR / "99-netmancer-dhcp.yaml"
STATIC_CONFIG_PATH = CONFIG_DIR / "99-netmancer-static.yaml"
SYSCONF_DB = '/data/sysconf.db'

# Pass argument ethernet dhcp or static with interface
def configure_parser(subparsers):
    parser = subparsers.add_parser('ethernet', help='Configure Ethernet interface')
    parser.add_argument(
        '--interface', '-i',
        required=True,
        help='Ethernet interface name (e.g., eth0)'
    )
    parser.add_argument(
        '--dhcp', '-d',
        action='store_true',
        help='Configure DHCP'
    )
    parser.add_argument(
        '--static', '-s',
        action='store_true',
        help='Configure static IP'
    )
    parser.set_defaults(func=handle_ethernet)

def handle_ethernet(args):
    # Check if all the required arguments are provided
    if not (args.dhcp or args.static):
        print("Error: Please specify either --dhcp or --static.")
        return
    
    # Check if the interface exists
    if not check_interface_exists(args.interface):
        print(f"Error: Interface {args.interface} does not exist.")
        return
    
    # Check if IPv4 Address is already configured for the interface
    CHECK_IPV4_CONFIG = check_ipv4_configured(args.interface)
    if CHECK_IPV4_CONFIG:
        print(f"INFO: IPv4 Address is already configured for interface {args.interface}.")
        # Check if it matches with the SYSCONF_DB (sqlite3)
        if not check_ipv4_in_sysconf_db(CHECK_IPV4_CONFIG['ip_address']):
            print(f"INFO: IPv4 Address in SYSCONF_DB does not match with the interface {args.interface}.")
            if not update_sysconf_db(CHECK_IPV4_CONFIG):
                print(f"Error: Failed to update SYSCONF_DB.")
                return
    else:
        pass

def check_interface_exists(interface):
    try:
        # Get device status from nmcli
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE', 'device'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Parse the output to find all ethernet devices
        ethernet_interfaces = []
        for line in result.stdout.strip().split('\n'):
            device, iface_type, state = line.split(':')
            if iface_type == 'ethernet' and state == 'connected':
                ethernet_interfaces.append(device)

        return interface in ethernet_interfaces
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get Ethernet interfaces - {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def check_ipv4_configured(interface, timeout=15):
    """Wait for the interface to obtain full IP configuration"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = subprocess.run(
                ['nmcli', '-t','-f', 'IP4.ADDRESS,IP4.GATEWAY,IP4.DNS', 'device', 'show', interface],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
                )
        output = result.stdout.strip()
        if output:
            ip_details = parse_dhcp_network_details(output)
            if ip_details:
                return ip_details
        time.sleep(1)
    return None

def parse_dhcp_network_details(output):
    details = {}
    for line in output.splitlines():
        if 'IP4.ADDRESS' in line:
            details['ip_address'] = line.split(':')[1].split('/')[0]
            details['cidr'] = line.split(':')[1].split('/')[1]
            details['netmask'] = cidr_to_netmask(int(details['cidr']))
        elif 'IP4.GATEWAY' in line:
            details['gateway'] = line.split(':')[1]
        elif 'IP4.DNS' in line:
            details.setdefault('dns', []).append(line.split(':')[1])
    return details

def cidr_to_netmask(cidr):
    """
    Convert CIDR notation to a netmask.
    """
    bits = (0xFFFFFFFF >> (32 - cidr)) << (32 - cidr)
    return f"{(bits >> 24) & 0xFF}.{(bits >> 16) & 0xFF}.{(bits >> 8) & 0xFF}.{bits & 0xFF}"

def check_ipv4_in_sysconf_db(ip_address):
    """
        Check if the 'ip_address' matches with the SYSCONF_DB (sqlite3)
    """
    try:
        conn = sqlite3.connect(SYSCONF_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT IP FROM NetworkDetails WHERE NetworkType='Ethernet:eth0'")
        result = cursor.fetchone()
        if result:
            stored_ip = result[0]
            if stored_ip == ip_address:
                conn.close()
                return True
        conn.close()
        return False
    except sqlite3.Error as e:
        print(f"Error: {e}")
        return False

def update_sysconf_db(ip_config: json):
    """
        Update the SYSCONF_DB (sqlite3) with the new IP configuration.
        SET: IP, Subnetmask, Gateway, PrimaryDNS and SecondaryDNS
    """
    try:
        conn = sqlite3.connect(SYSCONF_DB)
        cursor = conn.cursor()
        cursor.execute("UPDATE NetworkDetails SET IP=?, SubnetMask=?, Gateway=?, PrimaryDNS=?, WHERE NetworkType='Ethernet:eth0'",
                       (ip_config['ip_address'], ip_config['netmask'], ip_config['gateway'], ip_config['dns'][0]))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error: {e}")
        return False