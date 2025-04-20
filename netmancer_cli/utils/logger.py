"""Logger utility for Netmancer CLI"""

import os
import logging
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'log')
os.makedirs(log_dir, exist_ok=True)

# Configure logger
log_file = os.path.join(log_dir, 'netmancer.log')
logger = logging.getLogger('netmancer')
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create formatter
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Get the command from the record's extra attribute, or use 'UNKNOWN' if not provided
        command = getattr(record, 'command', 'UNKNOWN')
        # Format: DATE-TIME COMMAND MESSAGE
        record.msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {command} | {record.msg}"
        return super().format(record)

formatter = CustomFormatter('%(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

def log_command(command_name, message):
    """
    Log a command execution with the specified message.
    
    Args:
        command_name (str): The name of the command being executed
        message (str): The message to log
    """
    logger.info(message, extra={'command': command_name}) 