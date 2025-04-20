"""Apply network settings"""

import click
import subprocess
import json
import os
import configparser
import yaml
from netmancer_cli.utils.logger import log_command
from netmancer_cli.utils.cidr_converter import CIDRConverter

def read_ini_file(ini_path):
    """
    Read and parse the INI configuration file.
    
    Args:
        ini_path (str): Path to the INI file
        
    Returns:
        dict: Parsed configuration data
    """
    if not os.path.exists(ini_path):
        raise FileNotFoundError(f"Configuration file not found: {ini_path}")
    
    config = configparser.ConfigParser()
    config.read(ini_path)
    
    # Initialize network configuration
    network_config = {
        'ethernets': {},
        'wifis': {}
    }
    
    # Check if general section exists
    if 'general' not in config:
        raise ValueError("Missing [general] section in configuration file")
    
    # Get interface name and type
    interface = config['general'].get('interface', '')
    if not interface:
        raise ValueError("Interface name not specified in [general] section")
    
    # Determine interface type
    if interface.startswith(('en', 'eth')):
        interface_type = 'ethernet'
        target_dict = network_config['ethernets']
    elif interface.startswith(('wl', 'wlan')):
        interface_type = 'wifi'
        target_dict = network_config['wifis']
    else:
        interface_type = 'ethernet'  # Default
        target_dict = network_config['ethernets']
    
    # Initialize interface configuration
    interface_config = {}
    target_dict[interface] = interface_config
    
    # Process general section
    dhcp = config['general'].get('dhcp', 'true').lower()
    if dhcp in ('true', 'yes', '1'):
        interface_config['dhcp4'] = True
        interface_config['dhcp6'] = True
        
        # Process address section if it exists and DHCP is enabled (optional)
        if 'address' in config:
            address_config = config['address']
            
            # Handle IP address and subnet
            ip = address_config.get('ip', '')
            subnet = address_config.get('subnet', '')
            if ip and subnet:
                # Use CIDRConverter to convert subnet mask to CIDR
                try:
                    # First try to parse as CIDR if it's already in CIDR format
                    cidr = int(subnet)
                    if cidr < 0 or cidr > 32:
                        raise ValueError("CIDR must be between 0 and 32")
                except ValueError:
                    # If not a valid CIDR, assume it's a subnet mask and convert
                    try:
                        cidr_converter = CIDRConverter()
                        cidr = cidr_converter.subnet_to_cidr(subnet)
                    except ValueError as e:
                        raise ValueError(f"Invalid subnet mask format: {subnet}")
                
                interface_config['addresses'] = [f"{ip}/{cidr}"]
            
            # Handle gateway
            gateway = address_config.get('gateway', '')
            if gateway:
                # Use the routes format as shown in the example
                interface_config['routes'] = [
                    {
                        'to': 'default',
                        'via': gateway
                    }
                ]
            
            # Handle DNS servers
            dns = address_config.get('dns', '')
            if dns:
                dns_servers = [ns.strip() for ns in dns.split(',')]
                interface_config['nameservers'] = {'addresses': dns_servers}
    else:
        interface_config['dhcp4'] = False
        interface_config['dhcp6'] = False
        
        # If DHCP is disabled, address section is mandatory
        if 'address' not in config:
            raise ValueError("Missing [address] section for static IP configuration")
        
        address_config = config['address']
        
        # IP address is mandatory for static configuration
        ip = address_config.get('ip', '')
        if not ip:
            raise ValueError("IP address is required in [address] section for static configuration")
        
        # Subnet is mandatory for static configuration
        subnet = address_config.get('subnet', '')
        if not subnet:
            raise ValueError("Subnet is required in [address] section for static configuration")
        
        # Use CIDRConverter to convert subnet mask to CIDR
        try:
            # First try to parse as CIDR if it's already in CIDR format
            cidr = int(subnet)
            if cidr < 0 or cidr > 32:
                raise ValueError("CIDR must be between 0 and 32")
        except ValueError:
            # If not a valid CIDR, assume it's a subnet mask and convert
            try:
                cidr_converter = CIDRConverter()
                cidr = cidr_converter.subnet_to_cidr(subnet)
            except ValueError as e:
                raise ValueError(f"Invalid subnet mask format: {subnet}")
        
        interface_config['addresses'] = [f"{ip}/{cidr}"]
        
        # Gateway is mandatory for static configuration
        gateway = address_config.get('gateway', '')
        if not gateway:
            raise ValueError("Gateway is required in [address] section for static configuration")
        
        # Use the routes format as shown in the example
        interface_config['routes'] = [
            {
                'to': 'default',
                'via': gateway
            }
        ]
        
        # Handle DNS servers
        dns = address_config.get('dns', '')
        if dns:
            dns_servers = [ns.strip() for ns in dns.split(',')]
            interface_config['nameservers'] = {'addresses': dns_servers}
    
    # Process wifi section if it exists
    if interface_type == 'wifi':
        # For wireless interfaces, wifi section is mandatory
        if 'wifi' not in config:
            raise ValueError("Missing [wifi] section for wireless interface configuration")
        
        wifi_config = config['wifi']
        
        # SSID is mandatory for wireless
        ssid = wifi_config.get('ssid', '')
        if not ssid:
            raise ValueError("SSID is required in [wifi] section for wireless interface")
        
        # Password is mandatory for wireless
        password = wifi_config.get('password', '')
        if not password:
            raise ValueError("Password is required in [wifi] section for wireless interface")
        
        # Configure the wireless access point
        interface_config['access-points'] = {ssid: {'password': password}}
    
    return network_config, interface, interface_type

def generate_netplan_yaml(network_config, output_path=None, interface=None, interface_type=None):
    """
    Generate Netplan YAML configuration from the network configuration.
    
    Args:
        network_config (dict): Network configuration data
        output_path (str, optional): Path to save the YAML file
        interface (str, optional): Interface name
        interface_type (str, optional): Interface type (ethernet or wifi)
        
    Returns:
        str: Generated YAML content
    """
    # Create Netplan structure
    netplan_config = {
        'network': {
            'version': 2,
            'renderer': 'networkd',
            'ethernets': network_config.get('ethernets', {}),
            'wifis': network_config.get('wifis', {})
        }
    }
    
    # Convert to YAML
    yaml_content = yaml.dump(netplan_config, default_flow_style=False, sort_keys=False)
    
    # Save to file if path is provided
    if output_path:
        with open(output_path, 'w') as f:
            f.write(yaml_content)
    
    return yaml_content

@click.command(
    name="network-apply",
    help="Apply network settings from an INI configuration file",
    short_help="Apply network settings"
)
@click.argument("ini_file", type=click.Path(exists=True), required=True)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Save Netplan YAML to a file (default: /etc/netplan/99-netmancer-<interface>.yaml for ethernet or 100-netmancer-<interface>.yaml for wireless)"
)
@click.option(
    "--apply", "-a",
    is_flag=True,
    help="Apply the configuration immediately"
)
def network_apply(ini_file, output, apply):
    """Apply network settings from an INI configuration file"""
    try:
        # Read and parse the INI file
        network_config, interface, interface_type = read_ini_file(ini_file)
        
        # Generate Netplan YAML
        if output:
            output_path = output
        else:
            # Use the specified naming convention based on interface type
            if interface_type == 'ethernet':
                output_path = f"/etc/netplan/99-netmancer-{interface}.yaml"
            else:  # wifi
                output_path = f"/etc/netplan/100-netmancer-{interface}.yaml"
        
        yaml_content = generate_netplan_yaml(network_config, output_path, interface, interface_type)
        
        # Log success
        message = f"Generated Netplan configuration from {ini_file} and saved to {output_path}"
        click.echo(message)
        log_command("network-apply", message)
        
        # For testing purposes, display the generated YAML
        click.echo("\nGenerated YAML content:")
        click.echo(yaml_content)
        
        # Apply the configuration if requested (commented out for testing)
        """
        if apply:
            try:
                # Check if we need sudo
                if os.geteuid() != 0:
                    click.echo("Applying configuration requires root privileges. Using sudo...")
                    subprocess.run(["sudo", "netplan", "apply"], check=True)
                else:
                    subprocess.run(["netplan", "apply"], check=True)
                
                apply_message = "Applied Netplan configuration successfully"
                click.echo(apply_message)
                log_command("network-apply", apply_message)
            except subprocess.CalledProcessError as e:
                error_message = f"Error applying Netplan configuration: {e}"
                click.echo(error_message, err=True)
                log_command("network-apply", error_message)
                return 1
        """
        
        return 0
    
    except FileNotFoundError as e:
        error_message = f"Error: {str(e)}"
        click.echo(error_message, err=True)
        log_command("network-apply", error_message)
        return 1
    except Exception as e:
        error_message = f"Error: {str(e)}"
        click.echo(error_message, err=True)
        log_command("network-apply", error_message)
        return 1

