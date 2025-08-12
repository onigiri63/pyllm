import tkinter as tk
from tkinter import scrolledtext
import threading

from flask import json
from chat import llmChat
from graphing import DynamicPlot
import sys
import helpers
import time
from runFromFile import runFromFile
from pyperclip import copy
from ChatHistory import chatHistory
# from markup import CodeSyntaxHighlighter

'''
 TODO: 
    -add a dropdown to select the model to run
'''
# format: file name, model name, context window size
# model = ('qwen2.5coder','qwen2.5-coder:7b', '2048')
# model = ('qwen2.5coder3b','qwen2.5-coder:3b', '2048')
# model = ('qwen2-32k','qwen2-32k', '2048')
# model = ('llama3.2','llama3.2', '2048')
model = ('llama3.2-16k','llama3.2-16k', '16384')

saveDirectory = f'C:\\Users\\shika001\\Documents\\ChatHistory'
imageStoreDirectory = f'M:\\Jeff_Shikany\\ollama\\models'

class LLMQueryUI:
    onlyCode = False
    def __init__(self):
        helpers.check_docker_engine()
        self.savehistory = chatHistory(saveDirectory)
        self.events = []
        self.breakout = [False]
        self.onlyCode = False
        self.minimized = False
        self.queryStatus = False
        self.chat = llmChat(model)
        self.initControls()
        runFromFile(model, imageStoreDirectory).launch()
        buttonthread = threading.Thread(target=self.buttonStatus, args=([self.breakout]))
        buttonthread.daemon = True
        buttonthread.start()
        self.root.mainloop()

    def minimize(self):
        if self.minimized:
            return
        self.minimized = True
        self.cpuplot.minimize()
        self.memplot.minimize()
    
    def maximize(self):
        if not self.minimized:
            return
        self.minimized = False
        self.cpuplot.maximize()
        self.memplot.maximize()

    def stopLLM(self):
        self.chat.stopGeneration()

    def initControls(self):
        self.root = tk.Tk()
        # self.root.iconbitmap("iconTemplate@2x.gif")  # Set the icon for the window
        self.root.title("LLM Query Interface")
        self.root.geometry("1300x950")
        self.root.minsize(1100, 300) # sets the minimum size of the root window
        self.customfont = {"family": "Courier", "size": 10, "weight": "normal"}

        tk.Label(self.root, font=("Courier", 12), text="Enter your query:").pack(pady=5)

        self.outerFrame = tk.Frame(self.root, width=1100, height=950)
        self.outerFrame.pack(anchor=tk.NW, expand=True)
        self.outerFrame.columnconfigure(0, minsize=100)
        self.outerFrame.columnconfigure(1, weight=2)
        self.outerFrame.columnconfigure(2, weight=10, minsize=210)

        self.outerGrid = tk.Frame(self.outerFrame)
        self.outerGrid.grid(row=0, column=0, columnspan=2, padx=0, pady=0)

        self.chatHistoryColumn = tk.Frame(self.outerGrid, width=100, height=500)
        self.chatHistoryColumn.grid(column=0, row=0, sticky='nw', rowspan=100)

        chathist = self.savehistory.enumerateChats()
        index = 0
        for chat in chathist:
            button = tk.Button(self.chatHistoryColumn, bg="snow3", width=20, height=1, text=helpers.convert_unix_to_date(float(chat)), font=("Courier", 10), command=lambda chat=chat: self.loadButtonClick(chat))
            button.grid(row=index, column=0, sticky="nsew")
            self.chatHistoryColumn.rowconfigure(index, weight=0)
            index += 1

        self.entry = scrolledtext.ScrolledText(self.outerGrid, width=100, height=25, wrap=tk.WORD, font=("Courier", 10))
        self.entry.grid(row=0, column=1, sticky='nw')
        self.events.append((self.customfont,self.entry))
        
        self.buttonFrame = tk.Frame(self.outerGrid, height=1)
        self.buttonFrame.grid(row=1, column=1, sticky="w")
        self.buttonGrid = tk.Frame(self.buttonFrame, relief=tk.RIDGE, height=1)
        self.buttonGrid.grid(row=0, column=0, columnspan=4, padx=10, pady=0)

        self.runButton = tk.Button(self.buttonGrid, bg="snow3", width=17, height=1, text="Run Query", font=("Courier", 10), command=self.on_button_click)
        self.runButton.grid(row=0, column=0, sticky="nsew")
        self.stopButton = tk.Button(self.buttonGrid, bg="snow3", width=17, height=1, text="Stop Query", font=("Courier", 10), command=self.stopLLM)
        self.stopButton.grid(row=0, column=1, sticky="nsew")
        self.codeButton = tk.Button(self.buttonGrid, bg="snow3", width=17, height=1, text="CODE OFF", font=("Courier", 10), command=self.codeOnly)
        self.codeButton.grid(row=0, column=2, sticky="nsew")
        self.copyButton = tk.Button(self.buttonGrid, bg="snow3", width=17, height=1, text="Paste Buffer", font=("Courier", 10), command=self.copyCode)
        self.copyButton.grid(row=0, column=3, sticky="nsew")
        self.countLabel = tk.Label(self.buttonGrid, font=("Courier", 10), height=1, text="context length: 0")
        self.countLabel.grid(row=0, column=4, sticky="nsew")

        self.output_text = scrolledtext.ScrolledText(self.outerGrid, width=40, height=27, wrap=tk.WORD, font=("Courier", 10))
        self.output_text.grid(row=2, column=1, sticky='nw')
        self.events.append( (self.customfont, self.output_text))

        self.rightBufferColumn = tk.Frame(self.outerGrid, width=200, height=500)
        self.rightBufferColumn.grid(row=0, column=2, sticky='ne', rowspan=100)
        
        self.cpuplot = DynamicPlot('CPU % Usage', '0', '100', 600, 0, self.root, self.breakout)
        self.memplot = DynamicPlot('Memory % Usage', '0', '100', 0, 300, self.root, self.breakout)

        tokenThread = threading.Thread(target=self.tokenCounterThread, args = ([self.tokenCallBack]))
        tokenThread.daemon = True  # Ensure the thread exits when the main program exits
        tokenThread.start()

        self.root.bind("<Configure>", lambda event:self.bindResize(event))
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.onclosing(self.breakout))

        resizeThread = threading.Thread(target=self.on_configure )
        resizeThread.daemon = True
        resizeThread.start()

    def on_button_click(self):
        # Reading the text from the input field
        user_input = self.entry.get("1.0",tk.END)
        thread = threading.Thread(target=self.runQuery,args=([user_input, self.responseCallback]))
        thread.start()

    def loadButtonClick(self, chatname):
        chat = self.savehistory.loadChat(chatname)
        if chat is not None and len(chat) > 0:
            self.entry.delete(1.0, tk.END)
            self.output_text.delete(1.0, tk.END)
            for message in chat:
                role = json.loads(message)['role']
                content = json.loads(message)['content']
                if role == 'user':
                    self.chat.loadMessage('user', content)
                    self.entry.insert(tk.END, content) 
                elif role == 'assistant':
                    self.chat.loadMessage('assistant', content)
                    self.output_text.insert(tk.END, content)

    def buttonStatus(self, breakout):
        while not breakout[0]:
            if self.chat.queryInProgress:
                if not self.queryStatus:
                    self.queryStatus = True
                    self.runButton.config(bg="green", text="Query In Progress")
            else:
                if self.queryStatus:
                    self.queryStatus = False
                    self.runButton.config(bg="snow3", text="Run Query")
                    input = self.entry.get("1.0",tk.END)
                    output = self.output_text.get("1.0", tk.END)
                    self.savehistory.addMessage(input, 'user')
                    self.savehistory.addMessage(output, 'assistant')
            time.sleep(0.1)

    def runQuery(self, user_input, callback):
        self.output_text.delete(1.0, tk.END)  # Clear any text
        self.chat.send_chat(user_input.strip(), callback)
        
    def responseCallback(self, responses):
        self.output_text.insert(tk.END, responses) 
        self.output_text.see(index=tk.END)

    def onclosing(self, breakout: list):
        breakout[0] = True
        print("Exiting application...")
        try:
            if self.root is not None:
                self.root.destroy()
            if self.cpuplot is not None:
                self.cpuplot.destroy()
            if self.memplot is not None:
                self.memplot.destroy()
            sys.exit()
        except Exception as e:
            print(f"Error during closing: {e}")

    def resize_textboxes(self, font, control):
        text_width = int( (self.root.winfo_width() - 450) / (helpers.get_font_dims(font)[0] + 2) )
        text_height = int( self.root.winfo_height() / (6 * helpers.get_font_dims(font)[1]) )
        
        control.config(width=text_width, height=text_height)

    def bindResize(self, event):
        self.resize_textboxes(self.customfont, self.entry)
        self.resize_textboxes(self.customfont, self.output_text)

        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        cpuoffsetX = root_w - 250
        cpuoffsetY = 20
        self.cpuplot.updatePosition(cpuoffsetX, cpuoffsetY, root_x, root_y, root_h)
        self.cpuplot.after(10, self.cpuplot.lift)
        memoffsetX = root_w - 250
        memoffsetY = int(root_h / 2)
        self.memplot.updatePosition(memoffsetX, memoffsetY, root_x, root_y, root_h)
        self.memplot.after(10,self.memplot.lift)

    def tokenCounterThread(self, callback):
        oldcount = 0
        while not self.breakout[0]:
            try:
                user_input = self.entry.get("1.0",tk.END)
                count = helpers.get_context_length(user_input)
                count += self.chat.tokenCount()
                if count != oldcount:
                    oldcount = count
                    callback(str(count))
            except Exception as e:
                print(f"error: {e}")
                pass
            time.sleep(.5)

    def tokenCallBack(self, new_text):
        if self.countLabel is not None:
            self.countLabel.config(text="context length: " + new_text + " of "+ model[2])  # Update the label's with the new text

    def codeOnly(self):
        self.onlyCode = not self.onlyCode
        if self.onlyCode:
            self.chat.setQueryHeader(self.onlyCode)
            self.codeButton.config(bg="green", text="CODE ON")
        else:
            self.codeButton.config(bg="snow3", text="CODE OFF")

    def copyCode(self):
        copy(self.output_text.get("1.0",tk.END))
    
    def on_configure(self):
        while True:
            state = self.root.state()
            if state == "iconic":  # Minimized
                self.minimize()
            elif state == "zoomed":  # Maximized
                self.maximize()
            elif state == "normal":  # Restored
                self.maximize()
            time.sleep(.1)

if __name__ == "__main__":
    llm_query_ui = LLMQueryUI()