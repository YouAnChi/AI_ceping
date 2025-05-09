import pandas as pd
import os
from datetime import datetime
import uuid

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

import os, time
import pandas as pd
from openai import OpenAI

def query_ai_model_with_excel(input_excel_path, key, url, model_name, get_first_token, prompt=None):
    """
    使用OpenAI模型处理Excel文件中的问题，并将结果直接写入原Excel文件。
    返回修改后的Excel文件路径。

    :param input_excel_path: 输入的Excel文件路径
    :param key: OpenAI API密钥
    :param url: OpenAI API URL
    :param model_name: 使用的OpenAI模型名称
    :param get_first_token: 是否获取首token
    :param prompt: 提示词（可选）
    :return: 修改后的Excel文件路径
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