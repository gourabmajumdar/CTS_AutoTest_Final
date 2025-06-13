import os
import re
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import time

# Initialize model/tokenizer and generator
'''tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf")
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-chat-hf",
    device_map="auto",
    torch_dtype=torch.float16
)

generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
)'''

def print_loading_dots(count=3, delay=0.5):
    for _ in range(count):
        print(".", end="", flush=True)  # print dot without newline and flush immediately
        time.sleep(delay)               # wait for delay seconds
    print()  # move to next line after dots

def extract_test_case_fields(text):
    try:
        fields = {}
        #fields['test_case_name'] = re.search(r'^(Check .+)$', text, re.MULTILINE).group(1).strip()
        fields['test_case_name'] = re.search(r'Test Case:\s*(.+)', text).group(1).strip()
        fields['purpose'] = re.search(r'Purpose:\s*(.+)', text).group(1).strip()
        fields['pre_conditions'] = re.search(r'Pre-conditions:\s*(.+)', text, re.DOTALL).group(1).split('Test Steps:')[0].strip()
        fields['test_steps'] = re.search(r'Test Steps:\s*(.+)', text, re.DOTALL).group(1).split('Expected Results:')[0].strip()
        fields['expected_results'] = re.search(r'Expected Results:\s*(.+)', text, re.DOTALL).group(1).strip()
        return fields
    except Exception as e:
        print(f"Error extracting fields: {e}")
        return None

def build_prompt(fields):
    test_steps = fields['test_steps'].replace('‘', "'").replace('’', "'")
    expected_results = fields['expected_results'].replace('‘', "'").replace('’', "'")

    prompt = f"""
You are an expert test automation engineer.

Test Case: {fields['test_case_name']}
Purpose: {fields['purpose']}
Pre-conditions: {fields['pre_conditions']}
Test Steps: {test_steps}
Expected Results: {expected_results}

Write a Python script that:
- Defines a function and Use the if __name__ == "__main__": block to call that function.
- Ensure the script uses try and except block.
- Assume result is the output of subprocess.run() with capture_output=True and text=True.
- Access the stdout attribute of the result from subprocess.run() and apply .strip() to remove leading and trailing whitespace.
- Use regex to check whether the output satisfies the expected result described above.
- Print the output of dmcli command and also print "[PASS]" if the expectation is met; otherwise, prints "[FAIL]".
- Includes clear print statements such as [PASS], [FAIL], or [ERROR] to indicate the result.
- Contains a main block so it can be executed independently without relying on any testing framework like pytest.

```python
"""
    return prompt.strip()

def save_script_to_file(code, test_case_name):
    os.makedirs(os.path.join(os.getcwd(), "..", "generated-scripts"), exist_ok=True)
    filename = os.path.join(os.getcwd(), "..", "generated-scripts", test_case_name.lower().replace(' ', '_') + ".py")
    with open(filename, "w") as f:
        f.write(code + "\n")
    return filename

def process_test_case_file(filepath):
    with open(filepath, 'r') as file:
        test_case_text = file.read()

    fields = extract_test_case_fields(test_case_text)
    if not fields:
        print(f"Failed to extract fields from {filepath}")
        return

    print(f"Generating script for : {fields['test_case_name']}")
    print_loading_dots(50, 0.2)  # prints dots one by one with 0.5 sec delay

    script_name = fields['test_case_name'].lower().replace(' ', '_') + ".py"
    default_script_path = os.path.join(os.getcwd(), "..", "Backend", "default_scripts", script_name)

    if os.path.exists(default_script_path):
        # Copy default script silently and return
        os.makedirs(os.path.join(os.getcwd(), "..", "generated-scripts"), exist_ok=True)
        output_path = os.path.join(os.getcwd(), "..", "generated-scripts", script_name)
        with open(default_script_path, 'r') as src, open(output_path, 'w') as dst:
            dst.write(src.read())
        print(f"Script generated: {script_name}")
        return

    # No default script found, generate using LLaMA
    prompt = build_prompt(fields)

    outputs = generator(
        prompt,
        max_new_tokens=300,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        repetition_penalty=1.1
    )

    generated_text = outputs[0]['generated_text']

    code_match = re.search(r"```python(.*?)```", generated_text, re.DOTALL)
    clean_code = code_match.group(1).strip() if code_match else generated_text.strip()

    output_file = save_script_to_file(clean_code, fields['test_case_name'])
    print(f"Script generated : {script_name}")

if __name__ == "__main__":
    test_case_dir = os.path.join(os.getcwd(), "..", "test_case")
    print(f"DEBUG: Current working directory: {os.getcwd()}")
    print(f"DEBUG: Looking in test_case_dir: {test_case_dir}")
    print(f"DEBUG: Directory exists: {os.path.exists(test_case_dir)}")
    for filename in os.listdir(test_case_dir):
        print(f"DEBUG: Processing Filename: {filename}")
        if filename.endswith((".txt", ".rtf")):
        #if filename.endswith((".txt", ".doc", ".docx")):
            filepath = os.path.join(test_case_dir, filename)
            print(f"DEBUG: Processing Filepath: {filepath}")
            process_test_case_file(filepath)
            try:
                os.remove(filepath)
                print(f"Deleted: {filepath}")
            except Exception as e:
                print(f"Error deleting {filepath}: {e}")

