import os
import textile
import glob
import re
from datetime import datetime


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


def get_analyzed_scripts():
    """Get list of all analyzed Python scripts"""
    scripts = glob.glob("generated-scripts/*.py")
    script_info = []

    for script_path in scripts:
        script_name = os.path.basename(script_path)
        # Convert script name to readable test case name
        test_case_name = script_name.replace('.py', '').replace('_', ' ').title()
        script_info.append({
            'file': script_name,
            'path': script_path,
            'name': test_case_name
        })

    return script_info


def extract_script_specific_issues(tool_output, script_name):
    """Extract issues specific to a particular script from tool output"""
    if not tool_output or not script_name:
        return "No issues found for this script."

    lines = tool_output.split('\n')
    script_issues = []

    for line in lines:
        # Check if line contains the script name (various formats)
        if script_name in line or f"generated-scripts/{script_name}" in line:
            script_issues.append(line)
        # For pylint, also check for lines that start with the script path
        elif line.startswith(f"generated-scripts/{script_name}:"):
            script_issues.append(line)

    if script_issues:
        return '\n'.join(script_issues)
    else:
        # If no script-specific issues found, it might mean no issues for this script
        return "No issues found for this script."


def read_tool_output(tool_file):
    """Read tool output file and return content"""
    if os.path.exists(tool_file):
        try:
            with open(tool_file, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading {tool_file}: {e}"
    return ""


def txt_html_converter(content, add_pre_tags=True):
    """Convert text content to HTML"""
    if not content.strip():
        return "<p><em>No issues found or no output generated.</em></p>"

    if add_pre_tags:
        # For code analysis output, preserve formatting
        return f"<pre>{content}</pre>"
    else:
        # For other content, use textile
        return textile.textile(content)


def create_organized_html_report(output_file):
    """Create HTML report organized by individual test cases"""
    delete_combined_report()

    # Get all analyzed scripts
    analyzed_scripts = get_analyzed_scripts()

    if not analyzed_scripts:
        print("No analyzed scripts found.")
        return

    # Read tool outputs
    tool_outputs = {
        'flake8': read_tool_output('reports/flake8_output.txt'),
        'pylint': read_tool_output('reports/pylint_output.txt'),
        'black': read_tool_output('reports/black_output.txt'),
        'bandit': read_tool_output('reports/bandit_output.html')  # bandit outputs HTML
    }

    # Read summary
    summary_content = read_tool_output('reports/summary.txt')

    # Start building HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Multi-Test Code Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }}
        h2 {{ color: #007acc; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        h3 {{ color: #555; margin-top: 25px; }}
        .timestamp {{ color: #666; font-style: italic; }}
        .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007acc; }}
        .test-case {{ background-color: #fafafa; margin: 30px 0; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }}
        .test-case-header {{ background-color: #007acc; color: white; padding: 10px 15px; margin: -20px -20px 20px -20px; border-radius: 8px 8px 0 0; }}
        .tool-section {{ margin: 20px 0; padding: 15px; background-color: white; border-radius: 5px; border-left: 3px solid #ccc; }}
        .tool-section h4 {{ color: #333; margin-top: 0; }}
        .flake8 {{ border-left-color: #ff6b6b; }}
        .pylint {{ border-left-color: #4ecdc4; }}
        .black {{ border-left-color: #45b7d1; }}
        .bandit {{ border-left-color: #f9ca24; }}
        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; font-size: 12px; }}
        .no-issues {{ color: #28a745; font-style: italic; }}
        .table-of-contents {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .table-of-contents ul {{ margin: 0; padding-left: 20px; }}
        .navigation {{ position: sticky; top: 10px; background-color: #007acc; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        .navigation a {{ color: white; text-decoration: none; margin-right: 15px; }}
        .navigation a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="navigation">
        <strong>Quick Navigation:</strong>
        <a href="#summary">Summary</a>
        <a href="#test-cases">Test Cases</a>
        <a href="#collective-analysis">Collective Analysis</a>
    </div>

    <h1>Multi-Test Code Quality Analysis Report</h1>
    <p class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Total Test Cases Analyzed:</strong> {len(analyzed_scripts)}</p>
"""

    # Add Executive Summary
    html_content += f"""
    <div id="summary" class="summary">
        <h2>Executive Summary</h2>
        <pre>{summary_content if summary_content else 'Summary not available.'}</pre>
    </div>
"""

    # Add Table of Contents
    html_content += """
    <div class="table-of-contents">
        <h2>Table of Contents</h2>
        <ul>
"""
    for i, script in enumerate(analyzed_scripts, 1):
        html_content += f'            <li><a href="#test-case-{i}">{script["name"]} ({script["file"]})</a></li>\n'

    html_content += """        </ul>
    </div>
"""

    # Add individual test case analysis
    html_content += '<div id="test-cases">\n    <h2>Individual Test Case Analysis</h2>\n'

    for i, script in enumerate(analyzed_scripts, 1):
        html_content += f"""
    <div id="test-case-{i}" class="test-case">
        <div class="test-case-header">
            <h3>Test Case {i}: {script['name']}</h3>
            <p><strong>Script File:</strong> {script['file']}</p>
        </div>
"""

        # Add analysis for each tool
        tools = [
            ('flake8', 'Flake8 - Style & Lint Checks', 'PEP 8 compliance and style issues'),
            ('pylint', 'Pylint - Static Code Analysis', 'Code quality and potential bugs'),
            ('black', 'Black - Code Formatting', 'Code formatting analysis'),
            ('bandit', 'Bandit - Security Analysis', 'Security vulnerability scanning')
        ]

        for tool_key, tool_title, tool_desc in tools:
            tool_output = tool_outputs.get(tool_key, '')

            if tool_key == 'bandit':
                # Bandit outputs HTML, so handle differently
                script_issues = tool_output if script[
                                                   'file'] in tool_output else "No security issues found for this script."
                is_html = True
            else:
                script_issues = extract_script_specific_issues(tool_output, script['file'])
                is_html = False

            html_content += f"""
        <div class="tool-section {tool_key}">
            <h4>{tool_title}</h4>
            <p><em>{tool_desc}</em></p>
"""

            if script_issues and script_issues.strip() and "No issues found" not in script_issues:
                if is_html:
                    html_content += f'            <div>{script_issues}</div>\n'
                else:
                    html_content += f'            <pre>{script_issues}</pre>\n'
            else:
                html_content += '            <p class="no-issues">✅ No issues found for this script.</p>\n'

            html_content += '        </div>\n'

        html_content += '    </div>\n'

    html_content += '</div>\n'

    # Add collective analysis section
    html_content += f"""
<div id="collective-analysis">
    <h2>Collective Analysis - All Test Cases</h2>
    <p><em>This section shows the complete output from all analysis tools across all test cases.</em></p>
"""

    collective_tools = [
        ('flake8', 'Flake8 - Complete Output', tool_outputs['flake8']),
        ('pylint', 'Pylint - Complete Output', tool_outputs['pylint']),
        ('black', 'Black - Complete Output', tool_outputs['black']),
        ('bandit', 'Bandit - Complete Output', tool_outputs['bandit'])
    ]

    for tool_key, title, content in collective_tools:
        html_content += f"""
    <div class="tool-section {tool_key}">
        <h3>{title}</h3>
"""
        if content and content.strip():
            if tool_key == 'bandit':
                html_content += f'        <div>{content}</div>\n'
            else:
                html_content += f'        <pre>{content}</pre>\n'
        else:
            html_content += '        <p class="no-issues">No output generated.</p>\n'

        html_content += '    </div>\n'

    html_content += """
</div>

<footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center;">
    <p>Report generated by CTS AutoTest Multi-Test Code Review System</p>
</footer>

</body>
</html>
"""

    # Write the final HTML file
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write(html_content)
        print(f"Organized HTML report created: {output_file}")
    except Exception as e:
        print(f"Error creating organized report: {e}")


def clean_reports_folder():
    reports_folder = "reports/"
    ignored_files = ["combinedreport.html", "summary.txt"]
    if os.path.exists(reports_folder):
        files_removed = 0
        for filename in os.listdir(reports_folder):
            file_path = os.path.join(reports_folder, filename)
            try:
                if filename in ignored_files:
                    continue
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    files_removed += 1
                    print(f"Removed file: {file_path}")
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")
        print(f"Cleanup completed: {files_removed} temporary files removed")
    else:
        print(f"Reports folder '{reports_folder}' does not exist.")


# Main execution
if __name__ == "__main__":
    output_file = "reports/combinedreport.html"

    print("Starting organized HTML report generation...")

    # Create organized report
    create_organized_html_report(output_file)

    # Clean up temporary files
    clean_reports_folder()

    print("Organized HTML report generation completed!")