from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_community.tools import WikipediaQueryRun, OpenWeatherMapQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, OpenWeatherMapAPIWrapper
import os
from dotenv import load_dotenv
from langchain.tools import Tool
from Server.Agents.InputModel import *
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from huggingface_hub import InferenceClient
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_experimental.utilities import PythonREPL
import json
from typing import Optional
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_huggingface.chat_models.huggingface import HuggingFaceEndpoint,ChatHuggingFace
from langchain_community.tools import ClickTool


class YouTubeSearchTool:
    def _search(self, person: str, num_results: int) -> str:
        from youtube_search import YoutubeSearch

        results = YoutubeSearch(person, num_results).to_json()
        data = json.loads(results)
        url_suffix_list = [
            "https://www.youtube.com" + video["url_suffix"] for video in data["videos"]
        ]
        return str(url_suffix_list)

    def run(
            self,
            query: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        try:
            values = query.split(",")
            person = values[0]
            if len(values) > 1:
                num_results = int(values[1])
            else:
                num_results = 2
            return self._search(person, num_results)
        except Exception as e:
            values = query.split(",")
            num_results = 55
            person = values[0]
            return self._search(person, num_results)


load_dotenv()

Huggingface = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    huggingfacehub_api_token=os.getenv("LLAMA_TOKEN"),
)
llm=ChatHuggingFace(llm=Huggingface)


def phi3(query, max_tokens=5000):
    client = InferenceClient(
        "microsoft/Phi-3-mini-4k-instruct",
        token=os.getenv("LLAMA_TOKEN"),
    )
    response = ""
    for message in client.chat_completion(
            messages=[{"role": "user", "content": query}],
            max_tokens=max_tokens,
            stream=True,
    ):
        if message.choices is not None:
            response += message.choices[0].delta.content
    return response


def medllama(query, max_tokens=5000):
    client = InferenceClient(
        "meta-llama/Meta-Llama-3-8B-Instruct",
        token=os.getenv("LLAMA_TOKEN"),
    )
    sys_message = ''' 
       You are an AI Medical Assistant trained on a vast dataset of health information. Please be thorough and
       provide an informative answer. If you don't know the answer to a specific medical inquiry, advise seeking professional help.
       '''
    response = ""
    for message in client.chat_completion(
            messages=[{"role": "system", "content": sys_message}, {"role": "user", "content": query}],
            max_tokens=max_tokens,
            stream=True,
    ):
        if message.choices is not None:
            response += message.choices[0].delta.content
    return response


def song_lyrics(query, max_tokens=5000):
    content = f"""
    "Please write song lyrics with the following structure: Intro-Verse-Chorus-Verse-Chorus-Bridge-Chorus-Outro.Rewrite an English love song in English, give me the title, complete lyrics, and style of the song, without translation or phonetic notation, with emotional and heartfelt lyrics. Here's a breakdown of each section:
song name:{query}
Style of Music:
Intro:
Verse 1:
Chorus:
Verse 2:
Chorus:
Bridge:
Chorus:
Outro:

    """
    client = InferenceClient(
        "meta-llama/Meta-Llama-3-8B-Instruct",
        token=os.getenv("LLAMA_TOKEN"),
    )
    response = ""
    for message in client.chat_completion(
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens,
            stream=True,
    ):
        if message.choices is not None:
            response += message.choices[0].delta.content
    return response


phi3_tool = Tool(
    name="Phi3",
    description="The tool which can answer any Conversation related Query.",
    func=phi3,
    args_schema=Phi3_Input
)

medllama_tool = Tool(
    name="medical-bot",
    description="The Tool which can answer any medical related Query.",
    func=medllama,
    args_schema=Phi3_Input
)
song_lyrics_tools = Tool(
    name="MusicLM",
    description="The Tool which can generate Lyrics based on the query",
    func=song_lyrics,
    args_schema=Phi3_Input
)


def python_repl(query):
    python_reply = PythonREPL()
    return python_reply.run(query)


# You can create the tool to pass to an agent
repl_tool = Tool(
    name="python_repl",
    description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
    func=python_repl,
    args_schema=HuggingGpt_Input,
)

youtube_tool = Tool(
    name="youtube_search",
    description=(
        "search for youtube videos associated with a person. "
        "the input to this tool should be a comma separated list, "
        "the first part contains a person name and the second a "
        "number that is the maximum number of video results "
        "to return aka num_results. the second part is optional"
    ),
    func=YouTubeSearchTool().run,
    args_schema=Phi3_Input,
)
wikipedia_api_wrapper = WikipediaAPIWrapper(top_k_results=5, doc_content_chars_max=250)
wikipedia_tool = WikipediaQueryRun(api_wrapper=wikipedia_api_wrapper)
open_weather_api_wrapper = OpenWeatherMapAPIWrapper()
open_weather_tool = OpenWeatherMapQueryRun(api_wrapper=open_weather_api_wrapper)
def agent(inputs):
    print(f"Agent 3:{inputs}")
    tools=load_tools(["arxiv", "wolfram-alpha", "stackexchange", "pubmed"])
    for i in [open_weather_tool, youtube_tool,DuckDuckGoSearchRun(),DuckDuckGoSearchResults(),YahooFinanceNewsTool(),phi3_tool]:
        tools.append(i)
    # Get the prompt to use - you can modify this!
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    # Create an agent executor by passing in the agent and tools
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True,)
                                   #max_iterations=4 * len(tools))
    response = agent_executor.invoke({"input": inputs})['output']
    return response

if __name__=="__main__":
    while True:
        user=input("USER:")
        if "exit" in user:
            break
        print(f"Assistant:{agent(user)}")

