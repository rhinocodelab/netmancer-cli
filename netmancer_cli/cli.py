"""Netmancer CLI"""

import click
from netmancer_cli.commands.list_network_interfaces import list_network_interfaces
from netmancer_cli.commands.showinfo import show_info
from netmancer_cli.commands.dhcpinfo import dhcp_info
from netmancer_cli.commands.interface_status import interface_status
from netmancer_cli.commands.network_appy import network_apply

@click.group()
def cli():
    """Netmancer CLI"""
    pass

# Add commands to the CLI group
cli.add_command(list_network_interfaces)
cli.add_command(show_info)
cli.add_command(dhcp_info)
cli.add_command(interface_status)
cli.add_command(network_apply)

if __name__ == '__main__':
    cli()


