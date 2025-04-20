"""Show information about the network interface"""

import click
import subprocess
import json
import re
from netmancer_cli.utils.logger import log_command
from netmancer_cli.utils.cidr_converter import CIDRConverter
from netmancer_cli.utils.valid_interface import InterfaceValidator

def get_ethernet_info(interface):
    """Get Ethernet interface information using ethtool"""
    try:
        result = subprocess.run(
            ["ethtool", interface],
            capture_output=True,
            text=True,
            check=True
        )
        
        info = {}
        for line in result.stdout.split('\n'):
            if 'Speed:' in line:
                info['SPEED'] = line.split(':')[1].strip()
            elif 'Duplex:' in line:
                info['DUPLEX'] = line.split(':')[1].strip()
            elif 'Wake-on:' in line:
                info['WAKE_ON'] = line.split(':')[1].strip()
        
        return info
    except subprocess.CalledProcessError:
        return {}

def get_wifi_info(interface):
    """Get WiFi interface information using iwconfig"""
    try:
        result = subprocess.run(
            ["iwconfig", interface],
            capture_output=True,
            text=True,
            check=True
        )
        
        info = {}
        for line in result.stdout.split('\n'):
            # Strip leading spaces for matching
            stripped_line = line.lstrip()
            
            # Split line into parts if it contains multiple values
            parts = stripped_line.split('  ')
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                    
                if 'ESSID:' in part:
                    match = re.search(r'ESSID:"([^"]+)"', part)
                    if match:
                        info['ESSID'] = match.group(1)
                elif 'Frequency:' in part:
                    match = re.search(r'Frequency:([\d.]+ GHz)', part)
                    if match:
                        info['FREQUENCY'] = match.group(1)
                elif 'Access Point:' in part:
                    match = re.search(r'Access Point: ([0-9A-F:]+)', part)
                    if match:
                        info['ACCESS_POINT'] = match.group(1)
                elif 'Bit Rate=' in part:
                    match = re.search(r'Bit Rate=([\d.]+ [KM]b/s)', part)
                    if match:
                        info['BIT_RATE'] = match.group(1)
                elif 'Tx-Power=' in part:
                    match = re.search(r'Tx-Power=(\d+ dBm)', part)
                    if match:
                        info['TX_POWER'] = match.group(1)
                elif 'Link Quality=' in part:
                    match = re.search(r'Link Quality=(\d+/\d+)', part)
                    if match:
                        info['LINK_QUALITY'] = match.group(1)
                elif 'Signal level=' in part:
                    match = re.search(r'Signal level=(-?\d+ dBm)', part)
                    if match:
                        info['SIGNAL_LEVEL'] = match.group(1)
        
        return info
    except subprocess.CalledProcessError:
        return {}

@click.command(
    name="show-info",
    help="Show information about the network interface",
    short_help="Show network info for a specific interface"
)
@click.argument('interface', required=True)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Save output to a JSON file'
)
def show_info(interface, output):
    """Show information about the specified network interface"""
    try:
        # Validate interface
        if not InterfaceValidator.is_valid_interface(interface):
            error_message = f"Error: Interface '{interface}' is not connected or does not exist"
            click.echo(error_message, err=True)
            log_command("show-info", error_message)
            return 1
            
        # Run nmcli command to get detailed device information
        result = subprocess.run(
            ["nmcli", "-t", "-f", "IP4.ADDRESS,IP4.GATEWAY,IP4.DNS,IP4.DOMAIN,GENERAL.STATE,GENERAL.TYPE", "device", "show", interface],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output
        info = {
            'IP4.ADDRESSES': [],
            'IP4.DNS_SERVERS': [],
            'IP4.GATEWAY': '',
            'IP4.DOMAIN': '',
            'GENERAL.STATE': '',
            'GENERAL.TYPE': ''
        }
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            # Split by colon as nmcli uses colon as separator in tabular mode
            parts = line.split(':')
            if len(parts) == 2:
                key, value = parts
                # Remove the [n] suffix from the key
                base_key = key.split('[')[0]
                
                if base_key == 'IP4.ADDRESS' and value:
                    try:
                        ip, subnet_mask = CIDRConverter.convert_ip_with_cidr_to_subnet(value)
                        info['IP4.ADDRESSES'].append({
                            'address': ip,
                            'subnet_mask': subnet_mask
                        })
                    except ValueError:
                        info['IP4.ADDRESSES'].append({
                            'address': value,
                            'subnet_mask': None
                        })
                elif base_key == 'IP4.DNS' and value:
                    info['IP4.DNS_SERVERS'].append(value)
                else:
                    info[base_key] = value
        
        # Get additional information based on interface type
        if info['GENERAL.TYPE'].lower() == 'ethernet':
            info['ETHERNET_INFO'] = get_ethernet_info(interface)
        elif info['GENERAL.TYPE'].lower() == 'wifi' or info['GENERAL.TYPE'].lower() == 'wireless':
            info['WIFI_INFO'] = get_wifi_info(interface)
        
        # Convert to JSON
        json_output = json.dumps(info, indent=2)
        
        # Output to file if specified
        if output:
            with open(output, 'w') as f:
                f.write(json_output)
            message = f"Output saved to {output}"
            click.echo(message)
            log_command("show-info", message)
        else:
            # Output to stdout
            click.echo(json_output)
            log_command("show-info", f"Showed information for interface {interface}")
        
    except subprocess.CalledProcessError as e:
        error_message = f"Error running nmcli: {e}"
        click.echo(error_message, err=True)
        log_command("show-info", error_message)
        return 1
    except Exception as e:
        error_message = f"Error: {e}"
        click.echo(error_message, err=True)
        log_command("show-info", error_message)
        return 1
    
    return 0
