"""
使用自然语言查询 SQLite 数据库（旧金山树木数据集）

功能说明：
1. 连接 SQLite 数据库
2. 使用自然语言提问（如 "How many Species of trees are there?"）
3. LLM 自动将问题转换为 SQL 查询
4. 执行 SQL 并返回自然语言答案

注意：需要确保数据库文件存在：data/San_Francisco_Trees.db
"""
import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_experimental.sql import SQLDatabaseChain


def query_database():
    """使用自然语言查询数据库"""
    # 加载环境变量
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    # 初始化 LLM 模型
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    # 连接 SQLite 数据库
    sqlite_db_path = 'data/San_Francisco_Trees.db'

    # 检查数据库文件是否存在
    if not os.path.exists(sqlite_db_path):
        print(f"错误：找不到数据库文件 {sqlite_db_path}")
        print("请确保数据库文件存在于指定路径。")
        return

    try:
        # 创建数据库连接
        db = SQLDatabase.from_uri(f"sqlite:///{sqlite_db_path}")

        # 显示数据库信息（可选）
        print("=" * 60)
        print("数据库信息：")
        print("=" * 60)
        print(f"数据库路径：{sqlite_db_path}")
        print(f"数据库表：{db.get_usable_table_names()}")
        print()

        # 创建 SQL 数据库链
        # 这个链会自动：自然语言 → SQL → 执行 → 自然语言答案
        db_chain = SQLDatabaseChain.from_llm(
            llm=llm,
            db=db,
            verbose=True  # 显示详细的执行过程
        )

        # 示例查询
        query = "How many Species of trees are there in San Francisco?"

        print("=" * 60)
        print("查询问题：")
        print("=" * 60)
        print(query)
        print()
        print("=" * 60)
        print("查询结果：")
        print("=" * 60)

        # 执行查询
        result = db_chain.run(query)

        print(result)
        print("=" * 60)

        return result

    except Exception as e:
        print(f"错误：{e}")
        print("\n可能的原因：")
        print("1. 数据库文件不存在或路径错误")
        print("2. 数据库文件损坏")
        print("3. API 配置错误")
        return None


def interactive_query():
    """交互式查询模式"""
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    sqlite_db_path = 'data/San_Francisco_Trees.db'

    if not os.path.exists(sqlite_db_path):
        print(f"错误：找不到数据库文件 {sqlite_db_path}")
        return

    db = SQLDatabase.from_uri(f"sqlite:///{sqlite_db_path}")
    db_chain = SQLDatabaseChain.from_llm(llm=llm, db=db, verbose=False)

    print("\n" + "=" * 60)
    print("交互式数据库查询（输入 'exit' 退出）")
    print("=" * 60)

    while True:
        query = input("\n请输入问题：").strip()

        if query.lower() in ['exit', 'quit', '退出']:
            print("再见！")
            break

        if not query:
            continue

        try:
            result = db_chain.run(query)
            print(f"\n答案：{result}")
        except Exception as e:
            print(f"查询出错：{e}")


if __name__ == '__main__':
    # 方式1：执行预设查询
    query_database()

    # 方式2：交互式查询（取消注释以启用）
    # interactive_query()