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


# Create a separate logger for collision detection events
collision_logger = logging.getLogger('collision_detection')
collision_logger.setLevel(logging.INFO)

# Create dedicated handler for collision events
collision_handler = logging.FileHandler('./logs/collision.log')
collision_handler.setLevel(logging.INFO)

# Create detailed formatter for collision events
collision_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
collision_handler.setFormatter(collision_format)

# Add handler to collision logger
collision_logger.addHandler(collision_handler)

# Prevent collision logs from propagating to root logger
collision_logger.propagate = False
