from APIs.webUtils import WebUtils 
from pprint import pprint

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
        info['text'] = postContent.get_text(separator='\n\n')
        info['origin'] = YouLoveItApi.origin

        return info