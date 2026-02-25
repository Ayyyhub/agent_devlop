"""
使用 LangChain APIChain 与 REST API 交互

功能说明：
1. 提供 API 文档给 LLM
2. LLM 根据用户问题自动选择合适的 API 端点
3. 调用 API 并返回结果

注意：在 LangChain 0.3.x 中，APIChain 可能需要从 langchain-experimental 导入
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 尝试从不同位置导入 APIChain（兼容不同版本）
try:
    from langchain_experimental.utilities import PythonREPL
    from langchain_experimental.tools import PythonREPLTool
    # 在 0.3.x 中，APIChain 可能在 langchain_community 或 langchain_experimental
    try:
        from langchain_community.utilities import APIChain
    except ImportError:
        try:
            from langchain_experimental.utilities import APIChain
        except ImportError:
            from langchain.chains import APIChain
except ImportError:
    from langchain.chains import APIChain


def query_country_api():
    """查询国家信息 API"""
    # 加载环境变量
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    # 初始化 LLM
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    # API 文档
    api_docs = """
BASE URL: https://restcountries.com/

API Documentation:

The API endpoint /v3.1/name/{name} is used to find information about a country. 
All URL parameters are listed below:
    - name: Name of country - Examples: italy, france, germany

The API endpoint /v3.1/currency/{currency} is used to find information about countries by currency. 
All URL parameters are listed below:
    - currency: 3 letter currency code - Examples: USD, EUR, COP

Response format: JSON
"""

    try:
        # 在 LangChain 0.3.x 中，limit_to_domains 可能需要使用不同的格式
        # 根据错误信息，它检查完整 URL，所以尝试使用 URL 前缀匹配

        # 方案1：尝试使用包含协议和路径的格式
        try:
            api_chain = APIChain.from_llm_and_api_docs(
                llm=llm,
                api_docs=api_docs,
                limit_to_domains=["https://restcountries.com"],  # 使用完整 URL
                verbose=True
            )

        # 方案2：尝试只使用域名
        except ValueError as e1:
            try:
                api_chain = APIChain.from_llm_and_api_docs(
                    llm=llm,
                    api_docs=api_docs,
                    limit_to_domains=["restcountries.com"],
                    verbose=True
                )

            # 方案3：如果都失败，可能是版本 bug，暂时不使用限制（仅测试）
            except ValueError as e2:
                print("警告：limit_to_domains 配置失败，这可能是 LangChain 0.3.x 的已知问题")
                print("错误信息1：", str(e1))
                print("错误信息2：", str(e2))
                print("临时解决方案：不使用域名限制（仅用于测试）\n")
                api_chain = APIChain.from_llm_and_api_docs(
                    llm=llm,
                    api_docs=api_docs,
                    verbose=True
                )

        # 示例查询
        query = "Can you tell me information about france?"

        print("=" * 60)
        print("API 查询示例")
        print("=" * 60)
        print(f"问题：{query}\n")
        print("正在调用 API...\n")

        # 执行查询（使用 invoke 替代已弃用的 run）
        result = api_chain.invoke({"question": query})

        # 处理返回结果（可能是字典或字符串）
        if isinstance(result, dict):
            answer = result.get("output", result.get("answer", str(result)))
        else:
            answer = result

        print("\n" + "=" * 60)
        print("查询结果：")
        print("=" * 60)
        print(answer)

        return result

    except Exception as e:
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()
        print("\n可能的原因：")
        print("1. APIChain 在 LangChain 0.3.x 中可能有 API 变化")
        print("2. 需要从 langchain-experimental 或 langchain-community 导入")
        print("3. limit_to_domains 参数的行为可能已改变")
        print("\n建议：")
        print("1. 检查 APIChain 的正确导入路径")
        print("2. 查看 LangChain 0.3.x 的文档")
        print("3. 考虑使用 LangChain 的工具调用功能替代 APIChain")
        return None


def interactive_api_query():
    """交互式 API 查询模式"""
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    api_docs = """
BASE URL: https://restcountries.com/

API Documentation:

The API endpoint /v3.1/name/{name} is used to find information about a country. 
    - name: Name of country - Examples: italy, france, germany

The API endpoint /v3.1/currency/{currency} is used to find information about countries by currency. 
    - currency: 3 letter currency code - Examples: USD, EUR, COP
"""

    try:
        # 尝试创建 API 链（使用相同的错误处理逻辑）
        try:
            api_chain = APIChain.from_llm_and_api_docs(
                llm=llm,
                api_docs=api_docs,
                limit_to_domains=["restcountries.com"],
                verbose=False
            )
        except ValueError:
            api_chain = APIChain.from_llm_and_api_docs(
                llm=llm,
                api_docs=api_docs,
                verbose=False
            )

        print("\n" + "=" * 60)
        print("交互式 API 查询（输入 'exit' 退出）")
        print("=" * 60)
        print("示例问题：")
        print("  - Can you tell me information about france?")
        print("  - What countries use USD currency?")
        print("  - Tell me about Italy")

        while True:
            query = input("\n请输入问题：").strip()

            if query.lower() in ['exit', 'quit', '退出']:
                print("再见！")
                break

            if not query:
                continue

            try:
                result = api_chain.invoke({"question": query})
                answer = result.get("output", result) if isinstance(result, dict) else result
                print(f"\n答案：{answer}")
            except Exception as e:
                print(f"查询出错：{e}")
                
    except Exception as e:
        print(f"初始化失败：{e}")


if __name__ == '__main__':
    # 方式1：执行预设查询
    query_country_api()
    
    # 方式2：交互式查询（取消注释以启用）
    # interactive_api_query()