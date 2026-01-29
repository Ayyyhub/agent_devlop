import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def extraction():
    # 加载.env文件的环境变量
    load_dotenv()
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    
    # 初始化LLM模型
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )
    
    # 定义提取指令
    instructions = """You will be given a sentence with fruit names. 
Extract those fruit names and assign an emoji to them.
Return ONLY a valid JSON object (Python dictionary format) with no additional text.
Example: {{"Apple": "🍎", "Pear": "🍐", "Kiwi": "🥝"}}"""
    
    # fruit_names = "Apple, Pear, this is an kiwi"
    fruit_names ="I love apples and pears, also some kiwis, and bananas"
    
    # 使用 ChatPromptTemplate
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", instructions),
        ("user", "Extract fruits from: {text}")
    ])
    
    # 创建链
    chain = prompt_template | llm | StrOutputParser()
    
    # 执行提取
    output = chain.invoke({"text": fruit_names})
    
    print("=" * 50)
    print("原始输出：")
    print(output)
    print(f"输出类型：{type(output)}")
    
    # 安全解析 JSON （清除 首尾空白字符、换行符啊等格式 问题）
    output_cleaned = output.strip()
    
    # 移除可能的代码块标记
    if output_cleaned.startswith("```"):
        lines = output_cleaned.split("\n")
        output_cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else output_cleaned
        output_cleaned = output_cleaned.strip("").strip("```").strip()
    
    # 解析 JSON
    try:
        output_dict = json.loads(output_cleaned)
    except json.JSONDecodeError as e:
        print(f"\nJSON 解析错误：{e}")
        print("尝试使用 ast.literal_eval...")
        import ast
        output_dict = ast.literal_eval(output_cleaned)
    
    print("\n" + "=" * 50)
    print("解析后的字典：")
    print(output_dict)
    print(f"字典类型：{type(output_dict)}")
    
    return output_dict


if __name__ == '__main__':
    extraction()