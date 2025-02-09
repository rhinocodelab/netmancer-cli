import json
import subprocess
import os
from time import sleep
import ipaddress

JSON_DB_PATH = os.path.expanduser("~/network_config.json")
POLL_INTERVAL = 10  # Check network configuration every 10 seconds

def cidr_to_netmask(cidr):
    """Convert CIDR notation to dotted-decimal netmask."""
    try:
        return str(ipaddress.IPv4Network(f"0.0.0.0/{cidr}").netmask)
    except ValueError:
        return ""

def get_network_info():
    """Retrieve connected network configuration (Wi-Fi or Ethernet only)."""
    network_data = {"NetworkNodes": []}

    # Get all devices with their connection status
    result = subprocess.run(
        ['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE,CONNECTION', 'device'], 
        stdout=subprocess.PIPE, text=True
    )

    devices = result.stdout.strip().split("\n")
    
    for device_info in devices:
        if not device_info:
            continue

        device, conn_type, state, connection_name = device_info.split(":")
        
        # Skip devices that are not connected or are not Ethernet/Wi-Fi
        if state != "connected" or conn_type not in ["wifi", "ethernet"]:
            continue

        node_info = {
            "NodeName": device,
            "NodeType": conn_type.capitalize(),
            "IP": "",
            "CIDR": "",
            "Netmask": "",
            "Gateway": "",
            "NameServers": [],
        }

        # Get IP and DNS details for the device
        ip_result = subprocess.run(['nmcli', '-f', 'IP4.ADDRESS,IP4.GATEWAY,IP4.DNS', 'device', 'show', device], 
                                    stdout=subprocess.PIPE, text=True)
        
        for line in ip_result.stdout.strip().split("\n"):
            if "IP4.ADDRESS" in line:
                ip_cidr = line.split(":")[1].strip()
                if "/" in ip_cidr:
                    ip, cidr = ip_cidr.split("/")
                    node_info["IP"] = ip
                    node_info["CIDR"] = f"/{cidr}"
                    node_info["Netmask"] = cidr_to_netmask(cidr)
            elif "IP4.GATEWAY" in line:
                node_info["Gateway"] = line.split(":")[1].strip()
            elif "IP4.DNS" in line:
                dns = line.split(":")[1].strip()
                if dns:
                    node_info["NameServers"].append(dns)

        network_data["NetworkNodes"].append(node_info)

    return network_data

def save_network_data(data):
    """Save the network data to a JSON file."""
    with open(JSON_DB_PATH, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def main():
    """Main function to monitor and update network configuration."""
    while True:
        network_data = get_network_info()
        save_network_data(network_data)
        print("Network configuration updated.")
        sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()

