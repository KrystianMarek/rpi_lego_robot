import logging
import logging.config
import yaml


def setup_logging(config_file='logging.yml'):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
        return logging
