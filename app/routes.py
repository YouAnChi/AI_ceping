from flask import Blueprint, render_template, request, current_app, send_from_directory, url_for, redirect
from datetime import datetime
from test.achieve import extract_column_to_new_excel,query_ai_model_with_excel
import os
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    log_message = f"Accessed index page at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return render_template('index.html')



@main_bp.route('/subpage2')
def subpage2():
    log_message = f"Accessed subpage2 at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return render_template('subpage2.html')

@main_bp.route('/function1', methods=['GET', 'POST'])
def function1():
    log_message = f"Accessed function1 at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    if request.method == 'POST':
        if 'excelFile' not in request.files:
            current_app.logger.error('No file part')
            return redirect(request.url)
        file = request.files['excelFile']
        if file.filename == '':
            current_app.logger.error('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            uploaded_file_path = os.path.join(current_app.config['UPLOADS_FOLDER'], filename)
            file.save(uploaded_file_path)
            current_app.logger.info(f'File {filename} uploaded to {uploaded_file_path}')

            column_letter = request.form.get('questionColumn', 'A') # 获取问题列，默认为A
            current_app.logger.info(f'Selected column: {column_letter}')

            # 1. 提取列
            # 注意: extract_column_to_new_excel 现在需要 output_dir 参数
            extracted_file_path = extract_column_to_new_excel(uploaded_file_path, column_letter, current_app.config['PROCESSED_FILES_FOLDER'])
            if not extracted_file_path:
                current_app.logger.error('Failed to extract column from Excel.')
                # 可以添加错误处理，例如返回一个错误页面或消息
                return render_template('function1.html', error_message='提取列失败')
            current_app.logger.info(f'Extracted column to {extracted_file_path}')

            # 2. 调用AI模型处理 (参数暂时硬编码)
            key = "sk-ptaneqxtvnazobcjgrnukaerzqmbjciacwbirtmekesqlrad"  # 替换为你的OpenAI API密钥
            api_url = "https://api.siliconflow.cn/v1/"  # 替换为你的OpenAI API URL
            model_name = "deepseek-ai/DeepSeek-V2.5"  # 替换为你的OpenAI模型名称
            get_first_token = True  # 是否获取首token
            prompt = request.form.get('prompt', '你是一个英文翻译机器人，请用英文翻译提供的内容，除此之外不要输出任何其他内容。') # 从表单获取prompt，如果用户没有输入则使用默认值
            
            processed_excel_path = query_ai_model_with_excel(extracted_file_path, key, api_url, model_name, get_first_token, prompt)
            
            if processed_excel_path:
                current_app.logger.info(f'AI model processed file saved to {processed_excel_path}')
                # 提取文件名用于下载链接
                processed_filename = os.path.basename(processed_excel_path)
                return render_template('function1.html', processed_filename=processed_filename)
            else:
                current_app.logger.error('Failed to process Excel with AI model.')
                return render_template('function1.html', error_message='AI模型处理失败')

    return render_template('function1.html')

@main_bp.route('/function2')
def function2():
    log_message = f"Accessed function2 at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return render_template('function2.html')

@main_bp.route('/download/<filename>')
def download_file(filename):
    log_message = f"Download request for {filename} at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return send_from_directory(current_app.config['PROCESSED_FILES_FOLDER'], filename, as_attachment=True)