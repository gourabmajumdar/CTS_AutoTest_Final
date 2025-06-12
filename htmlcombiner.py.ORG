import os
import textile

def delete_combined_report():
    combined_report_path = "reports/combinedreport.html"
    if os.path.exists(combined_report_path):
        try:
            os.remove(combined_report_path)
            print(f"Removed file: {combined_report_path}")
        except FileNotFoundError:
            pass
    else:
        print(f"File '{combined_report_path}' does not exist.")

def txt_html_converter(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    html_content = textile.textile(content)
    with open(output_file, 'w', encoding='utf-8') as file: #PD
        file.write(html_content) #PD

def combine_html_files(input_folder, output_file):
    combine_html = ""
    delete_combined_report()
    
    # Define the explicit processing order
    processing_order = [
        "bandit_output.html",        # Security scanner first
        "black_output.html",   # Formatter second
        "flake8_output.html",  # Linter third
        "pylint_output.html"   # Static analysis last
    ]
    
    try:
        # Process files in predefined order
        for filename in processing_order:
            file_path = os.path.join(input_folder, filename)
            if os.path.exists(file_path):
                if filename == "bandit_output.html":
                    combine_html += "<h2>Bandit - Security Analysis:</h2>\n"
                elif filename == "black_output.html":
                    combine_html += "<h2>Black - Code Formatting:</h2>\n"
                elif filename == "flake8_output.html":
                    combine_html += "<h2>Flake8 - Style & Lint Checks:</h2>\n"
                elif filename == "pylint_output.html":
                    combine_html += "<h2>Pylint - Static Code Analysis:</h2>\n"
                    combine_html += "<p><em>Pylint Scoring Info:</em> A minimum score threshold of <strong>8.0</strong> has been set using <code>--fail-under=8.0</code>. This ensures basic code quality without enforcing strict compliance.</p>\n"

                with open(file_path, 'r', encoding='utf-8') as file:
                    combine_html += file.read() + "\n"
                print(f"Processed: {filename}")
            else:
                print(f"Warning: {filename} not found - skipped")
                
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write(combine_html)
            
    except FileNotFoundError:
        print(f"Error: The folder '{input_folder}' does not exist.")
        return

def clean_reports_folder():
    reports_folder = "reports/"
    ignored_files = ["combinedreport.html", "summary.txt"]
    if os.path.exists(reports_folder):
        for filename in os.listdir(reports_folder):
            file_path = os.path.join(reports_folder, filename)
            try:
                if filename in ignored_files:
                    continue
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")
    else:
        print(f"Reports folder '{reports_folder}' does not exist.")

input_folder = "reports/"
output_file = "reports/combinedreport.html"

# Convert text reports to HTML (order doesn't matter here)
txt_html_converter("reports/black_output.txt", "reports/black_output.html")
txt_html_converter("reports/pylint_output.txt", "reports/pylint_output.html")
txt_html_converter("reports/flake8_output.txt", "reports/flake8_output.html")

# Combine in explicit order
combine_html_files(input_folder, output_file)
clean_reports_folder()

