from flask import Blueprint, render_template, request, current_app, send_from_directory, url_for, jsonify
from datetime import datetime
from ZhiBiao.achieve import extract_column_to_new_excel, process_and_evaluate_excel
import os
from werkzeug.utils import secure_filename
import uuid
import threading

main_bp = Blueprint('main', __name__)

# A simple in-memory store for task statuses (NOT SUITABLE FOR PRODUCTION)
# Structure: tasks_status[task_id] = {'status': 'processing' | 'completed' | 'failed', 'progress': 0-100, 'message': '...', 'processed_filename': '...'}
tasks_status = {}

import requests # For making HTTP requests in test_connection

def process_task_background(app, task_id, processing_params):
    with app.app_context(): # Need app context for logging and config
        try:
            current_app.logger.info(f"Background processing started for task {task_id}")
            tasks_status[task_id]['status'] = 'processing'
            tasks_status[task_id]['progress'] = 60 # Simulate some progress

            final_excel_path = process_and_evaluate_excel(
                processing_params['questions_excel_path'],
                processing_params['output_dir'],
                processing_params['prompt'],
                processing_params['external_model_config'],
                processing_params['internal_model_config'],
                processing_params['selected_metrics'],
                processing_params.get('embedding_model_for_ass', 'BAAI/bge-small-zh-v1.5') # Pass to background task
            )
            
            if final_excel_path:
                processed_filename = os.path.basename(final_excel_path)
                tasks_status[task_id].update({
                    'status': 'completed', 
                    'progress': 100, 
                    'processed_filename': processed_filename
                })
                current_app.logger.info(f'Background processing complete for task {task_id}. Final file: {final_excel_path}')
            else:
                tasks_status[task_id].update({'status': 'failed', 'progress': 100, 'message': '处理和评估Excel失败'})
                current_app.logger.error(f'Background processing failed for task {task_id}: process_and_evaluate_excel returned None.')

        except Exception as e:
            current_app.logger.error(f'Exception during background processing for task {task_id}: {str(e)}')
            tasks_status[task_id].update({'status': 'failed', 'progress': 100, 'message': f'处理过程中发生内部错误: {str(e)}'})

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
    log_message = f"Accessed function1 at {datetime.now()} from {request.remote_addr} with method {request.method}"
    current_app.logger.info(log_message)

    embedding_models_list = []
    try:
        # Correct path to AI_test_utils/models from app/routes.py
        # current_app.root_path is /Users/lpd/Documents/project/ceping/AI_test_utils/app
        models_dir = os.path.join(current_app.root_path, '..', 'models')
        if os.path.exists(models_dir) and os.path.isdir(models_dir):
            # List subdirectories which are potential model names or organization folders
            for item in os.listdir(models_dir):
                item_path = os.path.join(models_dir, item)
                if os.path.isdir(item_path):
                    # If item itself is a model (e.g. paraphrase-multilingual-MiniLM-L12-v2)
                    # or if it's an org folder (e.g. BAAI containing bge-small-zh-v1.5)
                    # We can list 'item' or 'item/subitem'
                    # For now, let's list top-level dirs and also one level deeper for org/model structure
                    if any(f.endswith(('.bin', '.safetensors', 'config.json')) for f in os.listdir(item_path)): # Heuristic for model dir
                        embedding_models_list.append(item)
                    else: # Check for org/model structure
                        for sub_item in os.listdir(item_path):
                            sub_item_path = os.path.join(item_path, sub_item)
                            if os.path.isdir(sub_item_path) and any(f.endswith(('.bin', '.safetensors', 'config.json')) for f in os.listdir(sub_item_path)):
                                normalized_sub_item = sub_item.replace('___', '.')
                                embedding_models_list.append(f"{item}/{normalized_sub_item}")
            embedding_models_list = sorted(list(set(embedding_models_list))) # Unique and sorted
        current_app.logger.info(f"Found embedding models: {embedding_models_list}")
    except Exception as e:
        current_app.logger.error(f"Error scanning models directory: {e}")

    if request.method == 'POST':
        task_id = str(uuid.uuid4())
        tasks_status[task_id] = {'status': 'submitted', 'progress': 0, 'task_id': task_id}

        if 'excelFile' not in request.files:
            current_app.logger.error('No file part')
            tasks_status[task_id].update({'status': 'failed', 'message': '没有上传文件'})
            return jsonify(tasks_status[task_id]), 400
        
        file = request.files['excelFile']
        if file.filename == '':
            current_app.logger.error('No selected file')
            tasks_status[task_id].update({'status': 'failed', 'message': '没有选择文件'})
            return jsonify(tasks_status[task_id]), 400

        if file:
            try:
                filename = secure_filename(file.filename)
                # Ensure UPLOADS_FOLDER exists
                uploads_folder = current_app.config['UPLOADS_FOLDER']
                if not os.path.exists(uploads_folder):
                    os.makedirs(uploads_folder)
                uploaded_file_path = os.path.join(uploads_folder, f"{task_id}_{filename}")
                file.save(uploaded_file_path)
                current_app.logger.info(f'File {filename} uploaded to {uploaded_file_path} for task {task_id}')
                tasks_status[task_id]['progress'] = 10

                column_letter = request.form.get('questionColumn', 'A')
                current_app.logger.info(f'Selected column: {column_letter} for task {task_id}')
                
                # Ensure PROCESSED_FILES_FOLDER exists
                processed_files_folder = current_app.config['PROCESSED_FILES_FOLDER']
                if not os.path.exists(processed_files_folder):
                    os.makedirs(processed_files_folder)

                questions_excel_path = extract_column_to_new_excel(uploaded_file_path, column_letter, processed_files_folder)
                if not questions_excel_path:
                    current_app.logger.error(f'Failed to extract column from Excel for task {task_id}.')
                    tasks_status[task_id].update({'status': 'failed', 'message': '提取问题列失败'})
                    return jsonify(tasks_status[task_id]), 500
                current_app.logger.info(f'Questions extracted to {questions_excel_path} for task {task_id}')
                tasks_status[task_id]['progress'] = 30

                prompt = request.form.get('prompt', '')
                external_model_config = {
                    'key': request.form.get('external_model_key'),
                    'url': request.form.get('external_model_url'),
                    'name': request.form.get('external_model_name'),
                    'get_first_token': request.form.get('external_model_get_first_token') == 'true'
                }
                internal_model_config = {
                    'key': request.form.get('internal_model_key'),
                    'url': request.form.get('internal_model_url'),
                    'name': request.form.get('internal_model_name'),
                    'get_first_token': request.form.get('internal_model_get_first_token') == 'true'
                }
                selected_metrics = request.form.getlist('metrics')
                embedding_model_for_ass = request.form.get('embedding_model_for_ass', 'BAAI/bge-small-zh-v1.5') # Default if not provided
                current_app.logger.info(f'Selected embedding model for ASS: {embedding_model_for_ass}')
                tasks_status[task_id]['progress'] = 50

                processing_params = {
                    'questions_excel_path': questions_excel_path,
                    'output_dir': processed_files_folder,
                    'prompt': prompt,
                    'external_model_config': external_model_config,
                    'internal_model_config': internal_model_config,
                    'selected_metrics': selected_metrics,
                    'embedding_model_for_ass': embedding_model_for_ass
                }
                
                # Start background thread for processing
                thread = threading.Thread(target=process_task_background, args=(current_app._get_current_object(), task_id, processing_params))
                thread.daemon = True # Daemonize thread
                thread.start()

                tasks_status[task_id]['status'] = 'processing' # Update status to processing as thread starts
                current_app.logger.info(f'Task {task_id} submitted for background processing.')
                return jsonify(tasks_status[task_id])

            except Exception as e:
                current_app.logger.error(f'Error during initial processing for task {task_id}: {str(e)}')
                tasks_status[task_id].update({'status': 'failed', 'message': f'处理请求时发生内部错误: {str(e)}'})
                return jsonify(tasks_status[task_id]), 500

    # GET request handling (renders the initial page)
    return render_template('function1.html', embedding_models=embedding_models_list)

@main_bp.route('/test_connection', methods=['POST'])
def test_connection():
    data = request.get_json()
    api_key = data.get('api_key')
    api_url = data.get('api_url')
    model_name = data.get('model_name') # Potentially useful for specific checks

    if not api_url:
        return jsonify({'status': 'failed', 'message': 'API URL 不能为空'}), 400

    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}' # Common practice, adjust if API expects different auth
    
    # Add a common header that might be expected by LLM APIs
    headers['Content-Type'] = 'application/json'

    try:
        # Attempt a simple request. A GET request to the base URL or a known health endpoint is common.
        # For LLM APIs, often a POST to a completions or models endpoint is needed for a real test.
        # Here, we'll try a GET request to the base URL as a generic test.
        # Some APIs might not respond to a simple GET on the base URL, or might require a specific path.
        # A more robust test might involve sending a minimal valid payload if the API structure is known.
        
        # Let's try to list models if the URL pattern suggests it (common for OpenAI-compatible APIs)
        # This is a heuristic and might not work for all APIs.
        test_url = api_url.strip('/') # Remove trailing slash for consistency
        if not test_url.endswith('/v1'): # if it's a base url like https://api.example.com
            test_url += '/v1' # append /v1
        
        # Try to list models, a common endpoint for LLM APIs
        # If the API is not OpenAI compatible, this might fail, but it's a reasonable attempt.
        # A simple GET to the base_url might also work for some health checks.
        # Using a timeout to prevent hanging indefinitely.
        response = requests.get(f"{test_url}/models", headers=headers, timeout=10) 

        # Check if the request was successful (status code 2xx)
        if response.status_code >= 200 and response.status_code < 300:
            # Optionally, check if the response body contains expected data, e.g., a list of models
            # For simplicity, we'll just consider a 2xx status as success here.
            current_app.logger.info(f"Connection test to {api_url} (model: {model_name}) successful. Status: {response.status_code}")
            return jsonify({'status': 'success', 'message': '连接成功'}), 200
        else:
            current_app.logger.warning(f"Connection test to {api_url} (model: {model_name}) failed. Status: {response.status_code}, Response: {response.text[:200]}")
            return jsonify({'status': 'failed', 'message': f'连接失败 (状态码: {response.status_code}). 请检查API URL和Key。'}), response.status_code

    except requests.exceptions.Timeout:
        current_app.logger.error(f"Connection test to {api_url} (model: {model_name}) timed out.")
        return jsonify({'status': 'failed', 'message': '连接超时。请检查API URL和网络连接。'}), 408
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Connection test to {api_url} (model: {model_name}) failed with exception: {str(e)}")
        return jsonify({'status': 'failed', 'message': f'连接请求失败: {str(e)}'}), 500
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during connection test to {api_url} (model: {model_name}): {str(e)}")
        return jsonify({'status': 'failed', 'message': f'发生意外错误: {str(e)}'}), 500


@main_bp.route('/get_progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    log_message = f"Polling progress for task_id {task_id} at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)

    task_info = tasks_status.get(task_id)
    if not task_info:
        return jsonify({'status': 'error', 'message': '无效的任务ID'}), 404
    
    # Simulate some progress if still processing by the background thread
    if task_info['status'] == 'processing' and task_info['progress'] < 90: # Don't overwrite final 100 from thread
        task_info['progress'] += 5 # Simple progress simulation for polling
        if task_info['progress'] > 90: task_info['progress'] = 90

    return jsonify(task_info)


@main_bp.route('/function2')
def function2():
    log_message = f"Accessed function2 at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return render_template('function2.html')

@main_bp.route('/download_file/<filename>')
def download_file(filename):
    log_message = f"Download request for {filename} at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    
    directory = current_app.config['PROCESSED_FILES_FOLDER']
    # Ensure directory is absolute or correctly relative to app root for send_from_directory
    if not os.path.isabs(directory):
        # Assuming PROCESSED_FILES_FOLDER is relative to the instance path or app root
        # For simplicity, let's assume it's relative to app.root_path if not absolute.
        # A more robust solution might involve current_app.instance_path
        directory = os.path.join(current_app.root_path, '..', directory) # Adjust if structure is different
        directory = os.path.normpath(directory)

    current_app.logger.info(f"Attempting to send file from directory: {directory}, filename: {filename}")
    
    safe_filename = secure_filename(filename)
    if safe_filename != filename:
        current_app.logger.warning(f"Potentially unsafe filename requested: {filename}, sanitized to {safe_filename}. Denying request.")
        return jsonify({'status': 'error', 'message': '无效的文件名'}), 400
    
    file_path = os.path.join(directory, safe_filename)
    if not os.path.exists(file_path):
        current_app.logger.error(f"File not found for download: {file_path}")
        return jsonify({'status': 'error', 'message': '文件未找到'}), 404

    return send_from_directory(directory, safe_filename, as_attachment=True)