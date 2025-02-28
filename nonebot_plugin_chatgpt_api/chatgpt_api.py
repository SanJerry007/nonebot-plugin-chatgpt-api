import time
from typing import Any, Dict, List, Optional

import httpx
from nonebot.log import logger
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from .chatgpt_stats import calculate_price, get_number_of_tokens
from .config import PLUGIN_CONFIG
from .data_storage import get_latest_system_prompt

ALL_CHATGPTS = {}


class ChatGPT:
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        http_proxy_url: Optional[str] = None,
        max_retries: int = 3,
        model: str = "gpt-4o",
        system_prompt: str = "",
        chat_history: Optional[list] = None,
        **gen_args,
    ) -> None:
        logger.debug("Creating ChatGPT instance...")
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=httpx.Client(proxy=http_proxy_url) if http_proxy_url else None,
            max_retries=max_retries,
        )
        self.model = model
        self.system_prompt = system_prompt if isinstance(system_prompt, str) else ""
        self.chat_history = chat_history if isinstance(chat_history, list) else []
        self.gen_args = gen_args
        logger.debug("Created successfully!")

    def set_chat_history(self, chat_history):
        self.chat_history = chat_history

    def reset_chat_history(self):
        self.set_chat_history([])

    def update_chat_history(self, user_content, response_content):
        if response_content is not None:
            self.chat_history.append({"role": "user", "content": user_content})
            self.chat_history.append({"role": "assistant", "content": response_content})

    def set_system_prompt(self, system_prompt: str = "", reset_history: bool = True):
        self.system_prompt = system_prompt
        if reset_history:
            self.reset_chat_history()

    def format_input_messages(self, content, input_type: str = "text") -> List[Dict[str, Any]]:
        input_messages = []

        if len(self.system_prompt) > 0:
            input_messages.append({"role": "system", "content": self.system_prompt})

        input_messages.extend(self.chat_history)

        if input_type == "text":
            input_messages.append({"role": "user", "content": content})
        elif input_type == "image":
            raise NotImplementedError("Image input is not supported yet.")
        else:
            raise ValueError(f"Invalid input type: {input_type}")

        return input_messages

    async def get_chat_response(self, messages) -> Optional[ChatCompletion]:
        try:
            logger.info(f"Sending request:\n{messages}")
            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **self.gen_args,
            )
            logger.debug(f"[Content] Request raw response:\n{response}")
            return response

        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            return None

    async def multi_round_chat(self, content: str, input_type: str = "text") -> Dict[str, Any]:
        input_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        messages = self.format_input_messages(content, input_type=input_type)
        response = await self.get_chat_response(messages)
        output_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        if response is not None:
            cached_tokens, prompt_tokens, completion_tokens = get_number_of_tokens(response.usage)
            cache_cost, prompt_cost, completion_cost = calculate_price(self.model, response.usage)
            response_content = response.choices[0].message.content
            if response_content is None:
                logger.debug(f"Request response content is None")
        else:
            cached_tokens, prompt_tokens, completion_tokens = 0, 0, 0
            cache_cost, prompt_cost, completion_cost = 0, 0, 0
            response_content = None
            logger.debug(f"Request response is None")

        stat = {
            "cached_tokens": cached_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cache_cost": cache_cost,
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "prompt": self.system_prompt,
            "input": content,
            "input_time": input_time,
            "output": response_content,
            "output_time": output_time,
            "history": self.chat_history,
        }
        logger.debug(f"Statistics: {stat}")

        self.update_chat_history(content, response_content)

        return stat


def get_chatgpt(user_id: str) -> ChatGPT:
    if user_id not in ALL_CHATGPTS:
        chatgpt = ChatGPT(
            api_key=PLUGIN_CONFIG.chatgpt_api_key,
            base_url=PLUGIN_CONFIG.chatgpt_base_url,
            model=PLUGIN_CONFIG.chatgpt_model,
            system_prompt=get_latest_system_prompt(user_id),
            chat_history=None,
            **PLUGIN_CONFIG.chatgpt_gen_args,
        )
        ALL_CHATGPTS[user_id] = chatgpt
        logger.debug(f"[ChatGPT] Created for user \"{user_id}\": "
                     f"api_key={PLUGIN_CONFIG.chatgpt_api_key}, "
                     f"base_url={PLUGIN_CONFIG.chatgpt_base_url}, "
                     f"model={PLUGIN_CONFIG.chatgpt_model}, "
                     f"system_prompt={chatgpt.system_prompt}, "
                     f"chat_history={chatgpt.chat_history}")
    else:
        chatgpt = ALL_CHATGPTS[user_id]
        logger.debug(f"[ChatGPT] Called by user \"{user_id}\"")
    return chatgpt
