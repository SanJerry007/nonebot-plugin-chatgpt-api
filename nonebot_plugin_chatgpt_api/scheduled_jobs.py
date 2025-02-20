from typing import Dict, Set

from nonebot.log import logger
from nonebot_plugin_apscheduler import scheduler

ALL_TIMEOUT_JOB_IDS: Dict[str, Set[str]] = {}


def add_to_timeout_job_storage(user_id: str, job_id: str):
    """添加一个超时任务"""
    if user_id not in ALL_TIMEOUT_JOB_IDS:
        ALL_TIMEOUT_JOB_IDS[user_id] = set()
    ALL_TIMEOUT_JOB_IDS[user_id].add(job_id)
    logger.info(f"Schedule timeout job for \"{user_id}\"")


def remove_from_timeout_job_storage(user_id: str, job_id: str):
    """移除一个超时任务"""
    if user_id in ALL_TIMEOUT_JOB_IDS:
        if job_id in ALL_TIMEOUT_JOB_IDS[user_id]:
            scheduler.remove_job(job_id)
            logger.info(f"Removed timeout job: {job_id}")
            ALL_TIMEOUT_JOB_IDS[user_id].remove(job_id)


def remove_all_timeout_jobs_from_storage(user_id: str):
    """移除一个用户的所有超时任务"""
    if user_id in ALL_TIMEOUT_JOB_IDS:
        for job_id in ALL_TIMEOUT_JOB_IDS[user_id]:
            scheduler.remove_job(job_id)
            logger.info(f"Removed timeout job: {job_id}")
        ALL_TIMEOUT_JOB_IDS.remove(user_id)
