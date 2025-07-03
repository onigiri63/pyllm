import json
import subprocess
import os
import re
import time
import sys

# model = 'wizardlm2:7b'
# model = 'deepseek-coder-v2'
# model = 'mistral'
# model = 'codellama:13b'
# model = 'llama3.2'
model = 'llama3.2_32k'

if len(sys.argv) > 1:
    arg1 = sys.argv[1]
    model = f'{arg1}'

baseDir = '/mnt/c/git/steps2-web-ui/src'
url = 'http://localhost:11434/api/generate'

payload = {
        'model': f'{model}',
        'prompt': """
For each .component.ts file, write a corresponding jasmine test 'spec.ts' file that tests the component's functionality.

The input format for deprecated imports is:
[
  { "import_name": "<value>", "module_name": "<value>", "replacedBy": "<value>" },
  ...
]

⚠️ UNDER NO CIRCUMSTANCES should any deprecated imports listed in the array be used in the generated code.
If an import is deprecated, use the recommended `replacedBy` alternative instead.

The list of deprecated imports and the TypeScript source code will follow.
They are separated by the delimiter:

<--->

Proceed only after the delimiter and return only valid test code.

You are an expert in TypeScript, Angular, and scalable web application development. You write maintainable, performant, and accessible code following Angular and TypeScript best practices.
## TypeScript Best Practices
- Use strict type checking
- Prefer type inference when the type is obvious
- Avoid the `any` type; use `unknown` when type is uncertain
## Angular Best Practices
- Always use standalone components over NgModules
- Don't use explicit `standalone: true` (it is implied by default)
- Use signals for state management
- Implement lazy loading for feature routes
- Use `NgOptimizedImage` for all static images.
## Components
- Keep components small and focused on a single responsibility
- Use `input()` and `output()` functions instead of decorators
- Use `computed()` for derived state
- Set `changeDetection: ChangeDetectionStrategy.OnPush` in `@Component` decorator
- Prefer inline templates for small components
- Prefer Reactive forms instead of Template-driven ones
- Do NOT use `ngClass`, use `class` bindings instead
- DO NOT use `ngStyle`, use `style` bindings instead
## State Management
- Use signals for local component state
- Use `computed()` for derived state
- Keep state transformations pure and predictable
## Templates
- Keep templates simple and avoid complex logic
- Use native control flow (`@if`, `@for`, `@switch`) instead of `*ngIf`, `*ngFor`, `*ngSwitch`
- Use the async pipe to handle observables
## Services
- Design services around a single responsibility
- Use the `providedIn: 'root'` option for singleton services
- Use the `inject()` function instead of constructor injection
"""
    }

def estimate_token_count(text: str) -> int:
    """
    Approximate token count by splitting on whitespace and punctuation.
    This is NOT an exact LLM tokenizer, but works without dependencies.

    Parameters:
        text (str): The input string.

    Returns:
        int: Estimated number of tokens.
    """
    # Split on words and punctuation (approximate GPT-like token behavior)
    tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    return len(tokens)

def create_deprecated_dict_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    # print(data)
    return data
    # deprecated_dict = {item['module_name']: item['import_name'] for item in data}
    # return deprecated_dict

def remove_leading_word_and_trailing_quotes(input_string):
    if input_string.startswith("typescript"):
        input_string = input_string  [len("typescript"):len(input_string) ]

    while input_string.endswith("`"):
        input_string = input_string[:-1]

    return input_string

def removeExtension(filename):
    return filename[:filename.rfind('.ts')]

def file_exists_in_directory(directory: str, filename: str) -> bool:
    try:
        return filename in os.listdir(directory)
    except FileNotFoundError:
        return False

def scan_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.ts'):
                file_path = os.path.join(root, file)
                noex = removeExtension(file_path)
                if (noex.rfind('.spec') != -1 or file_exists_in_directory(file_path[:file_path.rfind('.ts')], noex + '.spec.ts')):
                    continue 
                print(f"Processing {file_path}")
                with open(file_path, 'r') as f: 
                    content = f.read()
                deprecated = str(create_deprecated_dict_from_file('deprecated.txt')) + '---'
                payload['prompt'] = payload['prompt'] + deprecated + content
                print(f"Token count: {estimate_token_count(payload['prompt'])}")
                # print(json.dumps(payload))
                out = ['curl','--location', url, '--data', json.dumps(payload)]
                response = query_llm(out)
                print(response)
                outfile = open(noex + '.spec.ts','w')
                
                outfile.write(remove_leading_word_and_trailing_quotes(response))


def query_llm(cmd):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Optional: merge stderr into stdout
        text=True,                # Ensures strings are returned, not bytes
        bufsize=1,                # Line-buffered
        universal_newlines=True   # Alias for text=True, ensures line endings handled properly
    )
    # time.sleep(1)  # Give the process a moment to start

    responses = []
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
            if 'response' in parsed:
                responses.append(parsed['response'])
        except json.JSONDecodeError as e:
            print(f"{line}")
        print('.', end='', sep='', flush=True)

    process.stdout.close()
    process.wait()
    print(responses)
    full_response = ''.join(responses)
    return full_response

if __name__ == "__main__":
    scan_directory(baseDir)

