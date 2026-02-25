"""
深度研究 Agent - Deep Research Agent

"""

from task_planner import WebSearchPlan, WebSearchItem, planner_chain
from web_searcher import search_agent
from txt_writer import ReportData, writer_chain

# 生成关键词规划
def plan_searches(query: str) -> WebSearchPlan:
    result = planner_chain.invoke({'query': query})
    return result

# 执行单个搜索项的网络搜索
def search(item: WebSearchItem) -> str | None:
    try:
        final_query = f"Search Item: {item.query}\nReason for searching: {item.reason}"
        result = search_agent.invoke({"messages":[
            {
                "role": "user",
                "content": final_query
            }
        ]})
        return str(result['messages'][-1].content)
    except Exception:
        return None

# 批量执行所有搜索项
def perform_searches(search_plan: WebSearchPlan):
    results = []
    # 遍历 WebSearchPlan 中的每个 WebSearchItem
    for item in search_plan.searches:
        # search 执行搜索
        result = search(item)
        if result is not None:
            results.append(result)
    return results

# 将搜索结果整合为最终报告
def write_report(query: str, search_results) -> ReportData:
    summary=''
    for search_result in search_results:
        summary += search_result
    final_query = f'Original query: {query}\n Summarized search results: {summary}'
    result = writer_chain.invoke({
        'query': final_query
    })
    return result

# 串联以上流程函数
def deepresearch(query: str) -> ReportData:
    '''
    输入一个研究主题，自动完成搜索规划、搜索和写报告
    返回最终的ReportData对象，就是一个markdown的格式完整的研究报告文档
    '''
    # 规划搜索关键词
    search_plan = plan_searches(query)
    # 执行所有搜索
    search_results = perform_searches(search_plan)
    # 生成最终报告
    report = write_report(query, search_results)
    print(report.markdown_report)
    return report


def main():
    """
    程序入口函数
    可以通过命令行参数传入查询，或者使用默认查询
    """
    import sys
    
    # 如果命令行有参数，使用第一个参数作为查询
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        # 默认查询示例
        query = '请问你对AI+教育有何看法'
    
    print(f"开始深度研究，查询主题：{query}")
    print("=" * 50)
    
    try:
        report = deepresearch(query)
        print("=" * 50)
        print("研究报告生成完成！")
        return report
    except Exception as e:
        print(f"发生错误：{e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
