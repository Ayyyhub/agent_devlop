from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def a():
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "把下面的语句翻译为{language}。"),
        ("user", "{text}")]
    )

    prompt = prompt_template.invoke({"language": "英文", "text": "飞流直下三千尺，平底高楼百尺高？"})
    print(prompt)


if __name__ == "__main__":
    a()