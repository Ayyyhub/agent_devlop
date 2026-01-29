import os
from langchain_community.document_loaders import TextLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

"""整体架构：RAG（检索增强生成）"""
def long_answer():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    # 1. 加载文本文件
    loader = TextLoader('wonderland.txt', encoding='utf-8')
    doc = loader.load()  # doc 是一个 Document 对象列表
    print(f"You have {len(doc)} document")
    print(f"You have {len(doc[0].page_content)} characters in that document")

    # 2. 切分文本（关键步骤！）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,  # 每个块3000字符
        chunk_overlap=400,  # 相邻块重叠400字符（保持上下文连贯）
        length_function = len,  # 用len函数计算文本，超过 CHUNK_SIZE 就按separators分割
        separators = ["\n\n", "\n", " ", ""]  # 代码按行和空行切分更合理
    )
    docs = text_splitter.split_documents(doc)  # 将长文本切分成多个小块，Document对象 / Document对象列表

    # 3.获取字符的总数，以便可以计算平均值
    num_total_characters = sum([len(x.page_content) for x in docs])
    print(f"Now you have {len(docs)} documents that have an average of {num_total_characters / len(docs):,.0f} characters (smaller pieces)")


    # ====== 创建向量数据库 =======
    # 步骤一：初始化 Embedding 模型,设置 embedding 引擎（需要配置 base_url）
    embeddings = OpenAIEmbeddings(
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )
    # # 也可以使用本地模型，但是需要自己实现向量化服务（比如使用huggingface的transformers库）
    # # 第一次运行会下载模型到本地，之后就不需要网络了
    # from langchain_community.embeddings import HuggingFaceEmbeddings
    # # 使用本地模型，不需要 API
    # embeddings = HuggingFaceEmbeddings(
    #     model_name="sentence-transformers/all-MiniLM-L6-v2"
    # )
    # 步骤二：Embed 向量化文档，然后使用 FAISS（Facebook 的向量数据库） 存储
    # FAISS 不仅存储向量，还存储向量与原始文本的映射关系
    print("\n正在创建向量数据库（这可能需要一些时间）...")
    docsearch = FAISS.from_documents(docs, embeddings)
    print("向量数据库创建完成！")
    # 这一步发生了什么：
        #   a. FAISS 调用 embeddings.embed_documents(docs)
        #   b. embeddings 向 OpenAI API 发送请求：将每个文档块转换为向量 （问：为什么需要调用 OpenAI API？答：因为OpenAI API提供了向量化服务，文本转向量需要理解语义，这需要模型能力！）
        #   c. OpenAI 返回向量（比如 [0.1, 0.3, -0.2, ...]）
        #   d. FAISS 接收这些向量，存储到本地


    # ====== 创建检索和问答链 =======
    # 1. 创建检索器
    retriever = docsearch.as_retriever()
    # 作用：根据问题，从向量数据库中找出最相关的文档片段

    # 2. 创建提示词模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Use the following pieces of context to answer the question...\n\n{context}"),
        ("user", "{input}")
    ])
    # 作用：定义如何将检索到的文档和问题组合成提示词

    # 3. 创建文档链
    document_chain = create_stuff_documents_chain(llm, prompt)
    # 作用：将多个文档片段"塞"进提示词，让模型基于这些上下文回答问题

    # 4. 创建检索链
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    # 作用：组合检索和生成，形成完整的问答流程


    # ====== 执行查询 =======
    # query = "What does the author describe the Alice following with?"
    user_input=input("请输入问题：")
    query=user_input if user_input else "What does the author describe the Alice following with?"
    print(f"\n问题：{query}")
    print("\n正在检索相关文档并生成答案...")

    result = retrieval_chain.invoke({"input": query})

    # 打印答案
    print("\n" + "=" * 50)
    print("答案：")
    print("=" * 50)
    print(result["answer"])

    # 可选：打印检索到的相关文档片段
    print("\n" + "=" * 50)
    print(f"检索到的相关文档片段数量：{len(result['context'])}")
    print("=" * 50)


if __name__ == '__main__':
    long_answer()