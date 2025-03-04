import json
import os.path
import time
from typing import Any, Dict, List, Optional

import nonebot_plugin_localstore as store
import pandas as pd
from nonebot.log import logger

from .config import PLUGIN_CONFIG
from .utils import create_dir, find_files, load_jsonl

CHATGPT_LOG_PATH: str = store.get_plugin_cache_dir().as_posix()
logger.info(f"ChatGPT cache will saved to \"{CHATGPT_LOG_PATH}\"")


def save_api_call_stat_to_jsonl(user_id: str, stat: Dict[str, Any]):
    """添加 API 调用统计信息到 JSONL 文件"""
    save_dir = os.path.join(CHATGPT_LOG_PATH, "api_call_stats", user_id)
    save_file = os.path.join(save_dir, f"{time.strftime('%Y-%m-%d')}.jsonl")

    create_dir(save_dir)

    with open(save_file, "a", encoding="utf8") as f:
        f.write(json.dumps(stat, ensure_ascii=False) + "\n")
    logger.debug(f"Save API call stat to {save_file}: {stat}")


def save_system_prompt_to_csv(user_id: str, system_prompt: str):
    """添加系统提示词到 CSV 文件"""
    now_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    save_dir = os.path.join(CHATGPT_LOG_PATH, "system_prompts")
    save_file = os.path.join(save_dir, f"{user_id}.csv")

    create_dir(save_dir)

    # create headers
    if not os.path.exists(save_file):
        with open(save_file, "w", encoding="utf8") as f:
            f.write("Time,System Prompt\n")

    # log prompt
    df = pd.DataFrame(
        [[now_timestamp, system_prompt]],
        columns=["Time", "System Prompt"]
    )
    df.to_csv(save_file, mode='a', header=False, index=False, encoding="utf8")
    logger.debug(f"Save system prompt to {save_file}: \"{system_prompt}\"")


def get_latest_system_prompt(user_id: str) -> str:
    """获取最新的系统提示词"""
    save_file = os.path.join(CHATGPT_LOG_PATH, "system_prompts", f"{user_id}.csv")

    if not os.path.exists(save_file):  # initialize the system prompt file
        system_prompt = ""
        if PLUGIN_CONFIG.chatgpt_log_system_prompt:
            save_system_prompt_to_csv(user_id, system_prompt)
    else:
        df = pd.read_csv(save_file)
        system_prompt = "" if df.empty else df.iloc[-1]["System Prompt"]
        if pd.isna(system_prompt):  # empty value from csv
            system_prompt = ""
        logger.debug(f"Get latest system prompt from {save_file}: \"{system_prompt}\"")

    return system_prompt


def save_chat_history_to_jsonl(user_id: str, chat_history: List[Dict[str, str]], create_new_file=False):
    """添加聊天历史记录到 JSONL 文件"""
    now_date = time.strftime('%Y-%m-%d')
    now_time = time.strftime('%Y%m%d-%H%M%S')  # don't use ":" in case running on Windows
    save_dir = os.path.join(CHATGPT_LOG_PATH, "chat_histories", user_id, f"{now_date}")

    # get the target file to save
    if create_new_file:
        save_file = os.path.join(save_dir, f"{now_time}.jsonl")
    else:
        all_files = sorted(find_files(save_dir, "*.jsonl"))
        if len(all_files) == 0:  # no existing chat history file, create a new one
            save_file = os.path.join(save_dir, f"{now_time}.jsonl")
        else:  # append to the latest file
            save_file = os.path.join(save_dir, all_files[-1])

    create_dir(save_dir)

    with open(save_file, "a", encoding="utf8") as f:
        for chat in chat_history:
            f.write(json.dumps(chat, ensure_ascii=False) + "\n")
            logger.debug(f"Save chat history to {save_file}: \"{chat}\"")


def get_latest_chat_history(user_id: str) -> Optional[List[Dict[str, str]]]:
    """获取最新的聊天历史记录"""
    save_dir = os.path.join(CHATGPT_LOG_PATH, "chat_histories", user_id)  # here
    all_files = sorted(find_files(save_dir, "*.jsonl"))
    if len(all_files) == 0:
        logger.debug(f"Get no chat history from {save_dir}")
        return None
    else:
        logger.debug(f"Get latest chat history from {all_files[-1]}")
        return load_jsonl(all_files[-1])
