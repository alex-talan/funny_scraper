import os
import asyncio
import smtplib
import httpx
from abc import ABC, abstractmethod
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email.message import EmailMessage
from pydantic import BaseModel, Field
from typing import TypedDict, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langsmith.async_client import AsyncClient
from langchain_openrouter import ChatOpenRouter
from openrouter.errors.toomanyrequestsresponse_error import TooManyRequestsResponseError
from langgraph.graph import StateGraph, START, END

def build_langsmith_client(api_key: str) -> AsyncClient:
    return AsyncClient(
        api_key=api_key, 
        api_url="https://eu.api.smith.langchain.com"
    )

class EmailField(BaseModel):
    subject: str = Field(description="The subject of the email")
    body: str = Field(description="The body content of the email")


class LlmProvider(ABC):

    @abstractmethod
    async def invoke(self, messages):
        pass

class PromptProvider(ABC):
    
    @abstractmethod
    async def get_prompt(self, variables:dict = {}) -> ChatPromptTemplate:
        pass

class LangsmithPromptProvider(PromptProvider):

    def __init__(self, api_key: str, prompt_name: str):
        self.client = build_langsmith_client(api_key) 
        self.prompt_name = prompt_name

    async def get_prompt(self, variables:dict = {}) -> ChatPromptTemplate:
        prompt: ChatPromptTemplate = await self.client.pull_prompt(self.prompt_name)
        for variable, value in variables.items():
            if variable in prompt.input_variables:
                prompt = prompt.partial({variable: value})
        return prompt
    
class SummarizationPromptProvider(LangsmithPromptProvider):
    def __init__(self):
        super().__init__(
            api_key=os.getenv("LANGSMITH_KEY"), 
            prompt_name="funny_scraper_summary_prompt"
        )

class EmailPromptProvider(LangsmithPromptProvider):
    def __init__(self):
        super().__init__(
            api_key=os.getenv("LANGSMITH_KEY"), 
            prompt_name="funny_scraper_email_prompt"
        )

class OpenRouterProvider(LlmProvider):

    def __init__(self):
        load_dotenv()

        self.llm = ChatOpenRouter(
            model=os.getenv("MODEL_NAME"),
            temperature=0,
        )

    async def invoke(self, messages):
        for attempt in range(3):
            try:
                return await self.llm.ainvoke(messages)

            except TooManyRequestsResponseError:
                wait_time = 5 * (attempt + 1)
                print(f"Rate limit reached. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

class BasicChain:

    def __init__(self, 
            llm_provider: LlmProvider,
            prompt_provider: PromptProvider):
        self.llm = llm_provider
        self.prompt_provider = prompt_provider

    async def invoke(self, input_message: str):
        prompt_template = await self.prompt_provider.get_prompt()
        messages = prompt_template.format_messages(question=input_message)
        output = await self.llm.invoke(messages)
        return output.content

class PydanticChain(BasicChain):

    def __init__(self, 
            llm_provider: LlmProvider,
            prompt_provider: PromptProvider,
            pydantic_object: type):
        super().__init__(llm_provider=llm_provider, prompt_provider=prompt_provider)
        self.pydantic_object = pydantic_object

    async def invoke(self, input_message: str):
        output_parser = PydanticOutputParser(pydantic_object=self.pydantic_object)
        format_instructions = output_parser.get_format_instructions()
        prompt_template = await self.prompt_provider.get_prompt()

        messages = prompt_template.format_messages(question=input_message, format_instructions=format_instructions)
        output = await self.llm.invoke(messages)
        response = output_parser.parse(output.content)
        return response
    
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
    def __init__(self, strategies: list[ScrapingStrategy]):
        self.strategies = strategies

    def scrape(self, k: int) -> list[str]:
        all_contents = []

        for strategy in self.strategies:
            contents = strategy.scrap(k)
            all_contents.extend(contents)

        return all_contents

class EmailSender:

    def __init__(self):
        load_dotenv()
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT") or 587)
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.sender = os.getenv("EMAIL_FROM")

    def send_email(self, recipient: str, subject: str, body: str):
        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(self.username, self.password)
            smtp.send_message(msg)
            smtp.quit()

class AgentState(TypedDict):
    news: list[str]
    email_subject: str
    email_body: str
    email_generation_attempts: int

class Orchestrator:
    def __init__(self):
        load_dotenv()

        self.news_limit = int(os.getenv("NEWS_LIMIT") or 5)
        self.max_attempts = int(os.getenv("MAX_ATTEMPTS") or 3)
        self.email_to = os.getenv("EMAIL_TO") or ""
        self.scraper = Scraper([
            AnthropicNewsScraper(),
            LatentSpaceNewsScraper()
        ])

        self.summary_agent = BasicChain(
            llm_provider=OpenRouterProvider(),
            prompt_provider=SummarizationPromptProvider()
        )

        self.email_agent = PydanticChain(
            llm_provider=OpenRouterProvider(),
            prompt_provider=EmailPromptProvider(),
            pydantic_object=EmailField
        )

    async def generate_email(self, state: AgentState) -> AgentState:
        """"This function will generate the email to be sent based on the news summaries.
        The email must have a funny subject and body must start with a joke and follow with a summary of the news and a funny comment at the end."""
        email:EmailField = await self.email_agent.invoke("\n\n".join(state["news"]))
        print(f"Generated email:\nSubject: {email.subject}\nBody:\n{email.body}")
        
        return AgentState(
            news=state["news"],
            email_subject=email.subject,
            email_body=email.body,
            email_generation_attempts=state["email_generation_attempts"] + 1
        )

    async def send_email(self, state: AgentState) -> AgentState:
        """ This function will send the email to the recipient defined in the environment variables."""
        await asyncio.run(
            EmailSender().send_email(
                self.email_to,
                state["email_subject"],
                state["email_body"]
            )
        )
        return state
    
    def decide_next_node(self, state:AgentState) -> Literal["OK", "FAIL", "BREAK"]:
        """This node will select the next node of the graph"""
        # TODO: call the llm to decide the next node based on the state of the agent
        if state["email_body"]:
            return "OK"
        if state["email_generation_attempts"] >= self.max_attempts:
            return "BREAK"
        attempts = state["email_generation_attempts"]
        print(f"Email generation failed, attempts: {attempts} - retrying...")
        return "FAIL"

    async def invoke(self):

        # SCRAPING & SUMMARIZATION (no graph logic needed here)

        contents = self.scraper.scrape(self.news_limit)
        print("Scraped news articles, now summarizing...\n")

        async def summarize_article(i: int, content: str) -> str:
            summary = await self.summary_agent.invoke(content)
            return f"Article {i}:\n{summary}\n{'-'*3}\n"

        tasks = [
            summarize_article(i, content)
            for i, content in enumerate(contents, 1)
        ]

        news = await asyncio.gather(*tasks)
        print("Summarization completed. Now running Graph logic...\n")

        # GRAPH DEFINITION

        graph = StateGraph(AgentState)

        graph.add_node("email_generator", self.generate_email)
        graph.add_node("email_sender", self.send_email)

        graph.add_edge(START, "email_generator")
        graph.add_conditional_edges(
            "email_generator",
            self.decide_next_node, 
            {
                # Edge: Node
                "OK": "email_sender",
                "FAIL": "email_generator",
                "BREAK": END #TODO: call node to generate message and send it.
            }
        )
        graph.add_edge("email_sender", END)

        graph_agent = graph.compile()

        initial_state = AgentState(
            news=news,
            email_subject="",
            email_body="",
            email_generation_attempts=0
        )

        await graph_agent.ainvoke(initial_state)

def main():
    orchestrator = Orchestrator()
    asyncio.run(orchestrator.invoke())

if __name__ == "__main__":
    main()