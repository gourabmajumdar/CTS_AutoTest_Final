import subprocess
import yaml
import glob
import os
from datetime import datetime

# Load configuration from YAML
with open("config.yaml", "r", encoding="utf8") as file:
    config = yaml.safe_load(file)


def get_all_script_files():
    """Gets all Python files in the scripts directory."""
    files = glob.glob("generated-scripts/*.py")
    if not files:
        print("No Python files found in generated-scripts directory.")
        return []

    print(f"Found {len(files)} script files:")
    for file in files:
        print(f"  - {file}")
    return files


def get_latest_file():
    """Finds the latest file in the scripts directory for backward compatibility."""
    files = glob.glob("generated-scripts/*.py")
    if not files:
        print("No Python files found in generated-scripts directory.")
        return None
    latest_file = max(files, key=lambda x: os.path.getctime(x))
    print(f"Latest file: {latest_file}")
    updated_file_path = latest_file.replace("\\", "/")
    return updated_file_path


# runs command while ignoring errors
def run_command(command):
    """Executes a shell command and prints output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding="utf-8")
    print(result.stdout)
    if result.stderr:
        pass
    return result


def run_command_to_file(command, output_file):
    """Executes a command and writes output to file."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding="utf-8")
    with open(output_file, "w", encoding="utf8") as file:
        file.write(result.stdout)
        if result.stderr:
            file.write(f"{result.stderr}\n")
    return result


def create_reports_folder():
    """Creates the reports folder if it does not exist."""
    if not os.path.exists("reports"):
        os.makedirs("reports")
        print("Created reports folder.")
    else:
        print("Reports folder already exists.")


'''def write_summary(results, analyzed_files):
    """Writes a summary of linter results to summary.txt"""
    with open("reports/summary.txt", "w", encoding="utf8") as f:
        f.write("CODE REVIEW SUMMARY\n")
        f.write("=" * 20 + "\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Files analyzed: {len(analyzed_files)}\n")
        for file in analyzed_files:
            f.write(f"  - {file}\n")
        f.write("\n")

        for tool, data in results.items():
            f.write(f"{tool.upper()}:\n")
            f.write(f"  Return Code: {data['returncode']}\n")
            f.write(f"  Status: {'Success' if data['success'] else 'Issues Found'}\n")
            if 'issues_count' in data:
                f.write(f"  Issues Found: {data['issues_count']}\n")
            f.write("\n")
'''

def write_summary(results, analyzed_files):
    """Simple version - adds icons to existing summary format with special pylint handling"""
    with open("reports/summary.txt", "w", encoding="utf8") as f:
        f.write("CODE REVIEW SUMMARY\n")
        f.write("=" * 20 + "\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Files analyzed: {len(analyzed_files)}\n")
        for file in analyzed_files:
            f.write(f"  - {file}\n")
        f.write("\n")

        for tool, data in results.items():
            # Special logic for pylint - use red cross for issues, amber for others
            if data['success']:
                icon = "✅"
            elif 'pylint' in tool.lower():
                icon = "❌"  # Red cross for pylint issues
            else:
                icon = "⚠️"  # Amber warning for other tools

            f.write(f"{tool.upper()}: {icon}\n")
            f.write(f"  Return Code: {data['returncode']}\n")
            f.write(f"  Status: {'Success' if data['success'] else 'Issues Found'}\n")
            f.write("\n")

# Main execution
create_reports_folder()

# Get all script files to analyze
all_files = get_all_script_files()
if not all_files:
    print("No files to analyze. Exiting.")
    exit(1)

# For backward compatibility, if only one file, use the original logic
if len(all_files) == 1:
    target_files = all_files[0]
    file_pattern = all_files[0]
else:
    # Analyze all files
    target_files = " ".join(all_files)
    file_pattern = "generated-scripts/*.py"

print(f"Analyzing: {target_files}")

# Dictionary to store all results
results = {}

# Runs black on all files
black_options = config["linting"]["black"]
black_result = run_command_to_file(f"black {target_files} {black_options}", "reports/black_output.txt")
results['black - Code Formatting'] = {
    'returncode': black_result.returncode,
    'success': black_result.returncode == 0
}

# Runs flake8 on all files
flake8_options = config["linting"]["flake8"]
flake8_result = run_command_to_file(f"flake8 {file_pattern} {flake8_options}", "reports/flake8_output.txt")
results['flake8 - Style & Lint Checks'] = {
    'returncode': flake8_result.returncode,
    'success': flake8_result.returncode == 0
}

# Runs bandit on all files
bandit_options = config["security"]["bandit"]
bandit_result = run_command_to_file(f"bandit {file_pattern} {bandit_options}", "reports/bandit_output.txt")
results['bandit - Security Analysis'] = {
    'returncode': bandit_result.returncode,
    'success': bandit_result.returncode == 0
}

# Runs pylint on all files
pylint_options = config["linting"]["pylint"]
pylint_result = run_command_to_file(f"pylint {file_pattern} {pylint_options}", "reports/pylint_output.txt")
results['pylint - Static Code Analysis'] = {
    'returncode': pylint_result.returncode,
    'success': pylint_result.returncode == 0
}

# Write the summary file
write_summary(results, all_files)

print("Code analysis completed successfully!")
print(f"Reports generated in 'reports/' directory")
print(f"Summary available in 'reports/summary.txt'")