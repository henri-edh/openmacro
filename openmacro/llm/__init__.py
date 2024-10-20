from datetime import datetime
from .models.samba import SambaNova

import os
import re

def interpret_input(input_str):
    pattern = r'```(?P<format>\w+)\n(?P<content>[\s\S]+?)```|(?P<text>[^\n]+)'
    
    matches = re.finditer(pattern, input_str)
    
    blocks = []
    current_message = None
    
    for match in matches:
        if match.group("format"):
            if current_message:
                blocks.append(current_message)
                current_message = None
            block = {
                "type": "code",
                "format": match.group("format"),
                "content": match.group("content").strip()
            }
            blocks.append(block)
        else:
            text = match.group("text").strip()
            if current_message:
                current_message["content"] += "\n" + text
            else:
                current_message = {
                    "type": "message",
                    "content": text
                }
    
    if current_message:
        blocks.append(current_message)
    
    return blocks

def to_lmc(content: str, role: str = "assistant", type="message", format: str | None = None) -> dict:            
    lmc = {"role": role, "type": type, "content": content} 
    return lmc | ({} if format is None else {"format": format})
    
def to_chat(lmc: dict, logs=False) -> str:
    #_defaults = {}
    
    _type, _role, _content, _format = (lmc.get("type", "message"), 
                                       lmc.get("role", "assistant"), 
                                       lmc.get("content", "None"), 
                                       lmc.get("format", None))
    
    time = datetime.now().strftime("%I:%M %p %m/%d/%Y")
    
    if logs:
        return f'\033[90m({time})\033[0m <type: {_type if _format is None else f"{_type}, format: {_format}"}> \033[1m{_role}\033[0m: {_content}'
    
    if _role == "system":
        return ("----- SYSTEM PROMPT -----\n" +
                _content + "\n----- END SYSTEM PROMPT -----")
    
    return f'({time}) [type: {_type if _format is None else f"{_type}, format: {_format}"}] *{_role}*: {_content}'

class LLM:
    def __init__(self, verbose=False, messages: list = None, system=""):
        self.system = system

        self.verbose = verbose

        if not (api_key := os.getenv('API_KEY')) :
            raise Exception("API_KEY for LLM not provided. Get yours for free from https://cloud.sambanova.ai/")
        
        self.llm = SambaNova(api_key=api_key,
                             model="Meta-Llama-3.1-405B-Instruct",
                             remember=True,
                             system=self.system,
                             messages=[] if messages is None else messages)
        self.messages = self.llm.messages
            
    def chat(self, *args, **kwargs):
        if self.system and not "system" in kwargs:
            return self.llm.chat(*args, **kwargs, system=self.system, max_tokens=1400)
        return self.llm.chat(*args, **kwargs, max_tokens=1400)
