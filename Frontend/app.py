import paramiko
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import json
import sys
import subprocess
import re
import time
import glob
from datetime import datetime

# Initialize Flask with explicit static folder configuration
app = Flask(__name__,
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')

# Production configuration
if os.environ.get('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
else:
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'dev-secret-key'

#app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'test_case')
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
#app.config['GENERATED_SCRIPTS_FOLDER'] = os.path.join(os.getcwd(), 'generated-scripts')
#app.config['REPORT_FOLDER'] = os.path.join(os.getcwd(), 'reports')

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), '..', 'test_case')
app.config['GENERATED_SCRIPTS_FOLDER'] = os.path.join(os.getcwd(), '..', 'generated-scripts')
app.config['REPORT_FOLDER'] = os.path.join(os.getcwd(), '..', 'reports')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Updated allowed file extensions
ALLOWED_EXTENSIONS = {
    'txt', 'rtf', 'md', 'log', 'pdf', 'doc', 'docx', 'odt', 'pages',
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Security headers
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


'''
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)
'''

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


# Global variables to store uploaded files and generated scripts info
uploaded_files_global = []
generated_scripts_info = []


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    global uploaded_files_global

    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'message': 'No files selected'})

        files = request.files.getlist('files')
        uploaded_files = []
        total_size = 0

        for file in files:
            if file.filename == '':
                continue

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                file_size = os.path.getsize(file_path)
                total_size += file_size

                uploaded_files.append({
                    'name': file.filename,
                    'size': file_size,
                    'path': filename
                })
            else:
                print(f"File not allowed: {file.filename}")

        # Store uploaded files globally
        uploaded_files_global = uploaded_files

        if uploaded_files:
            return jsonify({
                'success': True,
                'files': uploaded_files,
                'total_size': total_size,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)'
            })
        else:
            return jsonify({'success': False, 'message': 'No valid files uploaded. Please check file types.'})

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'message': f'Upload error: {str(e)}'})


@app.route('/ingest', methods=['POST'])
def ingest_test():
    """Process ingested test files and identify individual test cases"""
    try:
        data = request.get_json()
        files = data.get('files', [])

        # Process each uploaded file and identify test cases
        processed_files = []
        for i, file_info in enumerate(files):
            # Simulate analyzing file content to determine number of test cases
            # In reality, you might parse the file content here
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info['path'])

            # For demonstration, assume each file contains 1 test case
            # You can enhance this to actually parse the file content
            test_case_name = file_info['name'].replace('.txt', '').replace('.docx', '').replace('.pdf', '')

            processed_files.append({
                'id': i + 1,
                'name': test_case_name,
                'original_filename': file_info['name'],
                'status': 'processed',
                'test_cases': f"1 test case identified",
                'file_path': file_path
            })

        return jsonify({
            'success': True,
            'processed_files': processed_files,
            'total_test_cases': len(processed_files),
            'message': f'Test ingestion completed successfully. Found {len(processed_files)} test case(s)'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ingestion error: {str(e)}'})


@app.route('/generate', methods=['POST'])
def generate_code():
    """Generate Python test code for all test cases"""
    global uploaded_files_global
    global generated_scripts_info

    try:
        data = request.get_json()
        print(f"Generate request data: {data}")

        # Clear old scripts
        folder_path = app.config['GENERATED_SCRIPTS_FOLDER']
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"[INFO] Deleted old script: {file_path}")
                except Exception as e:
                    print(f"[ERROR] Failed to delete {file_path}: {e}")
            try:
                os.rmdir(folder_path)
                print(f"[INFO] Deleted folder: {folder_path}")
            except:
                pass
        else:
            print(f"[INFO] Folder '{folder_path}' does not exist. Skipping cleanup.")

        # Run Auto_test_gen.py to generate scripts
        print(f"Executing Auto_test_gen.py")
        script_path = os.path.join(os.getcwd(), "..", "Backend", "Auto_test_gen.py")
        print(f"DEBUG: App.py current directory: {os.getcwd()}")
        print(f"DEBUG: Looking for Auto_test_gen.py at: {script_path}")
        print(f"DEBUG: Auto_test_gen.py exists: {os.path.exists(script_path)}")
        #output = subprocess.run(["python3", os.path.join(os.getcwd(), "Backend", "Auto_test_gen.py")], capture_output=True, text=True)
        output = subprocess.run(["python3", os.path.join(os.getcwd(), "..", "Backend", "Auto_test_gen.py")],
                                capture_output=True, text=True)
        print(f"Auto_test_gen.py completed")
        print(f"DEBUG: Subprocess return code: {output.returncode}")
        print(f"DEBUG: Subprocess stderr: '{output.stderr}'")
        print("STDOUT:", output.stdout)

        # Extract all generated script names
        matches = re.findall(r"Script generated\s*:\s*(\S+\.py)", output.stdout)

        if not matches:
            return jsonify({'success': False, 'message': 'No scripts were generated.'})

        # Read all generated scripts
        generated_scripts_info = []
        script_folder = app.config['GENERATED_SCRIPTS_FOLDER']
        print(f"DEBUG: App looking for scripts in: {script_folder}")
        print(f"DEBUG: Generated scripts folder exists: {os.path.exists(script_folder)}")

        for i, script_name in enumerate(matches):
            file_path = os.path.join(script_folder, script_name)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        script_content = f.read()

                    # Extract test case name from script name
                    test_case_name = script_name.replace('.py', '').replace('_', ' ').title()

                    generated_scripts_info.append({
                        'id': i + 1,
                        'script_name': script_name,
                        'test_case_name': test_case_name,
                        'file_path': file_path,
                        'code': f'# Generated Python Test Code - {script_name}\n# Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n{script_content}'
                    })
                except Exception as e:
                    generated_scripts_info.append({
                        'id': i + 1,
                        'script_name': script_name,
                        'test_case_name': script_name.replace('.py', ''),
                        'file_path': file_path,
                        'code': f"Error reading file {script_name}: {str(e)}"
                    })
            else:
                generated_scripts_info.append({
                    'id': i + 1,
                    'script_name': script_name,
                    'test_case_name': script_name.replace('.py', ''),
                    'file_path': '',
                    'code': f"Script {script_name} was listed but not found on disk."
                })

        return jsonify({
            'success': True,
            'generated_scripts': generated_scripts_info,
            'total_scripts': len(generated_scripts_info),
            'message': f'Successfully generated {len(generated_scripts_info)} Python test script(s)'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Generation error: {str(e)}'})


@app.route('/save_code', methods=['POST'])
def save_code():
    """Save generated code to file system"""
    global generated_scripts_info

    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        test_case_id = data.get('test_case_id', None)
        test_case_name = data.get('test_case_name', 'general')

        if not code:
            return jsonify({'success': False, 'message': 'No code to save!'})

        if test_case_id is not None and test_case_id <= len(generated_scripts_info):
            # Multi-test case mode - save specific script
            script_info = generated_scripts_info[test_case_id - 1]
            filepath = script_info['file_path']
            filename = script_info['script_name']
        else:
            # Single test case mode or fallback
            script_dir = app.config['GENERATED_SCRIPTS_FOLDER']
            os.makedirs(script_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"autotest_{timestamp}.py"
            filepath = os.path.join(script_dir, filename)

        # Write the code to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)

        return jsonify({
            'success': True,
            'message': f'Python code saved as {filename}',
            'filename': filename,
            'filepath': filepath
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving file: {str(e)}'})


def remove_ansi_codes(text):
    """Function to strip ANSI escape codes (color codes) from terminal output"""
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


@app.route('/execute', methods=['POST'])
def execute_code():
    """Execute all generated test scripts on remote RPI via SSH"""
    global generated_scripts_info

    try:
        data = request.get_json()
        test_case_id = data.get('test_case_id', None)

        # RPI connection details
        rpi_list = [
            {"host": "71.185.253.158", "user": "root", "pass": ""},
            {"host": "65.78.96.246", "user": "root", "pass": ""}
        ]

        MAX_RETRIES = 3
        RETRY_DELAY = 3
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connected = False
        connected_host = None

        # Try to connect to any available RPI
        for attempt in range(MAX_RETRIES):
            print(f"[INFO] Connection attempt {attempt + 1}")
            for rpi in rpi_list:
                try:
                    print(f"[INFO] Connecting to {rpi['host']}...")
                    ssh.connect(rpi["host"], username=rpi["user"], password=rpi["pass"], timeout=5)
                    connected = True
                    connected_host = rpi["host"]
                    print(f"[INFO] Connected to {rpi['host']}")
                    break
                except Exception as e:
                    print(f"[ERROR] Connection to {rpi['host']} failed: {e}")
            if connected:
                break
            time.sleep(RETRY_DELAY)

        if not connected:
            return jsonify({'success': False, 'message': 'Failed to connect to any Raspberry Pi.'})

        execution_results = []

        if test_case_id is not None:
            # Execute specific test case
            if test_case_id <= len(generated_scripts_info):
                script_info = generated_scripts_info[test_case_id - 1]
                result = execute_single_script(ssh, script_info)
                execution_results.append(result)
            else:
                ssh.close()
                return jsonify({'success': False, 'message': f'Test case {test_case_id} not found.'})
        else:
            # Execute all test cases
            script_folder = app.config['GENERATED_SCRIPTS_FOLDER']
            if not os.path.isdir(script_folder):
                ssh.close()
                return jsonify({'success': False, 'message': 'Generated scripts folder does not exist.'})

            # Execute each generated script
            for script_info in generated_scripts_info:
                if os.path.isfile(script_info['file_path']):
                    result = execute_single_script(ssh, script_info)
                    execution_results.append(result)

        ssh.close()

        return jsonify({
            'success': True,
            'connected_host': connected_host,
            'execution_results': execution_results,
            'total_executed': len(execution_results),
            'message': f'Successfully executed {len(execution_results)} test script(s)'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Execution error: {str(e)}'})


def execute_single_script(ssh, script_info):
    """Execute a single script on the remote RPI"""
    try:
        with open(script_info['file_path'], 'r') as f:
            script_content = f.read()

        remote_path = f"/tmp/{script_info['script_name']}"
        print(f"[INFO] Uploading {script_info['script_name']} to {remote_path}")

        # Upload script content via echo command
        escaped_script = script_content.replace("'", "'\"'\"'")
        command = f"echo '{escaped_script}' > {remote_path} && chmod +x {remote_path}"
        ssh.exec_command(command)

        # Execute the script
        print(f"[INFO] Executing {script_info['script_name']}")
        stdin, stdout, stderr = ssh.exec_command(f"python3 {remote_path}")
        execution_output = stdout.read().decode()
        error_output = stderr.read().decode()

        return {
            'test_case_id': script_info['id'],
            'script_name': script_info['script_name'],
            'test_case_name': script_info['test_case_name'],
            'stdout': remove_ansi_codes(execution_output),
            'stderr': remove_ansi_codes(error_output),
            'success': len(error_output.strip()) == 0
        }

    except Exception as e:
        return {
            'test_case_id': script_info['id'],
            'script_name': script_info['script_name'],
            'test_case_name': script_info['test_case_name'],
            'stdout': '',
            'stderr': f'Execution error: {str(e)}',
            'success': False
        }


@app.route('/review', methods=['POST'])
def review_code():
    """Review Python code quality for individual or all test cases"""
    try:
        data = request.get_json()
        test_case_id = data.get('test_case_id', None)

        # Run tox for code quality analysis
        print("[INFO] Running tox for code quality analysis...")
        run_tox = subprocess.run(["tox"], capture_output=True, text=True)

        # Read the summary file
        summary_path = os.path.join(os.getcwd(), 'reports', 'summary.txt')
        summary_content = ""

        try:
            with open(summary_path, 'r') as f:
                summary_content = f.read()
        except FileNotFoundError:
            summary_content = "Summary file not found. Code analysis may have failed."

        if test_case_id is not None:
            # Generate review for specific test case
            review_report = f"""=== PYTHON CODE REVIEW REPORT ===
Test Case ID: {test_case_id}
Review Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Language: Python

{summary_content}

=== INDIVIDUAL TEST CASE ANALYSIS ===
This analysis covers Test Case {test_case_id} specifically.

Status: Click on "Open Report" or "Download Report" for detailed analysis results.

Note: This review includes syntax validation, PEP 8 compliance, security analysis, and static code analysis."""
        else:
            # Generate review for all test cases
            review_report = f"""=== PYTHON CODE REVIEW REPORT ===
Review Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Language: Python
Total Test Cases Analyzed: {len(generated_scripts_info)}

{summary_content}

=== COMPREHENSIVE ANALYSIS ===
This analysis covers all generated test scripts:
{chr(10).join([f"- {script['script_name']}: {script['test_case_name']}" for script in generated_scripts_info])}

Status: Click on "Open Report" or "Download Report" for detailed analysis results.

Note: This review includes syntax validation, PEP 8 compliance, security analysis, and static code analysis for all test cases."""

        return jsonify({
            'success': True,
            'review_report': review_report,
            'message': 'Python code review completed successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Review error: {str(e)}'})


@app.route('/open-report')
def open_report():
    """Open the combined HTML report"""
    try:
        return send_from_directory(app.config['REPORT_FOLDER'], 'combinedreport.html')
    except Exception as e:
        return jsonify({'success': False, 'message': f'View report error: {str(e)}'})


@app.route('/download-report')
def download_report():
    """Download the combined HTML report"""
    try:
        return send_from_directory(app.config['REPORT_FOLDER'], 'combinedreport.html', as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Download error: {str(e)}'})


@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'message': 'File too large. Maximum size is 16MB.'}), 413


@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])