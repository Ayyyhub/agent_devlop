import os
from typing import List

# 第三方库导入（按功能分组，提升可读性）
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# ===================== 配置项（集中管理，方便修改）=====================
# 环境变量与API配置
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
# 文档路径配置
ROOT_DIR = '/'  # 代码仓库根目录（修改为你的代码目录路径）
VECTOR_STORE_SAVE_PATH = "faiss_vector_store"  # 向量库保存路径

# 支持的代码文件扩展名（可根据需要添加）
CODE_FILE_EXTENSIONS = {
    '.py',      # Python
    '.js',      # JavaScript
    '.ts',      # TypeScript
    '.java',    # Java
    '.cpp',     # C++
    '.c',       # C
    '.go',      # Go
    '.rs',      # Rust
    '.php',     # PHP
    '.rb',      # Ruby
    '.swift',   # Swift
    '.kt',      # Kotlin
    '.scala',   # Scala
    '.sh',      # Shell脚本
    '.sql',     # SQL
    '.html',    # HTML
    '.css',     # CSS
    '.xml',     # XML
    '.json',    # JSON
    '.yaml',    # YAML
    '.yml',     # YAML
    '.md',      # Markdown（文档）
    '.txt',     # 文本文件（README等）
}
# 模型与切分器配置
LLM_MODEL_NAME = "gpt-3.5-turbo"
LLM_TEMPERATURE = 0
CHUNK_SIZE = 1000  # 文本块大小
CHUNK_OVERLAP = 100  # 块重叠字符数
# 默认查询配置
DEFAULT_QUERIES = [
    
    "What function do I use if I want to find the most similar item in a list of items?",
    "Can you write the code to use the process.extractOne() function? Only respond with code. No other text or explanation"
]


def validate_config() -> None:
    """校验关键配置（比如API密钥），提前发现问题"""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY 未配置！请检查.env文件")
    if not os.path.exists(ROOT_DIR):
        raise FileNotFoundError(f"文档根目录不存在：{ROOT_DIR}")
    print("配置校验通过")


def load_and_split_documents(root_dir: str) -> List[Document]:
    """
    加载指定目录下的所有代码文件，并按规则切分
    :param root_dir: 代码仓库根目录
    :return: 切分后的Document对象列表
    """
    # 配置文本切分器（针对代码优化）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,                # 用len函数计算文本，超过 CHUNK_SIZE 就按separators分割
        separators=["\n\n", "\n", " ", ""]  # 代码按行和空行切分更合理
    )

    docs = []
    loaded_files = 0
    failed_files = []
    file_type_count = {}  # 统计各类型文件数量

    # 需要忽略的目录（避免加载不必要的文件）
    ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 
                   'env', '.idea', '.vscode', 'dist', 'build', '.pytest_cache'}

    # 遍历目录加载代码文件
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 过滤掉需要忽略的目录
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        
        for filename in filenames:
            # 获取文件扩展名
            _, ext = os.path.splitext(filename)
            
            # 只处理支持的代码文件类型
            if ext.lower() not in CODE_FILE_EXTENSIONS:
                continue

            file_path = os.path.join(dirpath, filename)
            
            # 跳过隐藏文件
            if filename.startswith('.'):
                continue
            
            try:
                loader = TextLoader(file_path, encoding="utf-8")
                # 加载文件内容
                raw_docs = loader.load()
                
                # 为每个文档添加文件路径元数据（方便追踪来源）
                for doc in raw_docs:
                    doc.metadata['source_file'] = file_path
                    doc.metadata['file_type'] = ext
                    doc.metadata['file_name'] = filename
                
                # 切分文档
                split_docs = text_splitter.split_documents(raw_docs)        # 将长文本切分成多个小块，Document对象 / Document对象列表
                docs.extend(split_docs)
                loaded_files += 1
                
                # 统计文件类型
                file_type_count[ext] = file_type_count.get(ext, 0) + 1
                
                print(f"成功加载：{file_path}（切分后块数：{len(split_docs)}）")
            except UnicodeDecodeError:
                # 二进制文件或编码问题，跳过
                failed_files.append((file_path, "编码错误（可能是二进制文件）"))
                print(f"跳过文件（编码错误）：{file_path}")
            except Exception as e:
                failed_files.append((file_path, str(e)))
                print(f"加载文件失败：{file_path}，错误：{e}")

    # 打印加载统计信息
    print(f"文件加载完成 | 成功加载：{loaded_files}个 | 加载失败：{len(failed_files)}个 | 最终文档块数：{len(docs)}")
    
    # 打印文件类型统计
    if file_type_count:
        print(f"文件类型统计：{dict(sorted(file_type_count.items(), key=lambda x: x[1], reverse=True))}")
    
    if failed_files:
        print(f"失败文件列表（前10个）：{failed_files[:10]}")

    # 验证加载结果
    if not docs:
        raise ValueError(f"未加载到任何代码文件！请检查目录 {root_dir} 下是否有支持的代码文件。\n"
                        f"支持的扩展名：{', '.join(sorted(CODE_FILE_EXTENSIONS))}")

    # 打印第一个文档的预览
    print(f"\n------ 代码预览（前300字符）------\n{docs[0].page_content[:300]}")
    print(f"来源文件：{docs[0].metadata.get('source_file', 'Unknown')}")
    return docs


def build_or_load_vectorstore(docs: List[Document], save_path: str) -> FAISS:
    """
    构建向量库（如果已保存则加载，提升重复运行效率）
    :param docs: 切分后的Document列表
    :param save_path: 向量库保存路径
    :return: FAISS向量库实例
    """
    embeddings = OpenAIEmbeddings(
        disallowed_special=(),              # 不禁止任何特殊标记 / 特殊字符序列，允许你的文本中包含所有类型的特殊字符 / 标记
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_BASE_URL
    )

    # 优先加载已保存的向量库
    if os.path.exists(save_path):
        print(f"加载已保存的向量库：{save_path}")
        # 加载向量库 FAISS
        vector_store = FAISS.load_local(
            save_path,
            embeddings,
            allow_dangerous_deserialization=True  # 本地使用安全，生产环境需谨慎
        )
    else:
        print("构建新的向量库...")
        vector_store = FAISS.from_documents(docs, embeddings)

        # 保存向量库到本地，避免重复构建
        # index.faiss：向量索引
        # index.pkl：映射关系
        vector_store.save_local(save_path)
        print(f"向量库已保存至：{save_path}")

    return vector_store


def build_rag_chain(vector_store: FAISS) -> create_retrieval_chain:
    """
    构建新版RAG链（替代旧版RetrievalQA，符合LangChain最佳实践）
    :param vector_store: FAISS向量库
    :return: 可调用的RAG链
    """
    # 初始化LLM（参数集中管理）
    llm = ChatOpenAI(
        temperature=LLM_TEMPERATURE,
        model_name=LLM_MODEL_NAME,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_BASE_URL
    )

    # 优化Prompt（针对代码理解任务）
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的代码理解助手，基于提供的代码库内容回答问题。

        重要规则：
        1. 只能基于提供的代码上下文回答问题
        2. 如果代码上下文中没有相关信息，必须明确说明"未找到相关信息"，不要基于自己的知识生成答案
        3. 不要编造或猜测代码，只使用上下文中实际存在的代码
        
        要求：
        1. 准确理解代码逻辑、函数功能、类结构等；
        2. 代码类问题只返回可运行的代码，无额外解释（除非明确要求解释）；
        3. 引用代码时，说明来源文件路径（如果上下文中有提供）；
        4. 如果代码库中没有相关信息，明确说明"未找到相关信息"（这是最重要的！）；
        5. 代码示例要完整，包含必要的导入语句和依赖。"""),

        ("human", """基于以下代码上下文回答问题：
        
        代码上下文：
        {context}
        
        问题：{input}
        
        注意：如果代码上下文中没有相关信息，请明确说明"未找到相关信息"。""")
    ])

    # 创建文档合并链（新版API）
    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    # 作用：这个链会接收 {"input": ..., "context": [...]}
    #       然后将 context 中的文档合并，填充到 prompt 的 {context} 位置

    # 把你构建好的向量数据库（vector_store）转换成一个 “检索器（retriever）” 对象，并指定检索规则 —— 从向量库中检索与查询最相似的前 5 个文本片段。
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    # 作用：根据问题检索相关文档

##### 【core】
    # 创建检索链（新版API）
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
    # 作用：组合检索和生成，形成完整流程

    print("RAG链构建完成")
    return retrieval_chain


def run_rag_query(retrieval_chain, query: str) -> str:
    """
    执行RAG查询，返回格式化后的结果
    :param retrieval_chain: 构建好的RAG链
    :param query: 用户查询
    :return: 回答文本
    """
    print(f"执行查询：{query}")
    try:
        # 调用新版链（返回结构更清晰）
        # 具体实现流程可查看README.txt
        response = retrieval_chain.invoke({"input": query})
        
        # 打印检索到的文档内容（用于调试和验证）
        print(f"\n检索到相关文档数：{len(response['context'])}")
        print("\n" + "=" * 60)
        print("检索到的文档内容：")
        print("=" * 60)
        for i, doc in enumerate(response['context'], 1):
            print(f"\n--- 文档 {i} ---")
            print(f"来源文件：{doc.metadata.get('source_file', 'Unknown')}")
            print(f"文件类型：{doc.metadata.get('file_type', 'Unknown')}")
            print(f"内容预览（前300字符）：")
            print(doc.page_content[:300])
            print("...")
        print("=" * 60 + "\n")
        
        # 提取核心回答（context是检索到的文档，answer是最终回答）
        answer = response["answer"].strip()
        return answer
    except Exception as e:
        print(f"查询执行失败：{e}")
        return f"查询失败：{str(e)}"


# ===================== 主函数（入口逻辑，清晰可控）=====================
def main():
    try:
        # 1. 校验配置
        validate_config()

        # 2. 加载并切分文档
        docs = load_and_split_documents(ROOT_DIR)

        # 3. 构建/加载向量库
        vector_store = build_or_load_vectorstore(docs, VECTOR_STORE_SAVE_PATH)

        # 4. 构建RAG链
        retrieval_chain = build_rag_chain(vector_store)

        # 5. 执行默认查询
        for idx, query in enumerate(DEFAULT_QUERIES, 1):
            print(f"\n========== 执行第{idx}个查询 ==========")
            answer = run_rag_query(retrieval_chain, query)
            print(f"\n查询：{query}\n回答：\n{answer}\n" + "=" * 50)

    except Exception as e:
        import traceback
        print(f"程序执行失败：{e}")
        traceback.print_exc()
        raise


# ===================== 程序入口 =====================
if __name__ == "__main__":
    main()