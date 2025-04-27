import asyncio
import json
import os
import openai
from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, RunConfig, Runner
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

project = projects[1]

# 解析project为key:value的格式的字符串
# 例如 <full_name> test </full_name> <description> test </description> <language> test </language>
project_str = ""
for key, value in project.items():
    project_str += f"<{key}> {value} </{key}>\n"

# 使用openai的agents
class ProjectInfo(BaseModel):
    name: str
    summary: str
    detail: str
    url: str
    language: str
    stars: int
    topics: list[str]
    types: list[str]

prompt = f"""
分析github项目，并返回项目信息，包括项目名称、项目描述、项目语言、项目星数、项目url、项目主题、项目类型。
需要使用中文分析，必要的情况下，保留一部分英文说明，不要机翻。
其中，
topic有：AI、Web、Mobile、Desktop、Server、Game、Other。
type有：Library、Tool、Framework、Plugin、Service、Other。

"""

agent = Agent(
    name="github项目分析",
    instructions=prompt,
    model=OpenAIChatCompletionsModel( 
        model=model_name,
        openai_client=openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        ),
    ),
    output_type=ProjectInfo,
)


async def main():
    try:
        result = await Runner.run(
            agent, 
            project_str,
            run_config=RunConfig(tracing_disabled=True, model_settings=ModelSettings(temperature=0.2))
        )
        final_output = result.final_output
        print(f"Project: {final_output.name}")
        print(f"Summary: {final_output.summary}")
        print(f"Detail: {final_output.detail}")
        print(f"Language: {final_output.language}")
        print(f"Stars: {final_output.stars}")
        print(f"Topics: {final_output.topics}")
        print(f"Types: {final_output.types}")
    except Exception as e:
        print(f"Error (expected): {e}")

if __name__ == "__main__":
    asyncio.run(main())
