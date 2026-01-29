"""
由于自然语言的不可预测性和可变性，评估LLM的输出是否正确有些困难，langchain 提供了一种方式帮助我们去解决这一难题。
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.evaluation import QAEvalChain
from langchain_text_splitters import RecursiveCharacterTextSplitter


def run_evaluation():
    # Load environment variables
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

    # Load document (ensure wonderland.txt exists and has content)
    file_path = 'wonderland.txt'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    loader = TextLoader(file_path, encoding='utf-8')
    doc = loader.load()

    print(f"Loaded {len(doc)} document(s) with {len(doc[0].page_content)} characters")

    # 将文本切分成多个文档块（关键步骤）
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=400)
    docs = text_splitter.split_documents(doc)       # 将长文本切分成多个小块，Document对象 / Document对象列表

    if not docs:
        print("No documents to process.")
        return

    avg_chars = sum(len(x.page_content) for x in docs) / len(docs)
    print(f"Split into {len(docs)} chunks (avg {avg_chars:.0f} chars each)")

    # 创建 Embeddings 和向量数据库
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_documents(docs, embeddings)
    print("向量数据库创建完成！")

    # 步骤一：定义测试数据
    question_answers = [
        {'question': "Which animal give alice a instruction?", 'except_answer': 'rabbit'},
        {'question': "What is the author of the book", 'except_answer': 'Lewis Carroll'}
    ]

    # 步骤二：创建 “问答链”
    # 问题 → retriever 检索相关文档 → 合并文档 + 问题 → LLM 生成答
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",                     # 将所有检索到的文档片段合并后传入模型
        retriever=docsearch.as_retriever(),     # 从向量数据库检索相关文档的接口
        input_key="question"                    # 指定输入字典中问题的字段名
    )
    # 生成预测
    print("\nGenerating predictions...")
    predictions = qa_chain.apply(question_answers)
    #   chain.apply作用：
    #   对于 question_answers 中的每个字典：
    #       1. 提取 'question' 字段
    #       2. 使用 retriever 检索相关文档
    #       3. 将检索到的文档 + 问题发给 LLM
    #       4. LLM 生成答案
    #       5. 返回格式：{'question': ..., 'result': '模型生成的答案', 'except_answer': ...}


    # 步骤三：评估预测，使用 “评估链” 评估预测是否与标准答案一致
    print("Evaluating results...")
    eval_chain = QAEvalChain.from_llm(llm)
    graded_outputs = eval_chain.evaluate(
        question_answers,           # 原始测试数据
        predictions,                # 模型预测结果
        question_key="question",    # 问题字段名
        prediction_key="result",    # 模型生成的答案
        answer_key='answer'         # 预期标准答案
    )
    # 输入：
    #    - question_answers（原始测试数据）
    #    - predictions（问答链的输出）
    # 处理：
    #    1.提取：问题、预测答案、标准答案
    #    2.构建评估 prompt：
    #        "问题：{question}
    #        标准答案：{answer}
    #        预测答案：{result}
    #        请评估预测是否正确“
    #    3.发送给 LLM 评估
    #    4.LLM 返回：CORRECT 或 INCORRECT

    # 显示结果
    for i, (pred, grade) in enumerate(zip(predictions, graded_outputs)):
        print(f"\n--- Question {i+1} ---")
        print(f"Q: {pred['question']}")
        print(f"Expected: {pred['answer']}")
        print(f"Actual: {pred['result'].strip()}")
        print(f"Grade: {grade['results']}")


if __name__ == '__main__':
    run_evaluation()
