# 项目更新文档

本文档详细记录了 AI Test Utils 项目近期在核心功能、API接口及前端交互方面的更新。

## 1. 后端核心逻辑 (`/Users/lpd/Documents/project/ceping/AI_test_utils/test/achieve.py`)

此文件包含了数据处理、模型调用和评估的核心函数。

### 1.1. 新增/修改的函数

#### a. `extract_column_to_new_excel(input_excel_path, column_letter, output_dir)`

*   **功能描述**: 从指定的Excel文件中提取特定列的数据，并将其保存到一个新的、唯一命名的Excel文件中。
*   **参数**:
    *   `input_excel_path` (str): 输入的原始Excel文件路径。
    *   `column_letter` (str): 需要提取的列的字母标识 (例如: 'A', 'B')。
    *   `output_dir` (str): 新生成的Excel文件的存放目录。
*   **返回值**: (str) 成功则返回新创建的Excel文件的完整路径，失败则返回 `None`。
*   **主要逻辑变更**: 
    *   读取输入Excel。
    *   根据列字母定位并提取指定列。
    *   生成包含时间戳和UUID的唯一文件名，确保文件不被覆盖。
    *   将提取的列数据写入新的Excel文件。

#### b. `query_ai_model_with_excel(df_input, question_column_name, output_response_column_name, output_first_token_column_name, key, url, model_name, get_first_token, prompt=None)`

*   **功能描述**: 针对DataFrame中的每一行问题，调用指定的AI模型（兼容OpenAI API格式）进行查询，并将模型的响应及可选的首token响应时间添加回DataFrame。
*   **参数**:
    *   `df_input` (pd.DataFrame): 包含问题列的输入DataFrame。
    *   `question_column_name` (str): DataFrame中问题所在列的列名。
    *   `output_response_column_name` (str): 用于存储模型完整响应的新列的列名。
    *   `output_first_token_column_name` (str): 用于存储首token响应时间的新列的列名。
    *   `key` (str): AI模型的API密钥。
    *   `url` (str): AI模型的API端点URL。
    *   `model_name` (str): 使用的AI模型名称。
    *   `get_first_token` (bool): 是否计算并记录首token的响应时间。
    *   `prompt` (str, optional): 提供给模型的系统提示词，默认为 `None`。
*   **返回值**: (pd.DataFrame) 一个新的DataFrame副本，其中包含了模型响应和（如果请求）首token时间的新列。
*   **主要逻辑变更**:
    *   初始化AI模型客户端。
    *   遍历DataFrame中的问题。
    *   为每个问题构建请求消息，并结合可选的系统提示词。
    *   以流式方式调用模型API，收集完整的响应内容。
    *   如果 `get_first_token` 为 `True`，则记录从发送请求到接收到第一个token的时间。
    *   将收集到的响应和首token时间添加到DataFrame的新列中。

#### c. `process_and_evaluate_excel(questions_excel_path, output_dir, prompt, external_model_config, internal_model_config, selected_metrics)`

*   **功能描述**: 这是一个核心的编排函数。它读取包含问题的Excel文件，分别使用外部和内部AI模型处理这些问题，合并处理结果，然后根据用户选择的评估指标进行评估，最终将所有结果保存到一个新的Excel文件中。
*   **参数**:
    *   `questions_excel_path` (str): 只包含一列问题的Excel文件路径（通常由 `extract_column_to_new_excel` 生成）。
    *   `output_dir` (str): 最终生成的包含所有结果和评估的Excel文件的存放目录。
    *   `prompt` (str): 应用于两个模型的通用提示词。
    *   `external_model_config` (dict): 外部模型的配置信息，包括 `key`, `url`, `name`, `get_first_token`。
    *   `internal_model_config` (dict): 内部模型的配置信息，包括 `key`, `url`, `name`, `get_first_token`。
    *   `selected_metrics` (list): 用户选择的评估指标列表 (例如: `['ass', 'rouge1', 'f1_chinese']`)。
*   **返回值**: (str) 成功则返回最终生成的Excel文件的完整路径，失败则返回 `None`。
*   **主要逻辑变更**:
    1.  读取问题Excel文件。
    2.  调用 `query_ai_model_with_excel` 函数获取外部模型的响应和首token时间。
    3.  调用 `query_ai_model_with_excel` 函数获取内部模型的响应和首token时间。
    4.  将问题、两个模型的响应及首token时间合并到一个DataFrame中。
    5.  按特定顺序排列DataFrame的列（Questions, External_Model_Response, Internal_Model_Response, External_Model_First_Token, Internal_Model_First_Token）。
    6.  将包含模型响应的DataFrame保存到一个中间Excel文件，文件名唯一。
    7.  如果 `selected_metrics` 列表不为空，则遍历选择的指标，并调用相应的评估函数（如 `excel_ragas`, `excel_rouge`, `calculate_f1_chinese`）。这些评估函数会直接修改上一步生成的Excel文件，在文件中添加新的评估结果列。
    8.  返回最终处理和评估完成的Excel文件路径。

## 2. API 路由 (`/Users/lpd/Documents/project/ceping/AI_test_utils/app/routes.py`)

此文件定义了Web应用的API端点。

### 2.1. 更新的路由

#### a. `@main_bp.route('/function1', methods=['GET', 'POST'])`
*   **对应函数**: `function1()`
*   **功能描述**: 处理与“功能1”（模型对比评估）相关的用户请求。GET请求用于展示表单页面，POST请求用于处理用户提交的数据并执行评估流程。
*   **GET 请求**: 
    *   渲染 `function1.html` 模板页面。
*   **POST 请求逻辑**:
    1.  **文件上传**: 接收用户上传的Excel文件 (`excelFile`)。
    2.  **参数获取**: 从表单中获取问题列字母 (`questionColumn`)、通用提示词 (`prompt`)、外部模型配置 (`external_model_key`, `external_model_url`, `external_model_name`, `external_model_get_first_token`)、内部模型配置 (`internal_model_key`, `internal_model_url`, `internal_model_name`, `internal_model_get_first_token`) 以及选择的评估指标列表 (`metrics`)。
    3.  **问题提取**: 调用 `achieve.extract_column_to_new_excel` 函数，从上传的Excel中提取指定的问题列，生成一个新的只包含问题的Excel文件。
    4.  **核心处理**: 调用 `achieve.process_and_evaluate_excel` 函数，传入提取的问题文件路径、输出目录以及从表单获取的所有配置参数和评估指标。
    5.  **结果反馈**: 
        *   如果处理成功，渲染 `function1.html` 页面，并传递处理后生成的最终Excel文件名 (`processed_filename`) 以供用户下载或查看。
        *   如果处理失败，渲染 `function1.html` 页面，并传递错误信息 (`error_message`)。

## 3. 前端页面 (`/Users/lpd/Documents/project/ceping/AI_test_utils/app/templates/function1.html`)

此HTML文件是“功能1”的用户交互界面。

### 3.1. 主要功能和表单元素

根据后端 `routes.py` 中的 `function1` 路由逻辑，`function1.html` 页面应包含以下表单元素以支持其功能：

*   **文件上传控件**: 用于选择和上传包含待处理问题的Excel文件 (name: `excelFile`)。
*   **问题列指定**: 输入框，用于指定Excel中问题所在的列的字母 (name: `questionColumn`, 默认值: 'A')。
*   **通用提示词**: 文本区域，用于输入AI模型的通用提示词 (name: `prompt`)。
*   **外部模型配置区域**:
    *   API Key 输入框 (name: `external_model_key`)
    *   API URL 输入框 (name: `external_model_url`)
    *   模型名称 输入框 (name: `external_model_name`)
    *   获取首token时间 复选框 (name: `external_model_get_first_token`, value: 'true')
*   **内部模型配置区域**:
    *   API Key 输入框 (name: `internal_model_key`)
    *   API URL 输入框 (name: `internal_model_url`)
    *   模型名称 输入框 (name: `internal_model_name`)
    *   获取首token时间 复选框 (name: `internal_model_get_first_token`, value: 'true')
*   **评估指标选择**: 一组复选框，允许用户选择一个或多个评估指标进行计算 (name: `metrics`)。预期的选项可能包括：
    *   ASS (Answer Semantic Similarity)
    *   ROUGE-1
    *   ROUGE-2
    *   ROUGE-L
    *   F1 Score (中文分词)
*   **提交按钮**: 触发POST请求，开始处理流程。
*   **结果显示区域**: 用于显示处理成功后的文件名（可能作为下载链接）或处理失败时的错误信息。

**变更总结**: 前端页面配合后端逻辑，提供了完整的用户输入接口，用于配置模型参数、上传数据、选择评估维度，并接收处理结果。