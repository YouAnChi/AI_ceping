from flask import Blueprint, render_template, request, current_app
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    log_message = f"Accessed index page at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return render_template('index.html')

@main_bp.route('/subpage1')
def subpage1():
    log_message = f"Accessed subpage1 at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return render_template('subpage1.html')

@main_bp.route('/subpage2')
def subpage2():
    log_message = f"Accessed subpage2 at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return render_template('subpage2.html')

@main_bp.route('/function1')
def function1():
    log_message = f"Accessed function1 at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return render_template('function1.html')

@main_bp.route('/function2')
def function2():
    log_message = f"Accessed function2 at {datetime.now()} from {request.remote_addr}"
    current_app.logger.info(log_message)
    return render_template('function2.html')