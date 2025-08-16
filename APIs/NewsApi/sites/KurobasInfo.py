import requests 
from APIs.NewsApi.NewsInfoClass import NewsInfoClass
from confings.Consts import RegexType, NewsConsts
from APIs.webUtils import WebUtils 
from APIs.utils import parse_japanese_date_range
import re

class KurobasInfo:

    getPostsApi = 'https://kurobas-info.sakura.ne.jp/wp-json/wp/v2/posts'

    @staticmethod
    def getNews():
        """Получение id новостей со страницы

        Args:
            page (int, optional): номер страницы. Defaults to 1.

        Returns:
            list<int>: список id
        """
        response = requests.get(url = KurobasInfo.getPostsApi)

        articles = response.json()

        articleIds = []
        for article in articles:
            articleIds.append(article['id'])

        return articleIds
    
    @staticmethod
    def getNewsInfo(id):
        """Получение содержимого новости

        Args:
            id (string): id новости

        Returns:
            NewsInfoClass:информация о новости
        """

        response = requests.get(url = KurobasInfo.getPostsApi + f'/{id}')

        postContent = response.json()
        info = {}
        
        if postContent:
            info['id'] = postContent['id']
            info['news_url'] = postContent['link']

            soup = WebUtils.getSoup(rawText = postContent['content']['rendered'])
            info['images_list'] = [x['src'] for x in soup.findAll('img')]

            info['origin'] = NewsConsts.NewsOrigin.kurobasInfo

            price_pattern = r'¥\d{1,3}(?:,\d{3})*'
            

            info['prices_list'] = re.findall(price_pattern, postContent['content']['rendered']) 
            info['additional_dates_list'] = parse_japanese_date_range(text = postContent['content']['rendered'])
            info['additional_urls_list'] = list(set(re.findall(RegexType.regex_url, soup.text)))

        return NewsInfoClass(**info)
