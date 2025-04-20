"""Show the status of the network interface"""

import click
import subprocess
import json
from netmancer_cli.utils.valid_interface import InterfaceValidator
from netmancer_cli.utils.logger import log_command

@click.command(
    name="interface-status",
    help="Show the status of the network interface",
    short_help="Show interface status"
)
@click.argument("interface", required=True)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Save output to a JSON file"
)
def interface_status(interface, output):
    """Show the status of the specified network interface"""
    try:
        # Validate interface
        if not InterfaceValidator.is_valid_interface(interface):
            error_message = f"Error: Interface '{interface}' is not connected or does not exist"
            click.echo(error_message, err=True)
            log_command("interface-status", error_message)
            return 1
            
        # Run nmcli command to get interface status
        result = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output
        status = {}
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            # Split by colon as nmcli uses colon as separator in tabular mode
            parts = line.split(':')
            if len(parts) >= 4:
                device, type_, state, connection = parts[:4]
                if device == interface:
                    status = {
                        'DEVICE': device,
                        'TYPE': type_,
                        'STATE': state,
                        'CONNECTION': connection if connection else ''
                    }
                    break
        
        if not status:
            error_message = f"Error: Interface '{interface}' not found"
            click.echo(error_message, err=True)
            log_command("interface-status", error_message)
            return 1
        
        # Convert to JSON
        json_output = json.dumps(status, indent=2)
        
        # Output to file if specified
        if output:
            with open(output, 'w') as f:
                f.write(json_output)
            message = f"Output saved to {output}"
            click.echo(message)
            log_command("interface-status", message)
        else:
            # Output to stdout
            click.echo(json_output)
            log_command("interface-status", f"Showed status for interface {interface}")
        
    except subprocess.CalledProcessError as e:
        error_message = f"Error running nmcli: {e}"
        click.echo(error_message, err=True)
        log_command("interface-status", error_message)
        return 1
    except Exception as e:
        error_message = f"Error: {str(e)}"
        click.echo(error_message, err=True)
        log_command("interface-status", error_message)
        return 1
    
    return 0

