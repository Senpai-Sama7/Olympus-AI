import os
from typing import Dict, Optional


class PromptStore:
    def __init__(self, prompts_dir: Optional[str] = None):
        self.prompts_dir = prompts_dir or os.path.join(
            os.path.dirname(__file__), "prompts"
        )
        self.prompts: Dict[str, str] = {}
        self.load_prompts()

    def load_prompts(self):
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(self.prompts_dir, filename), "r") as f:
                    self.prompts[filename[:-4]] = f.read()

    def get_prompt(self, name: str, **kwargs) -> str:
        if name not in self.prompts:
            raise ValueError(f"Prompt not found: {name}")
        return self.prompts[name].format(**kwargs)
