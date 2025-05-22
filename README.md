# 大模型辅助通用系统

## 1. 项目简介

本项目是一个基于大模型的辅助通用系统，旨在提供一系列工具来支持与大模型相关的研发和测试工作。系统包含多个功能模块，如生成式文本准确性指标测评、文件下载、文本内容随机抽取以及AI模型评估等。

## 2. 技术栈

- **后端**: Python, Flask
- **前端**: HTML, CSS (Bootstrap), JavaScript
- **数据存储**: 文件系统 (用于日志、上传下载文件)
- **AI模型**: 集成本地和外部大模型，具体模型通过配置指定。使用了 `sentence-transformers` (如 BAAI/bge-small-zh-v1.5), `openai` (GPT系列), `modelscope` 等库进行模型调用和评估。

## 3. 系统架构

系统采用典型的Web应用架构，前后端分离。

### 3.1 前端 (Frontend)

- 使用HTML、CSS和JavaScript构建用户界面。
- 利用Bootstrap框架进行页面布局和样式设计。
- 通过Flask的模板引擎 (Jinja2) 动态渲染页面。

### 3.2 后端 (Backend)

- 基于Flask框架开发，处理HTTP请求和业务逻辑。
- 包含路由定义、业务处理模块等。

### 3.3 模型 (Models)

- 系统支持集成和调用多种AI模型，包括本地部署的模型和通过API访问的外部模型。
- 本地模型（如词向量模型）通常存储在 `models/` 目录下，例如 `models/BAAI/bge-small-zh-v1.5`。
- 外部模型通过API密钥和URL进行配置，支持如OpenAI的GPT系列模型、国产大模型等。
- `TQ/PromptTemplate.json` 文件用于存储和管理不同任务的Prompt模板。

### 3.4 数据存储 (Data Storage)

- 用户上传的文件、处理后的文件以及应用日志主要存储在 `instance/` 目录下。

## 4. 功能模块

系统主要包含以下功能模块：

### 4.1 首页 (`main.index`)
- 系统入口页面，提供导航至各个功能模块。

### 4.2 生成式文本准确性指标测评工具 (`main.function1`)
- **核心功能**: 对生成式AI模型的输出文本进行多维度准确性评估。
- **输入**: 用户上传包含标准问题（或输入文本）的Excel文件，并指定问题所在的列。
- **处理流程**:
    1.  用户配置内部和/或外部大模型的API信息（Key, URL, 模型名称）及Prompt。
    2.  选择需要计算的评估指标，如 ROUGE, BLEU, BERTScore (ASS - 基于语义相似度), 字词编辑距离等。
    3.  系统后台异步处理：
        a.  读取Excel中的问题列。
        b.  根据用户配置的Prompt和模型，调用大模型生成答案。
        c.  计算选定的评估指标，对比模型生成答案与标准答案（如果提供）。
    4.  处理完成后，生成包含评估结果的新Excel文件供用户下载。
- **技术点**: 使用 `pandas` 处理Excel，`openai`, `requests` 调用模型API，`sentence-transformers`, `rouge`, `jieba`, `modelscope` 等库计算评估指标。任务状态通过轮询更新。

### 4.3 文件下载 (`main.function2`)
- **核心功能**: 列出并提供下载由其他功能模块（如function1, function3, function4）处理后生成的各类文件。
- **文件来源**: 主要来自 `instance/processed_files/` 目录。
- **展示方式**: 页面会列出该目录下的所有文件，显示文件名、大小、修改时间，并提供下载链接。
- **排序**: 文件列表默认按修改时间降序排列（最新文件在前）。

### 4.4 文本内容随机抽取工具 (`main.function3`)
- **核心功能**: 从用户上传的文本文件（`.txt`格式）或文件夹中，根据指定规则随机抽取一定数量或比例的内容，并保存为Excel文件。
- **输入**:
    1.  单个或多个 `.txt` 文件，或包含 `.txt` 文件的文件夹。
    2.  内容分割符（默认为换行符，可自定义）。
    3.  抽取方式：按数量或按百分比。
    4.  具体的数量或百分比值。
- **处理流程**:
    1.  用户上传文件/文件夹并配置抽取参数。
    2.  系统读取文本内容，根据分割符进行切分。
    3.  根据选定的抽取方式和值，随机抽取相应内容。
    4.  将抽取的内容保存到新的Excel文件中，文件名包含原始文件名和处理标识。
    5.  提供处理后的Excel文件下载链接。
- **技术点**: 使用 `werkzeug.utils.secure_filename` 处理上传文件名，`os` 模块进行文件操作，`TQ.tools.extract_and_save_to_excel` (或类似功能) 执行抽取和保存逻辑。

### 4.5 AI模型评估工具 (`main.function4`)
- **核心功能**: 允许用户上传包含待处理数据的Excel文件，选择预设的Prompt模板，配置大模型API，然后调用大模型对Excel中的每一行数据进行处理，并将模型的输出结果写回到Excel的新列中。
- **输入**:
    1.  包含待处理数据的Excel文件。
    2.  选择一个在 `TQ/PromptTemplate.json` 中定义的Prompt模板。
    3.  配置大模型的API Key, URL, 和模型名称。
- **处理流程**:
    1.  用户上传Excel，选择Prompt，配置模型信息。
    2.  系统后台异步处理：
        a.  读取Excel数据。
        b.  对每一行数据，结合选择的Prompt模板，调用配置的大模型API。
        c.  将模型返回的结果写入到Excel文件的一个新列中（列名通常与Prompt名称相关）。
    3.  处理完成后，提供修改后的Excel文件下载链接。
- **技术点**: 动态加载 `TQ/PromptTemplate.json` 中的Prompt模板。提供API连通性测试功能。使用 `threading` 进行后台异步处理。任务状态通过轮询更新。

## 5. 系统流程图

### 5.1 通用Web交互流程

1.  **用户访问**: 用户通过浏览器输入URL访问系统。
2.  **请求路由**: Flask应用接收HTTP请求，`app/routes.py` 中定义的蓝图 (`main_bp`) 根据URL路径将请求分发到对应的处理函数。
3.  **权限与日志**: (如果实现) 中间件或装饰器可能进行用户认证、权限检查，并记录访问日志到 `instance/app.log`。
4.  **业务逻辑处理**: 对应的处理函数执行核心业务逻辑：
    *   **数据获取**: 从请求中获取表单数据 (`request.form`)、查询参数 (`request.args`) 或上传的文件 (`request.files`)。
    *   **数据校验**: 对输入数据进行有效性验证。
    *   **核心操作**: 调用 `ZhiBiao/achieve.py` 或 `TQ/tools.py` 中的函数执行具体任务，如文件处理、模型调用、指标计算等。
    *   **文件操作**: 在 `instance/uploads/` (临时上传) 和 `instance/processed_files/` (处理结果) 目录下进行文件读写。
    *   **异步任务**: 对于耗时操作（如模型评估），通过 `threading` 创建后台线程处理，主线程立即返回任务ID，前端通过该ID轮询任务状态 (`/get_progress/<task_id>`, `/get_evaluation_progress/<task_id>`)。
5.  **响应生成**: 
    *   对于页面请求，使用 `render_template()` 渲染HTML模板 (`app/templates/`)，并将处理结果传递给模板。
    *   对于API请求或异步任务提交/状态查询，使用 `jsonify()` 返回JSON格式数据。
6.  **响应返回**: Flask将生成的HTML页面或JSON数据返回给用户浏览器。

### 5.2 功能1: 生成式文本准确性指标测评流程

1.  用户在 Function1 页面上传包含问题的Excel文件，选择问题列，填写Prompt，配置模型API，选择评估指标。
2.  前端JS将表单数据POST到 `/function1` 路由。
3.  后端接收请求，保存上传的Excel到 `instance/uploads/`，生成任务ID。
4.  启动后台线程执行 `process_task_background` 函数：
    a.  `extract_column_to_new_excel` 提取问题列到新Excel。
    b.  `process_and_evaluate_excel` 调用模型获取答案，计算指标，生成最终结果Excel到 `instance/processed_files/`。
5.  前端轮询 `/get_progress/<task_id>` 获取任务状态和进度。
6.  任务完成后，前端展示结果，并提供下载链接 (`/download_file/<filename>`)。

### 5.3 功能3: 文本内容随机抽取流程

1.  用户在 Function3 页面上传TXT文件/文件夹，设置分割符、抽取类型和数量/百分比。
2.  前端JS将表单数据POST到 `/function3` 路由。
3.  后端接收请求，保存上传文件到 `instance/uploads/` 下的临时子目录。
4.  调用 `TQ.tools.extract_and_save_to_excel` (或类似方法) 处理每个文件：
    a.  读取文本，按分割符切分。
    b.  随机抽取内容。
    c.  将结果保存为Excel到 `instance/processed_files/`。
5.  后端返回包含生成文件名和下载链接的JSON响应。
6.  前端展示下载链接。

### 5.4 功能4: AI模型评估工具流程

1.  用户在 Function4 页面上传Excel，选择Prompt模板，配置模型API。
2.  前端JS通过 `/get_prompts` 获取Prompt列表，`/get_llm_models` 获取模型列表（可选）。用户可测试API连通性 (`/test_ai_model_connection`)。
3.  前端JS将表单数据POST到 `/function4` 路由。
4.  后端接收请求，保存上传的Excel到 `instance/processed_files/` (作为输入副本)，生成任务ID。
5.  启动后台线程执行 `process_evaluation_task_background` 函数：
    a.  `tq_tools.ai_prompt_query` 逐行读取Excel，结合Prompt调用大模型，并将结果写入新列。
6.  前端轮询 `/get_evaluation_progress/<task_id>` 获取任务状态和进度。
7.  任务完成后，前端展示结果，并提供下载链接 (`/download_file/<filename>`)。

## 6. 安装与运行

1.  **克隆仓库** (如果项目使用Git管理)
    ```bash
    git clone <repository_url>
    cd AI_test_utils
    ```
    如果直接获取的项目文件夹，请跳过此步，直接进入项目根目录 `AI_test_utils`。

2.  **创建并激活Python虚拟环境** (强烈推荐)
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate    # Windows
    ```

3.  **安装依赖项**
    进入项目根目录 (包含 `requirements.txt` 文件的目录)，然后运行：
    ```bash
    pip install -r requirements.txt
    ```
    这将会安装所有必要的Python包。

4.  **配置环境变量** (可选，但重要)
    某些功能（如调用外部大模型API）可能需要配置API密钥。这些密钥通常通过环境变量设置，或者在 `config.py` 中以安全的方式管理。请查阅 `config.py` 或相关文档了解是否需要设置特定的环境变量，如 `SECRET_KEY` (Flask自身需要)。
    例如，如果 `config.py` 中有 `os.environ.get('OPENAI_API_KEY')` 这样的代码，您需要设置相应的环境变量。

5.  **运行应用**
    在项目根目录下运行：
    ```bash
    python run.py
    ```
    此命令会启动Flask开发服务器。

6.  **访问应用**
    启动成功后，终端会显示应用运行的地址，通常是：
    ```
    * Running on http://127.0.0.1:5000/
    ```
    在浏览器中打开 `http://127.0.0.1:5000` 即可访问系统。
    注意：`debug=True` 模式下运行，适合开发环境。生产环境部署应使用更健壮的方式（如Gunicorn + Nginx）。

## 7. 目录结构

```
AI_test_utils/
├── TQ/                             # TQ相关工具或模块
│   ├── PromptTemplate.json
│   └── tools.py
├── ZhiBiao/                        # 指标计算相关模块
│   ├── achieve.py
│   └── cilin.txt
├── app/                            # Flask应用核心目录
│   ├── __init__.py               # 应用工厂
│   ├── routes.py                 # 路由定义
│   ├── static/                   # 静态文件 (CSS, JS, Images)
│   │   ├── css/
│   │   ├── images/
│   │   └── js/
│   └── templates/                # HTML模板
│       ├── index.html
│       ├── function1.html
│       ├── function2.html
│       ├── function3.html
│       └── function4.html
├── config.py                       # 配置文件
├── instance/                       # 实例文件夹 (日志、上传文件等)
│   ├── app.log
│   ├── processed_files/
│   └── uploads/
├── models/                         # AI模型存储目录
├── requirements.txt                # Python依赖包
└── run.py                          # 应用启动脚本
```

## 8. 依赖项

项目的主要依赖项记录在 `requirements.txt` 文件中。截至目前分析，包含以下主要库：

- `flask`: Web框架，用于构建后端应用。
- `werkzeug`: WSGI工具库，Flask的依赖，提供HTTP和WSGI相关功能。
- `pandas`: 用于数据处理和分析，特别是Excel文件的读写和操作。
- `openai`: OpenAI官方Python库，用于调用GPT系列等模型API。
- `sentence-transformers`: 用于生成句子/文本嵌入，常用于语义相似度计算。
- `numpy`: 数值计算库，许多数据科学和机器学习库的依赖。
- `rouge`: ROUGE评分库，用于文本摘要和机器翻译的评估。
- `jieba`: 中文分词库。
- `modelscope`: ModelScope平台Python库，用于访问和使用其上的模型。

请查看 `requirements.txt` 文件获取完整且精确的依赖列表及其版本。
