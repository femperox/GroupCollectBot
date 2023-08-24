from datetime import datetime

def getHeader():
    """Установка заголовков для запросов

    Returns:
        dict: основные настройки заголовков
    """

    headers = {
        'User-Agent': ': Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 OPR/86.0.4363.64',
        'Content-Type': 'application/json, text/plain, */*',
        'x-platform': 'web',
    }

    return headers

def getCurrentTime():
    """Получить текущую дату+время

    Returns:
        string: текущая дата+время
    """
    
    return datetime.now().strftime('%Y-%m-%d %H:%M')