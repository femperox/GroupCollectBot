from APIs.webUtils import WebUtils 
from pprint import pprint
from confings.Consts import RegexType
import re
        
class YouLoveItApi:
    
    origin = 'youloveit'

    newsMainPage = 'https://www.youloveit.com/dolls/page/{}/'
    newsItemPage = 'https://www.youloveit.com/dolls/{}.html'

    @staticmethod
    def getNews(page = 1):
        """Получение id новостей со страницы

        Args:
            page (int, optional): номер страницы. Defaults to 1.

        Returns:
            list<string>: список id
        """
        
        soup = WebUtils.getSoup(url = YouLoveItApi.newsMainPage.format(page))
        articles = soup.findAll('article')

        articleIds = []
        for article in articles:
            articleIds.append(article.find('a')['href'].split('/')[-1].replace('.html', ''))

        return articleIds
    
    @staticmethod
    def getNewsInfo(id):
        """Получение содержимого новости

        Args:
            id (string): id новости

        Returns:
            dict: словарь с информацией о новости
        """

        soup = WebUtils.getSoup(url = YouLoveItApi.newsItemPage.format(id))
        info = {}
        postContent = soup.find('span', class_ = 'full-story')
        info['id'] = id
        info['url'] = YouLoveItApi.newsItemPage.format(id)
        info['imgs'] = ['https://www.youloveit.com'+ x['src'] for x in postContent.findAll('img')]
        info['origin'] = YouLoveItApi.origin

        text = postContent.get_text(separator='\n')
        release_pattern = r'Release date:\s*(.+)\n'
        price_pattern = r'Price:\s*(.+)\n'
        url_pattern = r'can get it here:\s*(https?://\S+)\n'

        release_info = re.findall(release_pattern, text)
        price_info = re.findall(price_pattern, text)
        urls_info = list(set(re.findall(url_pattern, text)))

        date_lines = []
        for line in text.split('\n'):
            if re.search(RegexType.regex_dates_in_text, line) and not re.search(r'Release date:', line):
                date_lines.append(line.strip())

        info['text'] = ''
        info['text'] += "Дата релиза:\n" + " ".join(release_info) + "\n\n" if release_info else ''
        info['text'] += "Доп. инфо даты:\n" + " ".join(date_lines) + "\n\n" if date_lines else ''
        info['text'] += "Цена:\n" + " ".join(price_info) + "\n\n" if price_info else ''
        info['text'] += "Ссылки:\n" + "\n".join(urls_info) + "\n\n" if urls_info else ''

        return info