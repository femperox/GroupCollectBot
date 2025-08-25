from datetime import datetime
import pytz
import locale
import re
from dateutil.relativedelta import relativedelta
from dateutil import parser

class DateUtils:

    @staticmethod
    def getCurrentDate(need_date_str = True):
        """Получить текущую дату

        Returns:
            string: текущая дата
        """
        
        if need_date_str:
            return datetime.now().strftime('%Y-%m-%d')
        else:
            return datetime.now()
    @staticmethod
    def getCurrentMonthString():
        """Получить текущий месяц на русском языке

        Returns:
            string: текущий месяц на русском языке
        """

        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        month = datetime.strftime(datetime.now(), '%b %Y')
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        return month
    
    @staticmethod
    def getDefaultEndTimeForProduct(years = 3):
        """Сгенерировать дефолтное значение для endtime для ProductInfoClass

        Args:
            years (int, optional): год. Defaults to 3.

        Returns:
            datetime: дефолтное значение для endtime для ProductInfoClass
        """

        return datetime.now() + relativedelta(years = years)

    @staticmethod
    def getExpiryDateString():
        """Получить строчку срока хранения

        Returns:
            string: срок хранения
        """

        now = datetime.now()
        gotDate = now.strftime("%d.%m.%Y")
        takeDate = (now + relativedelta(months=+1)).strftime("%d.%m.%Y")
        return '{0} - {1}'.format(gotDate, takeDate)

    @staticmethod
    def parse_utc_date(text):

        date = parser.parse(text.replace(",", ""))
        pdt = pytz.timezone("US/Pacific")
        date = pdt.localize(date)
        date = date.astimezone(pytz.timezone("Europe/Moscow")).replace(tzinfo=None)

        return date

    @staticmethod
    def compair_dates(date1, date2):
        return date1 > date2

    @staticmethod
    def parse_japanese_date_range(text, base_year=None):

        if base_year is None:
            base_year = datetime.now().year

        text = text.strip().replace('～', '~')

        # Регулярное выражение для даты: [ГГГГ年]?ММ月ДД日
        date_pattern = r'(?:\s*(\d{4})年)?(\d{1,2})月(\d{1,2})日'

        matches = re.findall(date_pattern, text)
        if not matches:
            return ''

        # Парсим каждую дату
        parsed_dates = []
        for match in matches:
            year_str, month, day = match
            month = int(month)
            day = int(day)
            year = int(year_str) if year_str else base_year

            try:
                dt = datetime(year, month, day)
                parsed_dates.append(dt)
            except ValueError as e:
                raise ValueError(f"Invalid date: {year}-{month}-{day}") from e

        return list(set([date.strftime('%Y.%m.%d') for date in parsed_dates]))