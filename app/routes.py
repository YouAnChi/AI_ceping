from flask import Blueprint, render_template, request, current_app, send_from_directory, url_for, redirect
from datetime import datetime
from test.achieve import extract_column_to_new_excel, process_and_evaluate_excel
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

            # 1. 提取问题列到单独的Excel文件
            questions_excel_path = extract_column_to_new_excel(uploaded_file_path, column_letter, current_app.config['PROCESSED_FILES_FOLDER'])
            if not questions_excel_path:
                current_app.logger.error('Failed to extract column from Excel.')
                return render_template('function1.html', error_message='提取问题列失败')
            current_app.logger.info(f'Questions extracted to {questions_excel_path}')

            # 2. 获取表单参数
            prompt = request.form.get('prompt', '')
            
            external_model_config = {
                'key': request.form.get('external_model_key'),
                'url': request.form.get('external_model_url'),
                'name': request.form.get('external_model_name'),
                'get_first_token': request.form.get('external_model_get_first_token') == 'true'
            }
            current_app.logger.info(f'External model config: {external_model_config}')

            internal_model_config = {
                'key': request.form.get('internal_model_key'),
                'url': request.form.get('internal_model_url'),
                'name': request.form.get('internal_model_name'),
                'get_first_token': request.form.get('internal_model_get_first_token') == 'true'
            }
            current_app.logger.info(f'Internal model config: {internal_model_config}')

            selected_metrics = request.form.getlist('metrics') # 获取所有选中的评估指标
            current_app.logger.info(f'Selected metrics: {selected_metrics}')

            # 3. 调用核心处理函数
            final_excel_path = process_and_evaluate_excel(
                questions_excel_path,
                current_app.config['PROCESSED_FILES_FOLDER'],
                prompt,
                external_model_config,
                internal_model_config,
                selected_metrics
            )

            if final_excel_path:
                current_app.logger.info(f'Processing and evaluation complete. Final file: {final_excel_path}')
                processed_filename = os.path.basename(final_excel_path)
                return render_template('function1.html', processed_filename=processed_filename)
            else:
                current_app.logger.error('Failed to process and evaluate Excel.')
                return render_template('function1.html', error_message='处理和评估Excel失败')

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