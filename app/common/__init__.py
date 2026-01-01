"""
Common utilities module.

Provides:
- Configuration (Config)
- Logging setup (setup_logging)
- Serialization utilities (compress, decompress)
"""
from .config import Config
from .logging_wrapper import setup_logging
from .serialization import compress, decompress, decompress_telemetry
