# retrieval_chain 的结构：
├─ retriever（检索器）
│  └─ 负责：根据问题检索相关文档
│
└─ combine_docs_chain（文档合并链）
   ├─ llm（语言模型）
   └─ prompt（提示词模板）
      └─ 负责：合并文档 + 生成答案


# retrieval_chain.invoke({"input": query}) 的工作流程：
retrieval_chain.invoke({"input": query})
    ↓
【步骤1】retriever 检索
    docs = retriever.invoke(query)
    # retriever 内部：
    #   1. 将 query 转换为向量
    #   2. 在向量数据库中搜索最相似的文档
    #   3. 返回最相关的 5 个文档：[doc1, doc2, doc3, doc4, doc5]
    ↓
【步骤2】构建参数字典
    params = {
        "input": query,        # 你传入的问题
        "context": [doc1, doc2, ...]      # 检索到的文档列表
    }
    ↓
【步骤3】调用 combine_docs_chain
    combine_docs_chain.invoke(params)
    ↓
【步骤4】combine_docs_chain 内部处理
    a. 合并 context 中的文档：
       context_text = 合并(docs[0].page_content, docs[1].page_content, ...)
    b. 填充 prompt 模板：
       final_prompt = prompt.format(
           context=context_text,  # 填充 {context}
           input=query            # 填充 {input}
       )
    ↓
【步骤5】发送给 LLM
    llm.invoke(final_prompt)
    ↓
【步骤6】返回结果
    {
        "answer": "LLM 生成的答案",
        "context": docs  # 保留原始文档列表
    }