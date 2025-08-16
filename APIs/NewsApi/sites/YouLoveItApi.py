from APIs.webUtils import WebUtils 
from pprint import pprint
from confings.Consts import RegexType, NewsConsts
import re
from APIs.NewsApi.NewsInfoClass import NewsInfoClass
from APIs.NewsApi.NewsParentClass import NewsParentClass
        
class YouLoveItApi(NewsParentClass):
    
    origin = NewsConsts.NewsOrigin.youloveit

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
            NewsInfoClass:информация о новости
        """

        soup = WebUtils.getSoup(url = YouLoveItApi.newsItemPage.format(id))
        info = {}
        postContent = soup.find('span', class_ = 'full-story')
        info['id'] = id
        info['news_url'] = YouLoveItApi.newsItemPage.format(id)
        info['images_list'] = ['https://www.youloveit.com'+ x['src'] for x in postContent.findAll('img')]
        info['origin'] = NewsConsts.NewsOrigin.youloveit

        text = postContent.get_text(separator='\n')
        release_pattern = r'Release date:\s*(.+)\n'
        price_pattern = r'Price:\s*(.+)\n'
        url_pattern = r'can get it here:\s*(https?://\S+)\n'

        info['prices_list'] = re.findall(price_pattern, text)
        info['additional_urls_list'] = list(set(re.findall(url_pattern, text)))
        info['release_date'] = re.findall(release_pattern, text)
        info['additional_dates_list'] = []
        for line in text.split('\n'):
            if re.search(RegexType.regex_dates_in_text, line) and not re.search(r'Release date:', line):
                info['additional_dates_list'].append(line.strip())

        return NewsInfoClass(**info)