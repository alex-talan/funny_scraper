import os
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

class ScrapingStrategy(ABC):

    def __init__(self, main_url: str, name:str):
        self.main_url = main_url
        self.name = name
    
    def scrap(self, k: int) -> list[str]:
        html = self._get_html(self.main_url)
        soup = BeautifulSoup(html, "lxml")

        news_links = self._extract_news_links(soup, self.main_url)

        contents = []

        for link in news_links[:k]:
            article_html = self._get_html(link)
            article_soup = BeautifulSoup(article_html, "lxml")

            content = self._extract_content(article_soup)
            contents.append(content)

        return contents

    def _get_html(self, url: str) -> str:
        response = httpx.get(url, timeout=20, follow_redirects=True)
        response.raise_for_status()
        return response.text

    def _extract_news_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        links = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            absolute_url = urljoin(base_url, href)

            if self.is_news_link(absolute_url) and absolute_url not in links:
                links.append(absolute_url)

        return links

    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Cleaning
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Get just the main content
        main_content = soup.find("article") or soup.find("main") or soup.body

        if main_content is None:
            return ""

        return main_content.get_text(separator="\n", strip=True)
    
    @abstractmethod
    def is_news_link(self, absolute_url: str) -> bool:
        pass


class AnthropicNewsScraper(ScrapingStrategy):
     
    def __init__(self):
        super().__init__("https://www.anthropic.com/news", "Anthropic News")
    
    def is_news_link(self, absolute_url: str) -> bool:
        return "/news/" in absolute_url
    
class LatentSpaceNewsScraper(ScrapingStrategy):
     
    def __init__(self):
        super().__init__("https://www.latent.space/", "Latent Space News")
    
    def is_news_link(self, absolute_url: str) -> bool:
        return "/p/" in absolute_url
    

class Scraper:
    def __init__(self):
        self.strategies = [
            AnthropicNewsScraper(), 
            LatentSpaceNewsScraper()
        ]

    def scrape(self, k: int) -> list[str]:
        all_contents = []

        for strategy in self.strategies:
            contents = strategy.scrap(k)
            all_contents.extend(contents)

        return all_contents


class Orchestrator:
    def __init__(self):
        pass

    def invoke(self):

        load_dotenv()

        news_limit = int(os.getenv("NEWS_LIMIT") or 5)

        scraper = Scraper()
        contents = scraper.scrape(news_limit)

        for i, content in enumerate(contents, 1):
            print(f"Article {i}:\n{content}\n{'-'*80}\n")

def main():
    orchestrator = Orchestrator()
    orchestrator.invoke()

if __name__ == "__main__":
    main()