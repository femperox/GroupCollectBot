import logging
from logging.handlers import TimedRotatingFileHandler
import os

def create_logger(name=''):
    """Создание логгера с именем name

    Args:
        name (str, optional): имя логгера. Defaults to ''.

    Returns:
        logger object: объект логгера
    """
    logname = os.getcwd()+f'/logs/log{name}/log{name}.log'

    log = logging.getLogger(f'log{name}')
    log.setLevel(logging.INFO)
    ch = TimedRotatingFileHandler(logname, when="midnight", backupCount=30)
    ch.suffix = "%Y%m%d"
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(message)s')

    ch.setFormatter(formatter)
    log.addHandler(ch)


    return log

logger = create_logger()
logger_fav = create_logger('_fav')
logger_utils = create_logger('_utils')