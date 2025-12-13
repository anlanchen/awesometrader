import time
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
from apscheduler.jobstores.memory import MemoryJobStore
from loguru import logger
from typing import Optional
import pytz

from scheduler.config_loader import ConfigLoader
from scheduler.executor import TaskExecutor

class SchedulerManager:
    def __init__(self, config_path: str = "config/tasks.yaml"):
        self.config_path = config_path
        self.config_loader = ConfigLoader(config_path)
        self.scheduler: Optional[BackgroundScheduler] = None
        self._last_config_mtime: float = 0
        self._setup_scheduler()

    def _setup_scheduler(self):
        """Initialize and configure the scheduler"""
        global_settings = self.config_loader.get_global_settings()
        
        # Configure defaults
        max_workers = global_settings.get('max_workers', 5)
        timezone_str = global_settings.get('timezone', 'Asia/Shanghai')
        
        try:
            timezone = pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
            logger.warning(f"Unknown global timezone '{timezone_str}', using Asia/Shanghai")
            timezone = pytz.timezone('Asia/Shanghai')

        executors = {
            'default': ThreadPoolExecutor(max_workers)
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            executors=executors,
            job_defaults=job_defaults,
            timezone=timezone
        )
        
        # Add event listener
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    def _job_listener(self, event):
        """Handle scheduler events"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed with exception: {event.exception}")
        elif event.code == EVENT_JOB_MISSED:
            logger.warning(f"Job {event.job_id} missed execution time")
        else:
            logger.info(f"Job {event.job_id} executed successfully")

    def load_tasks(self):
        """Load tasks from config and add them to scheduler"""
        if not self.scheduler:
            self._setup_scheduler()
            
        # Clear existing jobs to support reload
        self.scheduler.remove_all_jobs()
        
        tasks = self.config_loader.get_tasks()
        
        for task in tasks:
            logger.info(f"Adding task: {task.name} (Trigger: {task.trigger}, Args: {task.trigger_args}, TZ: {task.timezone})")
            
            try:
                self.scheduler.add_job(
                    func=TaskExecutor.run_script,
                    trigger=task.trigger,
                    args=[task.script, task.name, task.timeout, task.script_args],
                    id=task.name,
                    name=task.name,
                    timezone=task.timezone, # APScheduler handles timezone here
                    replace_existing=True,
                    **task.trigger_args
                )
            except Exception as e:
                logger.error(f"Failed to add task {task.name}: {e}")

        logger.info(f"Loaded {len(tasks)} tasks")

    def _get_config_mtime(self) -> float:
        """获取配置文件的修改时间"""
        try:
            return os.path.getmtime(self.config_path)
        except OSError:
            return 0
    
    def _check_and_reload(self):
        """检查配置文件是否变化，如有变化则重新加载"""
        current_mtime = self._get_config_mtime()
        if current_mtime > self._last_config_mtime:
            if self._last_config_mtime > 0:  # 不是首次加载
                logger.info("Config file changed, reloading tasks...")
                self.config_loader.load()
                self.load_tasks()
            self._last_config_mtime = current_mtime

    def start(self):
        """Start the scheduler"""
        if not self.scheduler:
            self._setup_scheduler()
        
        # 记录初始配置文件修改时间
        self._last_config_mtime = self._get_config_mtime()
        
        self.load_tasks()
        self.scheduler.start()
        logger.info("Scheduler started (config hot-reload enabled)")
        
        try:
            # Keep main thread alive and check config changes
            while True:
                time.sleep(1)
                self._check_and_reload()
        except (KeyboardInterrupt, SystemExit):
            self.stop()

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

