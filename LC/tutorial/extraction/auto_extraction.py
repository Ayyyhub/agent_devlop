import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# 使用 Pydantic 定义输出结构（结构化规则约束schema）
class MusicInfo(BaseModel):
    """音乐信息"""
    artist: str = Field(description="The name of the musical artist")   # Field给字段添加描述
    song: str = Field(description="The name of the song that the artist plays")

def main():
    # 加载环境变量
    load_dotenv()                                   # load_dotenv()：从本地 .env 文件加载环境变量
    openai_api_key = os.getenv("OPENAI_API_KEY")    # os.getenv(...)：读取环境变量中的 OpenAI API 密钥
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    
    # 初始化LLM模型
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    
    # 创建 Pydantic 输出解析器
    # PydanticOutputParser：LangChain提供的解析器，作用是把模型返回的文本输出，强制转换成 MusicInfo 结构的对象（比如模型返回 JSON 文本，解析器会转成 MusicInfo 实例）
    output_parser = PydanticOutputParser(pydantic_object=MusicInfo)
    # get_format_instructions()：依赖于PydanticOutputParser实例，生成一段 “格式提示语”（告诉模型 “请输出 JSON 格式，包含 artist 和 song 字段”），这段提示会加到给模型的指令里，确保模型输出符合要求
    format_instructions = output_parser.get_format_instructions()
    # 创建提示词模板
    # 这个 Prompt 会自动将格式说明包含进去，确保LLM输出符合schema
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that extracts information from user input."),
        ("user", """Given a command from the user, extract the artist and song names.

        {format_instructions}
        
        User input: {user_prompt}""")
    ])
    # 使用 partial_variables 预填充格式说明
    prompt = prompt.partial(format_instructions=format_instructions)


    # 创建链：prompt -> llm -> parser
    chain = prompt | llm | output_parser
    
    # 执行提取
    user_input = "I really like So Young by Portugal. The Man"
    print("=" * 50)
    print("输入：")
    print(user_input)
    print("\n" + "=" * 50)
    print("正在提取信息...")
    
    try:
        # 执行这条流水线，传入用户输入，得到解析后的 MusicInfo 对象
        output = chain.invoke({"user_prompt": user_input})
        
        print("\n" + "=" * 50)
        print("提取结果：")
        print("=" * 50)
        # Pydantic 模型可以使用属性访问或字典访问
        print(f"艺术家：{output.artist}")
        print(f"歌曲：{output.song}")
        print("\n完整输出：")
        print(output)
        print(f"\n输出类型：{type(output)}")
        # 也可以转换为字典（Pydantic V2 使用 model_dump()）
        print(f"\n字典格式：{output.model_dump()}")
        
        return output
        
    except Exception as e:
        print(f"\n错误：{e}")
        print("\n提示：如果使用 gpt-3.5-turbo 模型，生成的结果可能不够稳定。")
        print("建议使用 gpt-4 模型以获得更好的结构化输出。")
        return None

if __name__ == "__main__":
    main()