#!/usr/bin/env python3

import json
import subprocess
import os
from time import sleep
import ipaddress
from pathlib import Path
import sqlite3
from datetime import datetime

JSON_DB_PATH = os.path.expanduser("/etc/netmancer/network_config.json")
DB_PATH = "/data/sysconf.db"
LOG_FILE_PATH = "/var/log/netmancerd.log"
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 10))

def cidr_to_netmask(cidr):
    """Convert CIDR notation to dotted-decimal netmask."""
    try:
        return str(ipaddress.IPv4Network(f"0.0.0.0/{cidr}").netmask)
    except ValueError:
        return ""

def run_command(command):
    """Run a system command and return the output."""
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command '{' '.join(command)}': {e}")
        log_message(f"Error executing command '{' '.join(command)}': {e}")
        return ""

def get_network_info():
    """Retrieve connected network configuration (Wi-Fi or Ethernet only)."""
    network_data = {"NetworkNodes": []}

    result = run_command(['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE,CONNECTION', 'device'])

    if not result:
        return network_data

    devices = result.split("\n")

    for device_info in devices:
        if not device_info:
            continue

        device, conn_type, state, connection_name = device_info.split(":")

        if state != "connected" or conn_type not in ["wifi", "ethernet"]:
            continue

        node_info = {
            "NodeName": device,
            "NodeType": conn_type.capitalize(),
            "IP": "NA",
            "CIDR": "NA",
            "Netmask": "NA",
            "Gateway": "NA",
            "NameServers": [],
        }

        ip_result = run_command(['nmcli', '-f', 'IP4.ADDRESS,IP4.GATEWAY,IP4.DNS', 'device', 'show', device])

        if not ip_result:
            continue

        for line in ip_result.split("\n"):
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

        node_info["NameServers"] = list(sorted(set(node_info["NameServers"])))
        network_data["NetworkNodes"].append(node_info)

    return network_data


def ensure_directory_exists(path):
    """Ensure the directory for the JSON DB path exists."""
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def load_existing_network_data():
    """Load the existing network configuration from the JSON DB."""
    if not os.path.exists(JSON_DB_PATH):
        return {"NetworkNodes": []}
    try:
        with open(JSON_DB_PATH, 'r') as json_file:
            return json.load(json_file)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading existing network data: {e}")
        log_message(f"Error reading existing network data: {e}")
        return {"NetworkNodes": []}


def has_network_data_changed(new_data, existing_data):
    """Check if the network data has changed by comparing node IPs."""
    existing_nodes = {node["NodeName"]: node for node in existing_data.get("NetworkNodes", [])}
    new_nodes = {node["NodeName"]: node for node in new_data.get("NetworkNodes", [])}

    for new_node_name, new_node in new_nodes.items():
        existing_node = existing_nodes.get(new_node_name)
        if not existing_node or existing_node["IP"] != new_node["IP"]:
            return True

    for existing_node_name in existing_nodes:
        if existing_node_name not in new_nodes:
            return True

    return False


def prune_removed_nodes(new_data, existing_data):
    """Update nodes in existing data, keeping entries for disconnected interfaces."""
    new_node_names = {node["NodeName"] for node in new_data.get("NetworkNodes", [])}
    for existing_node in existing_data["NetworkNodes"]:
        if existing_node["NodeName"] not in new_node_names:
            # Mark disconnected node details as 'NA'
            existing_node.update({"IP": "NA", "CIDR": "NA", "Netmask": "NA", "Gateway": "NA", "NameServers": ["NA"]})
            new_data["NetworkNodes"].append(existing_node)

def save_network_data(data):
    """Save the network data to a JSON file."""
    try:
        with open(JSON_DB_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4)
    except IOError as e:
        print(f"Error writing to file {JSON_DB_PATH}: {e}")
        log_message(f"Error writing to file {JSON_DB_PATH}: {e}")


def log_message(message):
    """Write a log message to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    try:
        with open(LOG_FILE_PATH, 'a') as log_file:
            log_file.write(log_entry)
    except IOError as e:
        print(f"Error writing to log file {LOG_FILE_PATH}: {e}")
        log_message(f"Error writing to log file {LOG_FILE_PATH}: {e}")


def update_sysconf_db(network_data):
    """Update the SQLite database with network details if IPs have changed."""
    db_updated = False
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for node in network_data["NetworkNodes"]:
            # Replace 'NA' with an empty string before updating
            ip = "" if node["IP"] == "NA" else node["IP"]
            netmask = "" if node["Netmask"] == "NA" else node["Netmask"]
            gateway = "" if node["Gateway"] == "NA" else node["Gateway"]
            primary_dns = "" if not node["NameServers"] or node["NameServers"][0] == "NA" else node["NameServers"][0]
            secondary_dns = "" if len(node["NameServers"]) < 2 or node["NameServers"][1] == "NA" else node["NameServers"][1]
            interface = node["NodeName"]

            cursor.execute("SELECT IP FROM NetworkDetails WHERE NetworkType = ?", (interface,))
            row = cursor.fetchone()

            if row is None or row[0] != ip:
                cursor.execute(
                    "UPDATE NetworkDetails SET IP=?, Subnetmask=?, Gateway=?, PrimaryDNS=?, SecondaryDNS=? WHERE NetworkType=?",
                    (ip, netmask, gateway, primary_dns, secondary_dns, interface)
                )
                db_updated = True
        if db_updated:
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        log_message(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    return db_updated


def main():
    """Main function to monitor and update network configuration."""
    ensure_directory_exists(JSON_DB_PATH)

    if not os.access(JSON_DB_PATH, os.W_OK) and os.path.exists(JSON_DB_PATH):
        print(f"Permission denied: Cannot write to {JSON_DB_PATH}")
        log_message(f"Permission denied: Cannot write to {JSON_DB_PATH}")
        exit(1)

    while True:
        existing_data = load_existing_network_data()
        network_data = get_network_info()

        if has_network_data_changed(network_data, existing_data):
            prune_removed_nodes(network_data, existing_data)
            save_network_data(network_data)
            db_updated = update_sysconf_db(network_data)
            log_message("Network configuration updated in JSON DB and SQLite DB.") if db_updated else log_message("Network configuration updated in JSON DB only.")
            print("Network configuration updated.")
        else:
            print("No changes in network configuration.")

        sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
