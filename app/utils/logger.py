import logging


class CustomFormatter(logging.Formatter):
    """
    This is a custom logging formatter, it allows to change how logs are displayed
    """

    # ANSI escape codes for formatting logs in different colors
    grey = "\x1b[38;20m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    # This is the basic format for logging messages
    line_format = "%(levelname)s: %(message)s"

    # This dictionary defines the formats for different log levels
    FORMATS = {
        logging.DEBUG: blue + line_format + reset,
        logging.INFO: grey + line_format + reset,
        logging.WARNING: yellow + line_format + reset,
        logging.ERROR: red + line_format + reset,
        logging.CRITICAL: bold_red + line_format + reset,
    }

    def format(self, record):
        """
        This function formats a log message based on its level

        Args:
            record (LogRecord): The log record to be formatted.
        Returns:
            str: The formatted log message.
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Create the main logger
logger = logging.getLogger()

# Create a stream handler, which displays logs in the console
ch = logging.StreamHandler()

# Set the custom formatter for the stream handler
ch.setFormatter(CustomFormatter())

# Add the stream handler to the logger
logger.addHandler(ch)


def not_implemented_warning() -> None:
    """
    A function to display a warning about a feature that's not implemented yet.

    Returns:
        None: This function does not return any value. It only logs a warning message.
    """
    logger.warning("Not implemented yet")
