import logging
import logging.handlers
import os

import coloredlogs


def logging_setup(log_name: str, log_file: str):
    """
    Configures logging for a component (app or bot).
    log_name: The name of the logger (e.g. ‘app’ or ‘bot’).
    log_file: The name of the file where the logs will be written (e.g. ‘app.log’ or ‘bot.log’).
    """
    log_directory = os.path.join(os.path.dirname(__file__), f'../logs/{log_name}')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Full path to the log file
    log_file_path = os.path.join(log_directory, log_file)

    # Configuring basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5
            )
        ]
    )

    # Configuring colouredlogs
    coloredlogs.install(
        level='INFO',
        logger=logging.getLogger(log_name),
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        level_styles={
            'info': {'color': 'green'},
            'warning': {'color': 'yellow'},
            'error': {'color': 'red'},
            'critical': {'color': 'red', 'bold': True},
        },
        field_styles={
            'asctime': {'color': 220},
            'name': {'color': 208},
            'levelname': {'color': 'white', 'bold': True},
        }
    )

    return logging.getLogger(log_name)
