import pandas as pd
import os, time, uuid
from datetime import datetime
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import numpy as np

def extract_column_to_new_excel(input_excel_path, column_letter, output_dir):
    """
    从指定的Excel文件中提取指定列的内容，并将其写入一个新的Excel文件中。
    新文件的名称是唯一的，并返回新文件的路径。

    :param input_excel_path: 输入的Excel文件路径
    :param column_letter: 需要提取的列的字母（如A、B、C等）
    :param output_dir: 提取后文件的保存目录
    :return: 新创建的Excel文件的路径
    """
    try:
        # 读取输入的Excel文件
        df = pd.read_excel(input_excel_path)

        # 将列字母转换为列索引（从0开始）
        column_index = ord(column_letter.upper()) - ord('A')

        # 检查列索引是否超出范围
        if column_index >= len(df.columns):
            raise ValueError(f"指定的列 '{column_letter}' 超出了Excel文件的列范围。")

        # 提取指定列的内容
        extracted_column = df.iloc[:, [column_index]]

        # 创建一个唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]  # 取UUID的前8位作为唯一标识
        output_file_name = f"extracted_{column_letter}_{timestamp}_{unique_id}.xlsx"
        # 文件存放路径
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file_path = os.path.join(output_dir, output_file_name)

        # 将提取的列写入新的Excel文件
        extracted_column.to_excel(output_file_path, index=False)

        print(f"新文件已创建，路径为: {output_file_path}")
        return output_file_path

    except Exception as e:
        print(f"发生错误: {e}")
        return None



def query_ai_model_with_excel(input_excel_path, key, url, model_name, get_first_token, prompt=None):
    """
    使用OpenAI模型处理Excel文件中的问题，并将结果直接写入原Excel文件。
    返回修改后的Excel文件路径。

    :param input_excel_path: 输入的Excel文件路径    用户上传
    :param key: OpenAI API密钥  用户输入
    :param url: OpenAI API URL  用户输入
    :param model_name: 使用的OpenAI模型名称 用户选择
    :param get_first_token: 是否获取首token 用户选择
    :param prompt: 提示词（可选）   用户输入
    :return: 修改后的Excel文件路径  用户下载
    """
    try:
        # 配置OpenAI API
        client = OpenAI(
            api_key=key,
            base_url=url
        )

        # 读取Excel文件
        df = pd.read_excel(input_excel_path)

        # 检查是否有足够的列
        if len(df.columns) < 1:
            raise ValueError("Excel文件中没有足够的列。")

        # 获取第一列的内容作为问题
        questions = df.iloc[:, 0].dropna().tolist()

        # 准备结果列
        if 'W_Response' not in df.columns:
            df['W_Response'] = None
        if get_first_token and 'First_Token' not in df.columns:
            df['First_Token'] = None



        # 循环提问并获取结果
        for index, question in enumerate(questions):
            # 记录请求发送时间
            start_time = time.time()
            # 初始化标志变量
            first_token_received = False
            first_token_time = None

            messages = [
                {"role": "user", "content": question}
            ]
            if prompt:
                messages.insert(0, {"role": "system", "content": prompt})

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True  # 启用流式输出
            )

            # 初始化变量用于存储完整响应
            full_response = ""

            # 逐步接收并处理响应
            for chunk in response:
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.content:
                    if not first_token_received:
                        # 假设第一个 token 是在第一次非空行中返回的
                        first_token_time = time.time()
                        first_token_received = True
                    full_response += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end="", flush=True)
                if chunk.choices[0].delta.reasoning_content:
                    full_response += chunk.choices[0].delta.reasoning_content
                    print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
            print()
            # 将完整响应写入DataFrame
            df.at[index, 'W_Response'] = full_response

            # 如果需要获取首token
            if get_first_token:
                # 获取首token
                first_token = first_token_time - start_time
                print(first_token)
                df.at[index, 'First_Token'] = first_token

        # 保存修改后的Excel文件
        df.to_excel(input_excel_path, index=False)

        print(f"结果已保存到原文件: {input_excel_path}")
        return input_excel_path

    except Exception as e:
        print(f"发生错误: {e}")
        return None


def convert_seconds(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = round(seconds % 60, 2)
    return hours, minutes, seconds

def excel_ragas(input_excel_path):
    """
    对excel中的B列与C列进行ASS值比较，生成比较值，并写入excel中。

    :param input_excel_path: 输入的Excel文件路径
    """

    # 读取Excel文件
    df = pd.read_excel(input_excel_path)

    # 检查是否有足够的列
    if len(df.columns) < 1:
        raise ValueError("Excel文件中没有足够的列。")

    # 获取第二列与第三列的内容作为问题
    questions_one = df.iloc[:, 1].dropna().tolist()
    questions_two = df.iloc[:, 2].dropna().tolist()

    # 准备结果列
    if 'ASS值' not in df.columns:
        df['ASS值'] = None

    questions_len = len(questions_one)
    
    # 批量数据进行ASS对比
    print('加载acge_text_embedding向量模型，请耐心等待。。。')
    model = SentenceTransformer(r'C:\Users\admin\.cache\modelscope\hub\yangjhchs\acge_text_embedding')
    start_time = time.time()
    for index, question in enumerate(questions_one):
        reference_answer = question
        generated_answer = questions_two[index]

        # 计算两个答案的嵌入向量
        embedding_1 = np.array(model.encode(reference_answer))
        embedding_2 = np.array(model.encode(generated_answer))

        print(f'进行ASS相似度计算，共{questions_len}条数据，计算第{index+1}条，请耐心等待。。。')

        # 计算余弦相似度
        norms_1 = np.linalg.norm(embedding_1, keepdims=True)
        norms_2 = np.linalg.norm(embedding_2, keepdims=True)
        embedding_1_normalized = embedding_1 / norms_1
        embedding_2_normalized = embedding_2 / norms_2
        similarity = embedding_1_normalized @ embedding_2_normalized.T
        score = similarity.flatten()
        similarity_score = score.tolist()[0]

        # 将完整响应写入DataFrame
        df.at[index, 'ASS值'] = similarity_score

    # 计算耗时
    first_token_time = time.time()
    first_token = first_token_time - start_time
    hours, minutes, seconds = convert_seconds(first_token)
    print(f'ASS相似度计算完成，共耗时：{hours}小时{minutes}分钟{seconds}秒')

    # 保存修改后的Excel文件
    df.to_excel(input_excel_path, index=False)

    print(f"结果已保存到原文件: {input_excel_path}")

# excel_ragas('产品说明书1_AI生成的用例.xlsx')


from rouge import Rouge

def excel_rouge(input_excel_path,rouge_index='ROUGE-1'):
    """
    rouge 库在处理中文文本时可能会有一些问题，因为它默认是为英文设计的。
    在 ROUGE 评估中，Precision（精确率）、Recall（召回率） 和 F1 Score（F1 分数） 是三个重要的指标，它们分别从不同的角度衡量生成文本与参考文本的相似度。
    Precision（精确率）：精确率反映了生成文本中有多大比例的内容是与参考文本匹配的。
    Recall（召回率）：召回率反映了参考文本中有多少内容被生成文本覆盖。
    F1 Score（F1 分数）：F1 分数是一个综合指标，平衡了精确率和召回率。它既考虑了生成文本的质量，也考虑了生成文本的完整性。

    :param input_excel_path: 输入的Excel文件路径
    :param index: 指标，可选项为ROUGE-1、ROUGE-2、ROUGE-L，默认为ROUGE-1
    """
    # 读取Excel文件
    df = pd.read_excel(input_excel_path)

    # 检查是否有足够的列
    if len(df.columns) < 1:
        raise ValueError("Excel文件中没有足够的列。")

    # 获取第二列与第三列的内容作为问题
    questions_one = df.iloc[:, 1].dropna().tolist()
    questions_two = df.iloc[:, 2].dropna().tolist()

    # 准备结果列
    if rouge_index not in df.columns:
        df[rouge_index] = None

    questions_len = len(questions_one)

    # 初始化 ROUGE 计算器
    rouge = Rouge()
    print('加载ROUGE评估，请耐心等待。。。')

    start_time = time.time()
    for index, question in enumerate(questions_one):

        reference_answer = question
        generated_answer = questions_two[index]

        print(f'进行ROUGE评估，共{questions_len}条数据，计算第{index+1}条，请耐心等待。。。')

        # 计算 ROUGE 指标
        scores = rouge.get_scores(reference_answer, generated_answer)

        if rouge_index == 'ROUGE-1':
            # 输出评分
            print("ROUGE-1:")
            print("F1 Score: ", scores[0]['rouge-1']['f'])
            print("Recall: ", scores[0]['rouge-1']['r'])
            print("Precision: ", scores[0]['rouge-1']['p'])
            rouge_F1 = scores[0]['rouge-1']['f']
        elif rouge_index == 'ROUGE-2':
            print("\nROUGE-2:")
            print("F1 Score: ", scores[0]['rouge-2']['f'])
            print("Recall: ", scores[0]['rouge-2']['r'])
            print("Precision: ", scores[0]['rouge-2']['p'])
            rouge_F1 = scores[0]['rouge-2']['f']
        elif rouge_index == 'ROUGE-L':
            print("\nROUGE-L:")
            print("F1 Score: ", scores[0]['rouge-l']['f'])
            print("Recall: ", scores[0]['rouge-l']['r'])
            print("Precision: ", scores[0]['rouge-l']['p'])
            rouge_F1 = scores[0]['rouge-l']['f']

        # 将完整响应写入DataFrame
        df.at[index, rouge_index] = rouge_F1

    # 计算耗时
    first_token_time = time.time()
    first_token = first_token_time - start_time
    hours, minutes, seconds = convert_seconds(first_token)
    print(f'ROUGE相似度计算完成，共耗时：{hours}小时{minutes}分钟{seconds}秒')

    # 保存修改后的Excel文件
    df.to_excel(input_excel_path, index=False)

    print(f"结果已保存到原文件: {input_excel_path}")
# excel_rouge('产品说明书1_AI生成的用例.xlsx','ROUGE-1')

import jieba

def calculate_f1_chinese(input_excel_path):
    """
    计算两段中文文本之间的F1值，使用jieba进行分词。

    :param input_excel_path: 输入的Excel文件路径
    """
    # 读取Excel文件
    df = pd.read_excel(input_excel_path)

    # 检查是否有足够的列
    if len(df.columns) < 1:
        raise ValueError("Excel文件中没有足够的列。")

    # 获取第二列与第三列的内容作为问题
    questions_one = df.iloc[:, 1].dropna().tolist()
    questions_two = df.iloc[:, 2].dropna().tolist()

    # 准备结果列
    if 'F1值' not in df.columns:
        df['F1值'] = None

    questions_len = len(questions_one)

    # 初始化 F1值 计算器
    print('加载F1值评估，请耐心等待。。。')

    start_time = time.time()
    for index, question in enumerate(questions_one):

        # 使用jieba进行分词
        reference_answer = set(jieba.cut(question))
        generated_answer = set(jieba.cut(questions_two[index]))

        print(f'进行F1值评估，共{questions_len}条数据，计算第{index+1}条，请耐心等待。。。')

        # 计算交集和并集
        intersection = reference_answer.intersection(generated_answer)
        union = reference_answer.union(generated_answer)

        # 计算精确率和召回率
        precision = len(intersection) / len(generated_answer) if generated_answer else 0
        recall = len(intersection) / len(reference_answer) if reference_answer else 0

        # 计算F1值
        if precision + recall == 0:
            f1 = 0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)

        print(f1)

        # 将完整响应写入DataFrame
        df.at[index, 'F1值'] = f1

    # 计算耗时
    first_token_time = time.time()
    first_token = first_token_time - start_time
    hours, minutes, seconds = convert_seconds(first_token)
    print(f'ROUGE相似度计算完成，共耗时：{hours}小时{minutes}分钟{seconds}秒')

    # 保存修改后的Excel文件
    df.to_excel(input_excel_path, index=False)

    print(f"结果已保存到原文件: {input_excel_path}")

# calculate_f1_chinese('产品说明书1_AI生成的用例.xlsx')