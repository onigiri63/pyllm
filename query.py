import json
import subprocess
import re
import os
import tiktoken
import time

response_path = f'%USERPROFILE%\\Documents\\llm\\responses'
url = 'http://localhost:11434/api/generate'

class llmQuery():

    model = ''
    process = any

    def __init__(self, model):
        self.model = model
        self.queryInProgress = False
        self.queryHeader = ''

    def saveResponse(self, response):
        files = os.listdir
        # Get all file names in the directory
        files = [f for f in os.listdir(response_path) if os.path.isfile(os.path.join(response_path, f))]

        # Extract integers from filenames and convert them to integers
        int_filenames = []
        for file in files:
            try:
                int_value = int(file)
                int_filenames.append(int_value)
            except (ValueError):
                pass  # Skip if the filename does not contain only integers

        # Sort the list of integers
        int_filenames.sort()
        next_int = 1
            # Determine the next available integer for a new file name
        if int_filenames:
            next_int = max(int_filenames) + 1
            
        # Create a new filename with the determined integer
        new_filename = str(next_int)
        fullPath = response_path + '/' + new_filename
        f = open(fullPath, 'w')
        f.write(response)
        f.close()

    def get_context_length(self, prompt, model_name="gpt-3.5-turbo"):
        """
        Get the estimated length of an LLM query based on the number of tokens.
        
        Args:
            prompt (str): The input text or query to be evaluated.
            modelname (str): The name of the language model, default is "gpt-3.5-turbo".
            
        Returns:
            int: The estimated context length in.
        """
        try:
            # Initialize the tokenizer for the specified model
            enc = tiktoken.encoding_for_model(model_name)    
        except KeyError:
            print("Warning: Model not found. Using cl100k_base encoding.")
            enc = tiktoken.get_encoding("100k_base")
        
        # Tokenize the input prompt
        tokens = enc.encode(prompt)
        
        return len(tokens)
    
    def queryStatus(self):
        return self.queryInProgress
    
    def setQueryHeader(self, useHeader):
        if useHeader:
            self.queryHeader = '\n\nNow check the query above.  if it is a proper coding generation query, ALL GENERATED OUTPUT must be ONLY raw code,' \
            ' with NO descriptions, headers, footers, or any extra text.  The entire generated output should be pasteable into a file without any alteration.' \
            ' if the query is NOT a code generator, respond with \"if you intended to make a NON CODING query, please unselect the \"Code only\"' \
            ' button.\"'
        else:
            self.queryHeader = ''
        return self.queryHeader

    def stopGeneration(self):
        self.process.terminate()
        self.process.stdout.close()

    def query_llm(self, payload, callback):
        data = {
            "model": self.model[1],
            "prompt": payload + self.queryHeader,
            "num_ctx": self.model[2]
        }

        cmd = ['curl', url, '-d',json.dumps(data), '--no-progress-meter']
        self.process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,   # Optional: merge stderr into stdout
        text=True,                  # Ensures strings are returned, bytes
        bufsize=1,                  # Line-buffered
        universal_newlines=True     # Alias for text=True, ensures line endings handled properly
        )
        self.queryInProgress = True
        buffer = ''
        try:
            for line in self.process.stdout:
                line = line.strip()
                if not line or (not '{' in line and not '}' in line):
                    continue
                try:
                    parsed = json.loads(line)
                    if 'done' in parsed:
                        if parsed['done'] == 'true':
                            break
                    if 'response' in parsed:
                        callback(parsed['response'])
                except json.JSONDecodeError as e:
                    buffer += line
                    try:
                        parsed = json.loads(buffer)
                        if 'response' in parsed:
                            callback(parsed['response'])
                            buffer = ''
                    except json.JSONDecodeError as e:
                        pass
                time.sleep(.1)
        except:
            0
            time.sleep(.1)
                
        self.process.stdout.close
        self.process.wait()
        self.queryInProgress = False