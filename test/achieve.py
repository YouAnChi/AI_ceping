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



def query_ai_model_with_excel(df_input, question_column_name, output_response_column_name, output_first_token_column_name, key, url, model_name, get_first_token, prompt=None):
    """
    使用OpenAI模型处理DataFrame中的问题，并将结果添加到DataFrame中。

    :param df_input: 输入的DataFrame，包含问题列
    :param question_column_name: 问题列的名称
    :param output_response_column_name: 模型响应将写入的列名
    :param output_first_token_column_name: 首token时间将写入的列名
    :param key: OpenAI API密钥
    :param url: OpenAI API URL
    :param model_name: 使用的OpenAI模型名称
    :param get_first_token: 是否获取首token
    :param prompt: 提示词（可选）
    :return: 修改后的DataFrame副本，包含模型响应和首token时间
    """
    df_output = df_input.copy()
    try:
        client = OpenAI(api_key=key, base_url=url)
        questions = df_output[question_column_name].dropna().tolist()

        responses_list = []
        first_tokens_list = []

        for index, question_text in enumerate(questions):
            start_time = time.time()
            first_token_received = False
            first_token_time_val = None

            messages = [{"role": "user", "content": str(question_text)}]
            if prompt:
                messages.insert(0, {"role": "system", "content": prompt})

            response_stream = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True
            )

            full_response = ""
            for chunk in response_stream:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content
                reasoning_content = chunk.choices[0].delta.reasoning_content
                
                if content:
                    if not first_token_received:
                        first_token_time_val = time.time() - start_time
                        first_token_received = True
                    full_response += content
                    # print(content, end="", flush=True) # Optional: for live printing
                if reasoning_content:
                    full_response += reasoning_content
                    # print(reasoning_content, end="", flush=True) # Optional: for live printing
            # print() # Optional: for live printing

            responses_list.append(full_response)
            if get_first_token:
                first_tokens_list.append(first_token_time_val)
            else:
                first_tokens_list.append(None) # Keep lists aligned

        df_output[output_response_column_name] = pd.Series(responses_list, index=df_output.head(len(questions)).index)
        if get_first_token:
            df_output[output_first_token_column_name] = pd.Series(first_tokens_list, index=df_output.head(len(questions)).index)

        return df_output

    except Exception as e:
        print(f"发生错误 (query_ai_model_with_excel): {e}")
        # Return original dataframe with potentially empty new columns on error to avoid breaking flow
        if output_response_column_name not in df_output.columns:
             df_output[output_response_column_name] = None
        if get_first_token and output_first_token_column_name not in df_output.columns:
             df_output[output_first_token_column_name] = None
        return df_output



def process_and_evaluate_excel(questions_excel_path, output_dir, prompt,
                               external_model_config, internal_model_config,
                               selected_metrics):
    """
    核心处理函数：读取问题Excel，调用内外两个模型，合并结果，执行评估，并保存最终Excel。

    :param questions_excel_path: 只包含一列问题的Excel文件路径
    :param output_dir: 最终Excel文件的保存目录
    :param prompt: 通用提示词 (或按需调整为模型特定提示词)
    :param external_model_config: 外部模型配置字典 {key, url, name, get_first_token}
    :param internal_model_config: 内部模型配置字典 {key, url, name, get_first_token}
    :param selected_metrics: 用户选择的评估指标列表 (e.g., ['ass', 'rouge1'])
    :return: 处理完成的Excel文件路径, 或 None 如果失败
    """
    try:
        df_questions = pd.read_excel(questions_excel_path)
        if df_questions.empty or len(df_questions.columns) == 0:
            raise ValueError("问题Excel文件为空或没有列。")
        
        question_column_actual_name = df_questions.columns[0]
        
        # 准备一个基础DataFrame用于收集结果
        df_result = pd.DataFrame()
        df_result['Questions'] = df_questions[question_column_actual_name].dropna()
        if df_result.empty:
            raise ValueError("提取问题后DataFrame为空。")

        # 1. 调用外部模型
        print("调用外部模型...")
        df_result_with_ext = query_ai_model_with_excel(
            df_result.copy(), # Pass a copy to avoid unintended modifications
            'Questions',
            'External_Model_Response',
            'External_Model_First_Token',
            external_model_config['key'],
            external_model_config['url'],
            external_model_config['name'],
            external_model_config['get_first_token'],
            prompt
        )
        df_result['External_Model_Response'] = df_result_with_ext.get('External_Model_Response')
        if external_model_config['get_first_token']:
            df_result['External_Model_First_Token'] = df_result_with_ext.get('External_Model_First_Token')

        # 2. 调用内部模型
        print("调用内部模型...")
        df_result_with_int = query_ai_model_with_excel(
            df_result.copy(), # Pass a copy with only questions for internal model
            'Questions',
            'Internal_Model_Response',
            'Internal_Model_First_Token',
            internal_model_config['key'],
            internal_model_config['url'],
            internal_model_config['name'],
            internal_model_config['get_first_token'],
            prompt
        )
        df_result['Internal_Model_Response'] = df_result_with_int.get('Internal_Model_Response')
        if internal_model_config['get_first_token']:
            df_result['Internal_Model_First_Token'] = df_result_with_int.get('Internal_Model_First_Token')

        # 确保评估函数所需的列顺序：Questions, External, Internal
        final_columns_order = ['Questions', 'External_Model_Response', 'Internal_Model_Response']
        if external_model_config['get_first_token'] and 'External_Model_First_Token' in df_result:
            final_columns_order.append('External_Model_First_Token')
        if internal_model_config['get_first_token'] and 'Internal_Model_First_Token' in df_result:
            final_columns_order.append('Internal_Model_First_Token')
        
        # Reorder df_result columns if necessary, handling missing columns gracefully
        current_cols = [col for col in final_columns_order if col in df_result.columns]
        df_result = df_result[current_cols]

        # 创建唯一文件名并保存包含模型响应的Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        output_filename = f"eval_ready_{timestamp}_{unique_id}.xlsx"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file_path = os.path.join(output_dir, output_filename)
        df_result.to_excel(output_file_path, index=False)
        print(f"模型响应已保存到: {output_file_path}")

        # 3. 执行评估指标计算
        if selected_metrics:
            print(f"开始评估指标计算: {selected_metrics}")
            if 'ass' in selected_metrics:
                print("计算ASS值...")
                excel_ragas(output_file_path) # Modifies file in place
            if 'rouge1' in selected_metrics:
                print("计算ROUGE-1...")
                excel_rouge(output_file_path, 'ROUGE-1') # Modifies file in place
            if 'rouge2' in selected_metrics:
                print("计算ROUGE-2...")
                excel_rouge(output_file_path, 'ROUGE-2') # Modifies file in place
            if 'rougel' in selected_metrics:
                print("计算ROUGE-L...")
                excel_rouge(output_file_path, 'ROUGE-L') # Modifies file in place
            if 'f1_chinese' in selected_metrics:
                print("计算F1值(中文分词)...")
                calculate_f1_chinese(output_file_path) # Modifies file in place
        
        print(f"所有处理和评估完成。最终文件: {output_file_path}")
        return output_file_path

    except Exception as e:
        print(f"处理Excel时发生严重错误 (process_and_evaluate_excel): {e}")
        import traceback
        traceback.print_exc()
        return None


def excel_ragas(file_path):
    print(f"Stub for excel_ragas called with {file_path}")
    # TODO: Implement actual RAGAS evaluation logic
    pass

def excel_rouge(file_path, rouge_type):
    print(f"Stub for excel_rouge ({rouge_type}) called with {file_path}")
    # TODO: Implement actual ROUGE evaluation logic
    pass

def calculate_f1_chinese(file_path):
    print(f"Stub for calculate_f1_chinese called with {file_path}")
    # TODO: Implement actual F1 Chinese evaluation logic
    pass

# The existing functions excel_ragas, excel_rouge, calculate_f1_chinese, convert_seconds
# and extract_column_to_new_excel remain largely unchanged below this point.
# Ensure they are compatible with the column structure (Questions, External, Internal)
# excel_ragas, excel_rouge, calculate_f1_chinese expect answers in df.iloc[:, 1] and df.iloc[:, 2]
# which corresponds to 'External_Model_Response' and 'Internal_Model_Response' in the saved df_result.

# Example usage (for testing, can be removed or commented out):
# if __name__ == '__main__':
#     # Create a dummy questions.xlsx for testing
#     dummy_questions_data = {'MyQuestions': ['Translate hello to Spanish', 'What is the capital of France?', 'Summarize this text: AI is cool.']}
#     dummy_df = pd.DataFrame(dummy_questions_data)
#     dummy_excel_path = 'dummy_questions.xlsx'
#     dummy_df.to_excel(dummy_excel_path, index=False)

#     test_output_dir = './test_output'
#     if not os.path.exists(test_output_dir):
#         os.makedirs(test_output_dir)

#     ext_config = {'key': 'YOUR_EXTERNAL_KEY', 'url': 'YOUR_EXTERNAL_URL', 'name': 'YOUR_EXTERNAL_MODEL', 'get_first_token': True}
#     int_config = {'key': 'YOUR_INTERNAL_KEY', 'url': 'YOUR_INTERNAL_URL', 'name': 'YOUR_INTERNAL_MODEL', 'get_first_token': True}
#     metrics = ['ass', 'rouge1'] #, 'f1_chinese']
#     prompt_text = "Please provide a concise answer."

#     # Test extract_column_to_new_excel
#     # Create a dummy multi-column excel for extract_column_to_new_excel test
#     dummy_multi_col_data = {'ColA': [1,2], 'ColB_Questions': ['Q1', 'Q2'], 'ColC': [3,4]}
#     dummy_multi_excel = 'dummy_multi.xlsx'
#     pd.DataFrame(dummy_multi_col_data).to_excel(dummy_multi_excel, index=False)
#     extracted_path = extract_column_to_new_excel(dummy_multi_excel, 'B', test_output_dir)
#     print(f"Extracted file for testing: {extracted_path}")

#     if extracted_path:
#         final_file = process_and_evaluate_excel(extracted_path, test_output_dir, prompt_text, ext_config, int_config, metrics)
#         if final_file:
#             print(f"Test completed. Final file: {final_file}")
#             # print(pd.read_excel(final_file))
#         else:
#             print("Test failed during process_and_evaluate_excel.")
#     else:
#         print("Test failed during extract_column_to_new_excel.")

#     # Cleanup dummy files
#     # if os.path.exists(dummy_excel_path): os.remove(dummy_excel_path)
#     # if os.path.exists(dummy_multi_excel): os.remove(dummy_multi_excel)
#     # if extracted_path and os.path.exists(extracted_path): os.remove(extracted_path)
#     # if final_file and os.path.exists(final_file): os.remove(final_file)


# calculate_f1_chinese('产品说明书1_AI生成的用例.xlsx')