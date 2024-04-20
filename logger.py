'''Logger for the project'''
import logging

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
info_handler = logging.FileHandler('./logs/info.log')
info_handler.setLevel(logging.INFO)

warning_handler = logging.FileHandler('./logs/warning.log')
warning_handler.setLevel(logging.WARNING)

error_handler = logging.FileHandler('./logs/error.log')
error_handler.setLevel(logging.ERROR)

# Create formatters and add them to the handlers
info_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
info_handler.setFormatter(info_format)

warning_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
warning_handler.setFormatter(warning_format)

error_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_format)

# Add the handlers to the logger
logger.addHandler(info_handler)
logger.addHandler(warning_handler)
logger.addHandler(error_handler)
