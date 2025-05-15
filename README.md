# AI 测试工具

这是一个基于 Flask 的 Web 应用程序，旨在提供一套工具来辅助 AI 模型的测试和评估，特别是涉及到处理和分析 Excel 文件中的数据。

## 项目概述

本项目的主要功能包括：

1.  **Excel 文件处理**：用户可以上传 Excel 文件，指定特定列进行数据提取。
2.  **模型集成与评估**：提取的数据可以被用于调用内部和外部的 AI 模型进行处理，并根据用户选择的评估指标进行评估。
3.  **结果展示与下载**：处理和评估后的结果会生成新的 Excel 文件，用户可以下载该文件。
4.  **日志记录**：应用的关键操作和访问信息会被记录到日志文件中，便于追踪和调试。

## 项目架构

项目采用经典的 Flask Web 应用架构：

-   **`run.py`**: 项目的入口文件，用于启动 Flask 开发服务器。
-   **`config.py`**: 包含应用的配置信息，如密钥、数据库 URI (如果使用)、以及自定义配置项（如日志文件路径、上传文件夹路径等）。
-   **`app/`**: 应用的核心代码目录。
    -   **`__init__.py`**: 应用工厂函数 `create_app`，用于创建和配置 Flask 应用实例。这里会初始化应用配置、创建必要的文件夹（如上传目录、处理后文件目录）、配置日志记录器，并注册蓝图。
    -   **`routes.py`**: 定义应用的路由和视图函数。使用 Flask Blueprint (`main_bp`) 来组织路由。
    -   **`static/`**: 存放静态文件，如 CSS、JavaScript 文件和图片。
    -   **`templates/`**: 存放 HTML 模板文件，使用 Jinja2 模板引擎。
-   **`instance/`**: 实例文件夹，用于存放不应提交到版本控制的实例特定数据，如配置文件、SQLite 数据库（如果使用）、日志文件、上传的文件和处理后的文件。
    -   `uploads/`: 存放用户上传的原始文件。
    -   `processed_files/`: 存放经过处理和评估后生成的 Excel 文件。
    -   `app.log`: 应用的日志文件。
-   **`test/`**: 包含核心处理逻辑的模块。
    -   **`achieve.py`**: 实现了关键的数据处理和评估功能，如 `extract_column_to_new_excel` 和 `process_and_evaluate_excel`。
-   **`requirements.txt`**: 列出了项目运行所需的 Python 依赖包。
-   **`models/`**: 可能用于存放机器学习模型文件或相关资源（根据目录结构推断）。

## 主要功能及实现

### 1. 应用初始化 (`app/__init__.py`)

-   `create_app()` 函数：
    -   创建 Flask 应用实例。
    -   从 `config.Config` 加载配置。
    -   定义并创建 `UPLOADS_FOLDER` (位于 `instance/uploads`) 和 `PROCESSED_FILES_FOLDER` (位于 `instance/processed_files`)，如果它们不存在的话。
    -   配置日志系统，使用 `RotatingFileHandler` 将日志记录到 `instance/app.log`，日志级别为 INFO。
    -   从 `app.routes` 导入 `main_bp` 蓝图并注册到应用中。

### 2. 路由和视图函数 (`app/routes.py`)

所有路由都定义在 `main_bp` 蓝图下。

-   **`@main_bp.route('/')` -> `index()`**
    -   **功能**: 显示应用的主页。
    -   **实现**: 渲染 `index.html` 模板。记录访问日志。

-   **`@main_bp.route('/subpage2')` -> `subpage2()`**
    -   **功能**: 显示应用的子页面2。
    -   **实现**: 渲染 `subpage2.html` 模板。记录访问日志。

-   **`@main_bp.route('/function1', methods=['GET', 'POST'])` -> `function1()`**
    -   **功能**: 这是核心功能页面，用于上传 Excel 文件，提取指定列，使用模型进行处理和评估，并提供结果下载链接。
    -   **实现**:
        -   **GET 请求**: 渲染 `function1.html` 模板。可以接收 `processed_filename` (处理完成的文件名) 和 `error_message` (错误信息) 作为查询参数，用于在页面上显示相应信息。
        -   **POST 请求** (处理文件上传和评估流程):
            1.  **文件校验**: 检查请求中是否包含名为 `excelFile` 的文件部分，以及文件名是否为空。如果校验失败，则重定向回 `function1` 页面并显示错误信息。
            2.  **文件保存**: 使用 `secure_filename` 清理文件名，并将文件保存到 `current_app.config['UPLOADS_FOLDER']`。
            3.  **提取问题列**: 从表单获取 `questionColumn` (默认为 'A')，调用 `test.achieve.extract_column_to_new_excel()` 函数，将指定列的数据提取到一个新的 Excel 文件中，保存到 `current_app.config['PROCESSED_FILES_FOLDER']`。
            4.  **获取表单参数**: 获取用户输入的 `prompt`、外部模型配置 (`external_model_key`, `external_model_url`, `external_model_name`, `external_model_get_first_token`)、内部模型配置 (`internal_model_key`, `internal_model_url`, `internal_model_name`, `internal_model_get_first_token`) 以及选中的评估指标 `metrics`。
            5.  **核心处理与评估**: 调用 `test.achieve.process_and_evaluate_excel()` 函数，传入提取的问题 Excel 文件路径、处理后文件保存目录、prompt、模型配置和评估指标。此函数负责调用模型、进行评估并生成最终的 Excel 结果文件。
            6.  **结果处理**: 如果 `process_and_evaluate_excel` 成功返回最终文件路径，则获取文件名并重定向到 `function1` 页面，通过查询参数 `processed_filename` 传递文件名，以便用户下载。如果失败，则重定向并显示错误信息。
        -   所有关键步骤都会记录日志。

-   **`@main_bp.route('/function2')` -> `function2()`**
    -   **功能**: 显示应用的子页面/功能2。
    -   **实现**: 渲染 `function2.html` 模板。记录访问日志。

-   **`@main_bp.route('/download/<filename>')` -> `download_file(filename)`**
    -   **功能**: 提供文件下载功能。
    -   **实现**: 使用 `send_from_directory` 从 `current_app.config['PROCESSED_FILES_FOLDER']` 发送指定的文件给用户下载。记录下载请求日志。

### 3. 核心逻辑 (`test/achieve.py` - 基于调用推断)

-   **`extract_column_to_new_excel(uploaded_file_path, column_letter, output_folder)`**: 
    -   **功能**: 从指定的 Excel 文件 (`uploaded_file_path`) 中提取由 `column_letter` (如 'A', 'B') 指定的列的数据，并将这些数据保存到一个新的 Excel 文件中。新的 Excel 文件会存放在 `output_folder` 中。
    -   **返回**: 成功时返回新创建的 Excel 文件的路径，失败时返回 `None` 或引发异常。

-   **`process_and_evaluate_excel(questions_excel_path, output_folder, prompt, external_model_config, internal_model_config, selected_metrics)`**:
    -   **功能**: 这是核心的处理和评估引擎。它接收包含问题的 Excel 文件路径 (`questions_excel_path`)，用户提供的 `prompt`，内部和外部模型的配置信息，以及用户选择的评估指标 `selected_metrics`。
    -   该函数可能会执行以下操作：
        1.  读取 `questions_excel_path` 中的问题数据。
        2.  根据 `prompt` 和模型配置，调用外部 AI 模型和内部 AI 模型处理这些问题。
        3.  收集模型的输出。
        4.  根据 `selected_metrics` 对模型的输出进行评估。
        5.  将原始问题、模型输出、评估结果等整合到一个新的 Excel 文件中，并保存到 `output_folder`。
    -   **返回**: 成功时返回最终生成的 Excel 文件的路径，失败时返回 `None` 或引发异常。

## 安装与运行

1.  **克隆仓库** (如果适用)
    ```bash
    git clone <repository_url>
    cd AI_test_utils
    ```

2.  **创建并激活虚拟环境** (推荐)
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate    # Windows
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **运行应用**
    ```bash
    python run.py
    ```
    应用默认会在 `http://127.0.0.1:5000/` 启动。

## 目录结构详解

```
AI_test_utils/
├── app/                                # 应用核心代码
│   ├── __init__.py                     # 应用工厂
│   ├── routes.py                       # 路由定义
│   ├── static/                         # 静态文件 (CSS, JS, images)
│   │   ├── css/
│   │   └── js/
│   └── templates/                      # HTML 模板
│       ├── index.html
│       ├── subpage2.html
│       ├── function1.html
│       └── function2.html
├── instance/                           # 实例文件夹 (不应提交到git)
│   ├── uploads/                        # 用户上传的文件
│   ├── processed_files/                # 处理后的文件
│   └── app.log                         # 日志文件
├── models/                             # AI模型相关
│   └── ...
├── test/                               # 核心业务逻辑模块
│   ├── __init__.py
│   └── achieve.py                      # Excel处理和模型评估逻辑
├── config.py                           # 应用配置
├── requirements.txt                    # Python依赖
├── run.py                              # 应用启动脚本
└── README.md                           # 本文档
```

## 可优化和迭代的点

1.  **异步任务处理**: 对于 `process_and_evaluate_excel` 这种可能耗时较长的操作（尤其是调用外部模型和进行复杂评估时），可以考虑使用任务队列（如 Celery, RQ）将其改为异步处理。这样可以避免 Web 请求超时，并提升用户体验。用户提交任务后可以立即得到响应，并通过某种方式（如轮询、WebSocket）查询任务状态或在完成后收到通知。

2.  **更健壮的错误处理和用户反馈**: 
    -   在 `function1` 中，目前错误处理是通过重定向并传递 `error_message`。可以考虑使用 Flask 的 `flash` 消息机制，或者在前端通过 AJAX 提交表单，并在前端更友好地展示错误信息和处理进度。
    -   对 `extract_column_to_new_excel` 和 `process_and_evaluate_excel` 内部的各种潜在错误（如文件格式错误、模型API调用失败、评估指标计算错误等）进行更细致的捕获和报告。

3.  **输入验证**: 
    -   对用户上传的 Excel 文件进行更严格的内容和格式验证，确保其符合预期。
    -   对表单输入的参数（如模型 Key/URL）进行格式校验。

4.  **安全性增强**:
    -   除了 `secure_filename`，还应考虑其他安全措施，如限制上传文件的大小和类型。
    -   如果模型 API Key 等敏感信息需要长期存储，应考虑使用更安全的存储方式（如环境变量、Secrets Manager 服务），而不是直接通过表单传递（尽管当前实现似乎是即时使用）。

5.  **配置管理**: 
    -   对于模型端点、API密钥等，可以考虑从配置文件或环境变量中读取，而不是完全依赖用户在表单中输入，特别是对于一些固定的内部模型。

6.  **用户界面 (UI/UX) 改进**:
    -   提供更丰富的交互，如文件上传进度条、任务处理状态显示。
    -   对评估结果的展示可以更可视化。

7.  **模块化与可测试性**: 
    -   进一步解耦 `routes.py` 中的业务逻辑，将其移至 `test/achieve.py` 或其他服务模块中，使路由函数更轻量，只负责请求处理和响应。
    -   为核心功能（如 `extract_column_to_new_excel`, `process_and_evaluate_excel`）编写单元测试和集成测试。

8.  **模型管理**: 如果项目中涉及多种或可配置的模型，可以考虑建立一个更完善的模型管理机制，允许动态添加、配置和选择模型。

9.  **多用户与认证**: 如果需要支持多用户，需要引入用户认证和授权机制。

10. **文档完善**: 
    -   为 `test/achieve.py` 中的函数添加详细的文档字符串。
    -   提供 API 文档（如果计划将某些功能作为 API 暴露）。

## 依赖项

主要依赖项包括 (详见 `requirements.txt`):

-   Flask
-   Werkzeug (Flask 依赖)
-   Jinja2 (Flask 依赖)
-   Pandas (很可能在 `test/achieve.py` 中用于处理 Excel)
-   Openpyxl 或 XlsxWriter (Pandas 操作 Excel 文件可能需要)
-   Requests (可能用于调用外部模型 API)

(请根据实际 `requirements.txt` 内容更新此列表)