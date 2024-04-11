import logging


class CustomFormatter(logging.Formatter):
    grey = "\033[2;97m"
    yellow = "\033[0;33m"
    white = "\033[0;97m"
    red = "\033[0;31m"
    bold_red = "\033[0;1m"
    reset = "\033[0;97m"
    format = '{asctime:<27}{levelname:<11}{message}'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: white + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, style='{')
        return formatter.format(record)


def create_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    sh = logging.StreamHandler()
    logger.setLevel(level)
    sh.setFormatter(CustomFormatter())
    logger.addHandler(sh)
    return logger


logger = create_logger('main_logger', logging.DEBUG)
