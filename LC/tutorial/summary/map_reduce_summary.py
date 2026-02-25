from dotenv import load_dotenv
import os

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def long_summary():
    # 1. 加载API配置
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    # 2. 初始化模型
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    # 3. 读取完整文本（不再截取！）
    with open('wonderland.txt', 'r', encoding='utf-8') as file:
        text = file.read()

    print(f"=== 原始文本长度 ===")
    print(f"字符数：{len(text)}")
    # 计算token数
    num_tokens = llm.get_num_tokens(text)
    print(f"Token数：{num_tokens}")

    # 4. 将文本切分成多个文档块（关键步骤）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,  # 每个块约3000字符
        chunk_overlap=200,  # 块之间重叠200字符，保持上下文连贯
        length_function=len,
    )
    # 将文本切分成 字符串列表
    docs = text_splitter.create_documents([text])
    print(f"\n=== 文本切分结果 ===")
    print(f"切分成 {len(docs)} 个文档块")
    print(f"第一个块预览：{docs[0].page_content[:200]}...")

    # Map 阶段的 prompt（对每个块总结）
    map_template = """请总结以下文本片段，保留核心信息：
    {text}
    总结："""
    # Reduce 阶段的 prompt（合并所有总结）
    reduce_template = """以下是多个文本片段的总结，请将它们合并成一个完整的总结：
    {text}
    完整总结："""
    map_prompt = PromptTemplate.from_template(map_template)
    reduce_prompt = PromptTemplate.from_template(reduce_template)

    # 5. 使用 map_reduce 链进行总结
    # verbose=True 可以查看详细运行过程
    chain = load_summarize_chain(
        llm=llm,
        chain_type='map_reduce',
        map_prompt=map_prompt,
        combine_prompt=reduce_prompt,
        verbose=True
    )

    # 6. 执行总结（会自动处理所有文档块）
    print("\n=== 开始总结（Map-Reduce 模式）===")
    output = chain.run(docs)

    # 7. 打印最终总结结果
    print("\n=== 《爱丽丝梦游仙境》完整总结 ===")
    print(output)


if __name__ == "__main__":
    long_summary()