"""List network interfaces"""

import click
import json
import subprocess
from netmancer_cli.utils.logger import log_command

@click.command(
    name="list-network-interfaces",
    help="List network interfaces",
    short_help="List network interfaces"
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Save output to a JSON file'
)
def list_network_interfaces(output):
    """List network interfaces"""
    try:
        # Run nmcli command to get device information
        result = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output
        interfaces = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            # Split by colon as nmcli uses colon as separator in tabular mode
            parts = line.split(':')
            if len(parts) >= 4:
                device, type_, state, connection = parts[:4]
                
                # Skip loopback interface
                if device == "lo":
                    continue
                    
                interfaces.append({
                    "DEVICE": device,
                    "TYPE": type_,
                    "STATE": state,
                    "CONNECTION": connection if connection else ""
                })
        
        # Convert to JSON
        json_output = json.dumps(interfaces, indent=2)
        
        # Output to file if specified
        if output:
            with open(output, 'w') as f:
                f.write(json_output)
            message = f"Output saved to {output}"
            click.echo(message)
            log_command("list-network-interfaces", message)
        else:
            # Output to stdout
            click.echo(json_output)
            log_command("list-network-interfaces", "Listed network interfaces")
        
    except subprocess.CalledProcessError as e:
        error_message = f"Error running nmcli: {e}"
        click.echo(error_message, err=True)
        log_command("list-network-interfaces", error_message)
        return 1
    except Exception as e:
        error_message = f"Error: {e}"
        click.echo(error_message, err=True)
        log_command("list-network-interfaces", error_message)
        return 1
    
    return 0
