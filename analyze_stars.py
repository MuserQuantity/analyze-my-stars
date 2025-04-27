import asyncio
import json
import os
import openai
from agents import Agent, OpenAIChatCompletionsModel, RunConfig, Runner
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
# 从.env文件中读取信息
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_URL")
model_name = os.getenv("OPENAI_MODEL")

# 先读取all_stars.json文件
with open('all_stars.json', 'r', encoding='utf-8') as f:
    projects = json.load(f)

project = projects[0]

# 解析project为key:value的格式的字符串
# 例如 <full_name> test </full_name> <description> test </description> <language> test </language>
project_str = ""
for key, value in project.items():
    project_str += f"<{key}> {value} </{key}>\n"

# 使用openai的agents
class ProjectInfo(BaseModel):
    name: str
    description: str
    url: str
    language: str
    stars: int
    topics: list[str]
    types: list[str]


agent = Agent(
    name="Project analyzer",
    instructions="Analyze the project and return the project info",
    model=OpenAIChatCompletionsModel( 
        model=model_name,
        openai_client=openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    ),
    output_type=ProjectInfo,
)


async def main():
    try:
        result = await Runner.run(
            agent, 
            project_str,
            run_config=RunConfig(tracing_disabled=True)

        )
        final_output = result.final_output
        print(f"Project: {final_output.name}")
        print(f"Description: {final_output.description}")
        print(f"Language: {final_output.language}")
        print(f"Stars: {final_output.stars}")
        print(f"Topics: {final_output.topics}")
        print(f"Types: {final_output.types}")
    except Exception as e:
        print(f"Error (expected): {e}")

if __name__ == "__main__":
    asyncio.run(main())
