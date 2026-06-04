import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    original_len = len(content)
    
    if filepath.suffix == '.py':
        
        content = re.sub(r'\"\"\"[\s\S]*?\"\"\"', '', content)
        content = re.sub(r"\'\'\'[\s\S]*?\'\'\'", '', content)
        
        content = re.sub(r'
    elif filepath.suffix in ['.html', '.css', '.js']:
        
        content = re.sub(r'<!--[\s\S]*?-->', '', content)
        
        # pyrefly: ignore [parse-error]
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        
        content = re.sub(r'//.*', '', content)
        
    
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if len(content) != original_len:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Cleaned {filepath.relative_to(PROJECT_ROOT)}")

for ext in ['*.py', '*.html', '*.css', '*.js']:
    for filepath in PROJECT_ROOT.rglob(ext):
        if '.venv' not in str(filepath) and '__pycache__' not in str(filepath):
            process_file(filepath)

print("Done removing comments.")
