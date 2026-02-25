from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def long_summary():
    # 1. 加载API配置（你的原有逻辑）
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    # 2. 初始化模型（你的原有逻辑）
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    # 3. 读取文本 + 缩短信本（关键：只取前3000字符，确保token≤4k）
    with open('wonderland.txt', 'r', encoding='utf-8') as file:
        text = file.read()

    # 缩短信本：只取前3000字符（远低于4k token上限），也可手动编辑txt只保留前几章
    short_text = text[:3000]

    # 4. 你的原有打印逻辑（验证文本）
    print("=== 文本预览 ===")
    print(short_text[:285])  # 打印缩短后文本的前285字符
    num_tokens = llm.get_num_tokens(short_text)
    print(f"\n缩短后文本Token数：{num_tokens}（≤4096，可直接总结）")

    # 5. 补充核心：定义总结Prompt + 调用模型生成总结（你缺失的部分）
    # 定义总结模板
    summary_template = """
    请总结以下《爱丽丝梦游仙境》的文本内容，要求：
    1. 保留核心情节、人物和关键细节；
    2. 语言简洁易懂，不超过300字；
    3. 忠于原文，不添加额外信息。

    文本内容：
    {text}
    """

    # 创建ChatPrompt模板
    prompt = PromptTemplate(input_variables=["text"], template=summary_template)
    # 渲染Prompt（填充缩短信本）
    final_prompt = prompt.format(text=short_text)
    # 调用模型总结 + 解析输出
    summary_result = llm.invoke(final_prompt)
    parser = StrOutputParser()

    final_summary = parser.invoke(summary_result)

    # 6. 打印总结结果
    print("\n=== 《爱丽丝梦游仙境》总结 ===")
    print(final_summary)


# 执行函数
if __name__ == "__main__":
    long_summary()