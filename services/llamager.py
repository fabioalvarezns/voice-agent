import yaml
import time
from dotenv import load_dotenv
from groq import (
    Groq,
    AsyncGroq
)

load_dotenv()


class LLamager:

    def __init__(self, option: str) -> None:
        self.model = 'llama3-70b-8192'
        self.validator_model = 'llama3-70b-8192'
        self.temperature = 0.5,
        self.max_tokens = 1024,
        self.stop = None,
        self.stream = False,
        self.client = Groq()
        self.messages = self.get_system_prompt("system_prompt" if option == 'elevenlabs' else "system_prompt_english")
        self.validator_messages = self.get_system_prompt("validator_prompt" if option == 'elevenlabs' else "validator_prompt_english")

    @staticmethod
    def read_yaml_file():
        file_path = 'config.yaml'
        try:
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
            return data
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            return None
        except yaml.YAMLError as e:
            print(f"Error reading YAML file: {e}")
            return None

    def get_system_prompt(self, role: str):
        prompt = self.read_yaml_file()[role]
        return [{"role": "system", "content": prompt}]

    def conversation_handler(self, text: str, role: str, validator: bool):
        messages = {"role": role, "content": text}

        match role, validator:
            case "user", False:
                self.messages.append(messages)
                if len(self.validator_messages) > 6:
                    self.messages.pop(1)
                    self.messages.pop(2)
            case "user", True:
                self.validator_messages.append(messages)
                if len(self.validator_messages) > 2:
                    self.validator_messages.pop(1)
            case "assistant", False:
                self.messages.append(messages)
            case "assistant", True:
                self.validator_messages.append(messages)
            case _:
                raise ValueError("Invalid role")

    def process(self, text: str, role: str, validator: bool):
        self.conversation_handler(text, role, validator)

        start_time = time.time()
        completion = self.client.chat.completions.create(
            messages=self.validator_messages if validator else self.messages,
            model=self.validator_model if validator else self.model,
            temperature=0.5,
            max_tokens=1024,
            top_p=1,
            stop=None,
            stream=False,
        )

        chat_completion = completion.choices[0].message.content
        end_time = time.time()
        elapsed_time = int((end_time - start_time) * 1000)
        print(f"LLM ({elapsed_time}ms): Validator: {validator}: {chat_completion}")
        self.conversation_handler(chat_completion, 'assistant', validator)

        return chat_completion


class AsyncLLamager(LLamager):
    def __init__(self, option: str) -> None:
        super().__init__(option= option)
        self.client = AsyncGroq()

    async def conversation_handler(self, text: str, role: str, validator: bool):
        return super().conversation_handler(text, role, validator)

    async def process(self, text: str, role: str, validator: bool):
        await self.conversation_handler(text, role, validator)

        completion = await self.client.chat.completions.create(
            messages=self.validator_messages if validator else self.messages,
            model=self.validator_model if validator else self.model,
            temperature=0.5,
            max_tokens=1024,
            top_p=1,
            stop=None,
            stream=True,
        )

        return completion
