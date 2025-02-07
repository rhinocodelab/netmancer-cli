import argparse

def main():
    parser = argparse.ArgumentParser(prog="netmancer")
    subparsers = parser.add_subparsers()

    # Import and configure each command
    from netmancer.commands.list_network_nodes import configure_parser as list_network_nodes_parser
    from netmancer.commands.ethernet import configure_parser as ethernet_parser

    list_network_nodes_parser(subparsers)
    ethernet_parser(subparsers)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()