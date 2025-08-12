import json
import subprocess
import threading
import time
import helpers
from objectTypes import MessageList

'''
This version is in progress:
chat live instead of single prompts.
'''

chatURL = 'http://localhost:11434/api/chat'

class llmChat():
    model = ''
    
    def __init__(self, model):
        self.model = model
        self.queryInProgress = False
        self.queryHeader = ''
        self.messageLock = threading.Lock()
        self.messages = MessageList()
        self.process = any
    
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
        try:
            self.process.stdout.close()
            self.process.terminate()
        except Exception as e:
            print(f"unable to stop process: {e}")

    def tokenCount(self):
        count = len(self.queryHeader)
        for message in self.messages.getMessages():
            self.messageLock.acquire()
            count += helpers.get_context_length(message['content'])
            self.messageLock.release()
        return count

    def send_chat(self, payload, callback):
        self.messageLock.acquire()
        self.messages.addMessage("user",payload )
        self.messageLock.release()

        command = { "model": self.model[1], "messages": self.messages.getMessages() }
        # print(json.dumps(command))
        cmd = ['curl', chatURL, '-d',json.dumps(command), '--no-progress-meter']
        self.queryInProgress = True
        buffer = ''
        self.process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        bufsize=1,
        universal_newlines=True )
        try:
            for line in self.process.stdout:
                line = line.strip()
                print(line)
                try:
                    parsed = json.loads(line)
                    if 'done' in parsed:
                        if parsed['done'] == 'true':
                            break
                    if 'message' in parsed:
                        print(parsed['message']['content'])
                        callback(parsed['message']['content'])
                        buffer += parsed['message']['content']
                except json.JSONDecodeError as e:
                    pass
                time.sleep(.05)
        except:
            pass
            time.sleep(.05)
        self.messageLock.acquire()
        self.messages.addMessage("assistant", buffer )
        self.messageLock.release()
        
        self.queryInProgress = False

    def loadMessage(self, role, message):
        self.messages.addMessage(role, message)