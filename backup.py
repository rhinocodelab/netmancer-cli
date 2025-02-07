# src/netmancer/commands/ethernet.py

import configparser
import subprocess
import yaml
import json
from pathlib import Path
from datetime import datetime

CONFIG_DIR = Path("/etc/netplan")
DHCP_CONFIG_PATH = CONFIG_DIR / "99-netmancer-dhcp.yaml"
STATIC_CONFIG_PATH = CONFIG_DIR / "99-netmancer-static.yaml"

# Pass argument ethernet dhcp or static
def configure_parser(subparsers):
    parser = subparsers.add_parser('ethernet', help='Configure Ethernet interface')
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
    if not args.dhcp and not args.static:
        print("Error: Please specify either --dhcp or --static")
    if args.dhcp and args.static:
        print("Error: Please specify only one of --dhcp or --static")
    if args.dhcp:
        configure_dhcp()
    elif args.static:
        print("Configuring static IP...")

def configure_dhcp():
    try:
        # Remove all the files in the CONFIG_DIR directory
        for file in CONFIG_DIR.glob('*'):
            file.unlink()
        
        # Create a new DHCP_CONFIG_PATH file
        DHCP_CONFIG_PATH.touch()
        
        # Get the list of Ethernet interfaces
        ethernet_interfaces = get_ethernet_interfaces()
        if not ethernet_interfaces:
            return {
                "error" : "No Ethernet interfaces found.",
                "details": "No Ethernet interfaces found."
            }
        # Initialize the DHCP configuration dictionary
        dhcp_config = {
            'network': {
                'version': 2,
                'renderer': 'NetworkManager',
                'ethernets': {}
            }
        }
        # Add each Ethernet interface to the configuration
        for interface in ethernet_interfaces:
            dhcp_config['network']['ethernets'][interface] = {
                'dhcp4': True,
                'optional': True
            }
        # Create the YAML file with the configuration
        try:
            with open(DHCP_CONFIG_PATH, 'w') as f:
                yaml.dump(dhcp_config, f, default_flow_style=False)
        
        # Apply the DHCP configuration using netplan
            try:
                apply_dhcp_config(DHCP_CONFIG_PATH)
                return {
                    "success" : "DHCP configuration applied successfully.",
                    "details": "DHCP configuration applied successfully."
                }
            except Exception as e:
                return {
                    "error" : "Error applying DHCP configuration.",
                    "details": str(e)
                }
        except Exception as e:
            return {
                "error" : "Error creating DHCP configuration file.",
                "details": str(e)
            }
    except Exception as e:
        return {
            "error" : "Error removing existing DHCP configuration.",
            "details": str(e)
        }

def get_ethernet_interfaces():
    """
    Returns a list of all Ethernet interface names using nmcli.
    """
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

        return ethernet_interfaces
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get Ethernet interfaces - {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def apply_dhcp_config(config_path):
    """
    Applies the DHCP configuration from the specified file.
    """
    try:
        # Apply the DHCP configuration using netplan
        subprocess.run(['netplan', 'apply', '--config', config_path], check=True)
        print(f"DHCP configuration applied successfully from {config_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to apply DHCP configuration - {e}")
        return {
            "error" : "Error applying DHCP configuration.",
            "details": str(e)
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "error" : "Unexpected error applying DHCP configuration.",
            "details": str(e)
        }