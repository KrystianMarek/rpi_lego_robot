"""
Logging configuration utilities.

Provides setup_logging() to configure logging from YAML file.

Formerly named LoggingWrapper.py.
"""
import logging
import logging.config
import yaml


def setup_logging(config_file: str = 'logging.yml'):
    """
    Configure logging from a YAML configuration file.

    Args:
        config_file: Path to logging configuration YAML file

    Returns:
        The logging module for convenience
    """
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
        return logging

