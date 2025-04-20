"""CIDR to Subnet Mask converter utility"""

class CIDRConverter:
    @staticmethod
    def cidr_to_subnet_mask(cidr):
        """
        Convert CIDR notation to Subnet Mask format.
        
        Args:
            cidr (int): CIDR value (0-32)
            
        Returns:
            str: Subnet Mask in dotted decimal notation (e.g., '255.255.255.0')
            
        Raises:
            ValueError: If CIDR is not in valid range (0-32)
        """
        if not isinstance(cidr, int) or cidr < 0 or cidr > 32:
            raise ValueError("CIDR must be an integer between 0 and 32")
            
        # Calculate the subnet mask
        mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
        
        # Convert to dotted decimal notation
        octets = [
            (mask >> 24) & 0xff,
            (mask >> 16) & 0xff,
            (mask >> 8) & 0xff,
            mask & 0xff
        ]
        
        return '.'.join(str(octet) for octet in octets)
    
    @staticmethod
    def extract_cidr_from_ip(ip_with_cidr):
        """
        Extract CIDR value from IP address with CIDR notation.
        
        Args:
            ip_with_cidr (str): IP address with CIDR notation (e.g., '192.168.1.0/24')
            
        Returns:
            int: CIDR value
            
        Raises:
            ValueError: If IP address format is invalid
        """
        try:
            return int(ip_with_cidr.split('/')[1])
        except (IndexError, ValueError):
            raise ValueError("Invalid IP address format. Expected format: x.x.x.x/cidr")
    
    @staticmethod
    def convert_ip_with_cidr_to_subnet(ip_with_cidr):
        """
        Convert IP address with CIDR notation to IP address with Subnet Mask.
        
        Args:
            ip_with_cidr (str): IP address with CIDR notation (e.g., '192.168.1.0/24')
            
        Returns:
            tuple: (IP address, Subnet Mask)
            
        Raises:
            ValueError: If IP address format is invalid
        """
        try:
            ip, cidr = ip_with_cidr.split('/')
            cidr = int(cidr)
            subnet_mask = CIDRConverter.cidr_to_subnet_mask(cidr)
            return ip, subnet_mask
        except (IndexError, ValueError):
            raise ValueError("Invalid IP address format. Expected format: x.x.x.x/cidr") 