# Summaries Of Short Text
import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
def summary():
    # 加载.env文件的环境变量
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    llm = ChatOpenAI(temperature=0,
                     model_name='gpt-3.5-turbo',
                     openai_api_key=openai_api_key,
                     openai_api_base=openai_base_url) # 初始化LLM模型

    confusing_text = """
       For the next 130 years, debate raged.
       Some scientists called Prototaxites a lichen, others a fungus, and still others clung to the notion that it was some kind of tree.
       “The problem is that when you look up close at the anatomy, it’s evocative of a lot of different things, but it’s diagnostic of nothing,” says Boyce, an associate professor in geophysical sciences and the Committee on Evolutionary Biology.
       “And it’s so damn big that when whenever someone says it’s something, everyone else’s hackles get up: ‘How could you have a lichen 20 feet tall?’”
       """

    # 创建模板（保留你的原有模板，仅优化格式）
    template = """
    %INSTRUCTIONS:
    Please summarize the following piece of text.
    Respond in a manner that a 5 year old would understand.
    
    %TEXT:
    {text}
    """

    # # from_messages是带角色的对话式Prompt，适合Chat模型的交互逻辑，规则和输入分工清晰；
    # # from_template是无角色的纯文本Prompt，适合简单场景，兼容性强但不够贴合Chat模型；
    prompt = ChatPromptTemplate.from_template(template)

    print("------- Prompt Begin -------")
    # 渲染模板
    messages = prompt.format_messages(text=confusing_text)
    # 打印格式化后的提示（用于调试）
    print(messages[0].content)
    print("------- Prompt End -------")

    # 新版调用方式（Chat模型用invoke + 解析输出）
    output = llm.invoke(messages)
    parser = StrOutputParser()  # 解析Chat模型的AIMessage为纯文本
    final_output = parser.invoke(output)

    # 打印总结结果
    print("\n------- Summary Result -------")
    print(final_output)

if __name__ == "__main__":
    summary()