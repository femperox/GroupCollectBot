import requests 
from APIs.NewsApi.NewsInfoClass import NewsInfoClass
from confings.Consts import RegexType, NewsConsts
from APIs.webUtils import WebUtils 
from _utils.dateUtils import DateUtils
import re
from APIs.NewsApi.NewsParentClass import NewsParentClass

class KurobasInfoApi(NewsParentClass):

    getPostsApi = 'https://kurobas-info.sakura.ne.jp/wp-json/wp/v2/posts'

    origin = NewsConsts.NewsOrigin.kurobasInfo

    @staticmethod
    def getNews():
        """Получение id новостей со страницы

        Returns:
            list<str>: список id
        """
        response = requests.get(url = KurobasInfoApi.getPostsApi)

        articles = response.json()

        articleIds = []
        for article in articles:
            articleIds.append(str(article['id']))

        return articleIds
    
    @staticmethod
    def getNewsInfo(id):
        """Получение содержимого новости

        Args:
            id (string): id новости

        Returns:
            NewsInfoClass:информация о новости
        """

        response = requests.get(url = KurobasInfoApi.getPostsApi + f'/{id}')

        postContent = response.json()
        info = {}
        
        if postContent:
            info['id'] = postContent['id']
            info['news_url'] = postContent['link']

            soup = WebUtils.getSoup(rawText = postContent['content']['rendered'])
            info['images_list'] = [x['src'] for x in soup.findAll('img')]

            info['origin'] = KurobasInfoApi.origin

            price_pattern = r'¥\d{1,3}(?:,\d{3})*'
            

            info['prices_list'] = re.findall(price_pattern, postContent['content']['rendered']) 
            info['additional_dates_list'] = DateUtils.parse_japanese_date_range(text = postContent['content']['rendered'])
            info['additional_urls_list'] = list(set(re.findall(RegexType.regex_url, soup.text)))

        return NewsInfoClass(**info)
