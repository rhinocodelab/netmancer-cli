"""Show DHCP information about the network interface"""

import click
import subprocess
import json
from netmancer_cli.utils.logger import log_command
from netmancer_cli.utils.valid_interface import InterfaceValidator
from netmancer_cli.utils.cidr_converter import CIDRConverter

def get_hostname():
    """Get the static hostname using hostnamectl command"""
    try:
        result = subprocess.run(
            ["hostnamectl", "--static"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

@click.command(
    name="dhcp-info",
    help="Show DHCP information about the network interface",
    short_help="Show DHCP info for a specific interface"
)
@click.argument("interface", required=True)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Save output to a JSON file"
)
def dhcp_info(interface, output):
    """Show DHCP information about the specified network interface"""
    try:
        # Validate interface
        if not InterfaceValidator.is_valid_interface(interface):
            error_message = f"Error: Interface '{interface}' is not connected or does not exist"
            click.echo(error_message, err=True)
            log_command("dhcp-info", error_message)
            return 1
            
        # Run nmcli command to get DHCP information
        result = subprocess.run(
            ["nmcli", "-t", "-f", "DHCP4.OPTION", "device", "show", interface],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Initialize DHCP info dictionary
        dhcp_info = {
            'DHCP_SERVER_IDENTIFIER': '',
            'DOMAIN_NAME_SERVER': [],
            'DOMAIN_NAME': '',
            'ROUTES': [],
            'HOSTNAME': get_hostname(),  # Get hostname using the new function
            'IP4_ADDRESS': '',
            'SUBNETMASK': ''
        }
        
        # Parse the output
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            # Split by colon as nmcli uses colon as separator in tabular mode
            parts = line.split(':', 2)  # Split into max 3 parts to handle values containing colons
            if len(parts) >= 2:
                # Extract the actual key-value pair from the last part
                key_value = parts[-1].strip()
                if '=' in key_value:
                    key, value = key_value.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Map nmcli keys to our desired format
                    if key == 'dhcp_server_identifier':
                        dhcp_info['DHCP_SERVER_IDENTIFIER'] = value
                    elif key == 'domain_name_servers':
                        dhcp_info['DOMAIN_NAME_SERVER'] = value.split(';')
                    elif key == 'domain_name':
                        dhcp_info['DOMAIN_NAME'] = value
                    elif key == 'routers':
                        dhcp_info['ROUTES'] = value.split(';')
                    elif key == 'ip_address':
                        dhcp_info['IP4_ADDRESS'] = value
                    elif key == 'subnet_mask':
                        dhcp_info['SUBNETMASK'] = value
        
        # Convert to JSON
        json_output = json.dumps(dhcp_info, indent=2)
        
        # Output to file if specified
        if output:
            with open(output, 'w') as f:
                f.write(json_output)
            message = f"Output saved to {output}"
            click.echo(message)
            log_command("dhcp-info", message)
        else:
            # Output to stdout
            click.echo(json_output)
            log_command("dhcp-info", f"Showed DHCP information for interface {interface}")
        
    except subprocess.CalledProcessError as e:
        error_message = f"Error running nmcli: {e}"
        click.echo(error_message, err=True)
        log_command("dhcp-info", error_message)
        return 1
    except Exception as e:
        error_message = f"Error: {str(e)}"
        click.echo(error_message, err=True)
        log_command("dhcp-info", error_message)
        return 1
    
    return 0
