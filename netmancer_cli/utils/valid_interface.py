"""Interface validation utility"""

import subprocess
from typing import List, Tuple, Optional

class InterfaceValidator:
    @staticmethod
    def get_all_interfaces() -> List[Tuple[str, str]]:
        """
        Get all network interfaces and their states.
        
        Returns:
            List of tuples containing (interface_name, state)
        """
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "DEVICE,STATE", "device"],
                capture_output=True,
                text=True,
                check=True
            )
            
            interfaces = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                device, state = line.split(':')
                interfaces.append((device, state))
            
            return interfaces
        except subprocess.CalledProcessError:
            return []
    
    @staticmethod
    def is_valid_interface(interface: str) -> bool:
        """
        Check if the interface exists and is connected.
        
        Args:
            interface: Name of the interface to check
            
        Returns:
            True if interface exists and is connected, False otherwise
        """
        try:
            interfaces = InterfaceValidator.get_all_interfaces()
            for device, state in interfaces:
                if device == interface:
                    return 'connected' in state.lower()
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_connected_interfaces() -> List[str]:
        """
        Get list of all connected interfaces.
        
        Returns:
            List of connected interface names
        """
        try:
            interfaces = InterfaceValidator.get_all_interfaces()
            return [device for device, state in interfaces 
                   if 'connected' in state.lower()]
        except Exception:
            return []
    
    @staticmethod
    def get_interface_state(interface: str) -> Optional[str]:
        """
        Get the current state of an interface.
        
        Args:
            interface: Name of the interface
            
        Returns:
            State of the interface if it exists, None otherwise
        """
        try:
            interfaces = InterfaceValidator.get_all_interfaces()
            for device, state in interfaces:
                if device == interface:
                    return state
            return None
        except Exception:
            return None
