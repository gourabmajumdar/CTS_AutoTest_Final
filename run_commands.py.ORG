import subprocess
import yaml
import glob
import os
from datetime import datetime

# Load configuration from YAML
with open("config.yaml", "r", encoding="utf8") as file:
    config = yaml.safe_load(file)


def most_recent_file():
    """Finds the latest file in the scripts directory. Then converts \\ to / """
    files = glob.glob("generated-scripts/*.py")
    if not files:
        print("No HTML files found in reports directory.")
        return None
    latest_file = max(files, key=lambda x: os.path.getctime(x))
    print(f"Latest file: {latest_file}")


    updated_file_path = latest_file.replace("\\", "/")
    # print (f"Updated file path: {updated_file_path}")
    return updated_file_path



#runs command while ignoring errors
def run_command(command): 
    """Executes a shell command and prints output."""
    result =subprocess.run(command, shell=True, capture_output=True, text=True, encoding="utf-8")

    print(result.stdout)
    if result.stderr:
        pass
    return result  # Added return statement to capture result

def run_black(command, output_file,): 
    """Executes black and prints output to a created file"""
    result =subprocess.run(command, shell=True, capture_output=True, text=True, encoding="utf-8")
    with open(output_file, "w", encoding="utf8") as file:
        #file.write("*Black Output*:\n")
        file.write(result.stdout)
        if result.stderr:
            file.write(f"{result.stderr}\n")
        #file.write(f"*Flake8 Output:*\n")
    return result  # Added return statement to capture result


def create_reports_folder():
    """Creates the reports folder if it does not exist."""
    if not os.path.exists("reports"):
        os.makedirs("reports")
        print("Created reports folder.")
    else:
        print("Reports folder already exists.")

#adding the following function
def write_summary(results):
    """Writes a summary of linter results to summary.txt"""



    with open("reports/summary.txt", "w", encoding="utf8") as f:
        f.write("CODE REVIEW SUMMARY\n")
        f.write("="*20 + "\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"File analyzed: {most_recent_file()}\n\n")
        
        for tool, data in results.items():
            f.write(f"{tool.upper()}:\n")
            f.write(f"  Return Code: {data['returncode']}\n")
            f.write(f"  Status: {'Success' if data['success'] else 'Issues Found'}\n\n")


latest_file =most_recent_file()
create_reports_folder()

# Dictionary to store all results
results = {}

# Runs black on the latest file, saves output in file black_output.txt
black_options = config["linting"]["black"]
black_result = run_black(f"black {latest_file} {black_options}", "reports/black_output.txt")
results['black'] = {
    'returncode': black_result.returncode,
    'success': black_result.returncode == 0
}

# Runs flake8, on the latest file
flake8_options = config["linting"]["flake8"]
flake8_result = run_command(f"flake8 {latest_file} {flake8_options}")
#print("flake8 command", flake8_result)
results['flake8'] = {
    'returncode': flake8_result.returncode,
    'success': flake8_result.returncode == 0
}


# # Runs bandit on the latest file
bandit_options = config["security"]["bandit"]
bandit_result = run_command(f"bandit {latest_file} {bandit_options}")
results['bandit'] = {
    'returncode': bandit_result.returncode,
    'success': bandit_result.returncode == 0
}

#Runs pylint on the latest file, saves output in file pylint_output.txt
pylint_options = config["linting"]["pylint"]
#START of additional lines
pylint_result = run_command(f"pylint {latest_file} {pylint_options} ")
results['pylint'] = {
    'returncode': pylint_result.returncode,
    'success': pylint_result.returncode == 0
}

# Write the summary file
write_summary(results)
#END of additional lines

run_command(f"pylint {latest_file} {pylint_options} ")
with open("reports/pylint_output.txt", 'r', encoding="utf8") as content:
    save = content.read()
with open("reports/pylint_output.txt", 'w', encoding="utf8") as content:
    #content.write("*Pylint Output:*\n")
    content.write(save)




