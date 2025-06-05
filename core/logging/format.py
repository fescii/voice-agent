"""
Custom log formatting
"""
import logging
from datetime import datetime


class CustomFormatter(logging.Formatter):
    """Custom formatter with color coding and enhanced format"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Format log record with colors and enhanced information"""
        
        # Add timestamp
        record.asctime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Create formatted message
        if hasattr(record, 'call_id'):
            # Include call_id if present
            log_format = (
                f"{self.COLORS.get(record.levelname, '')}"
                f"[{record.asctime}] {record.levelname:8} | "
                f"CALL:{record.call_id} | {record.name} | {record.getMessage()}"
                f"{self.COLORS['RESET']}"
            )
        else:
            log_format = (
                f"{self.COLORS.get(record.levelname, '')}"
                f"[{record.asctime}] {record.levelname:8} | "
                f"{record.name} | {record.getMessage()}"
                f"{self.COLORS['RESET']}"
            )
        
        return log_format
