import yaml
import pytz
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from loguru import logger

@dataclass
class TaskConfig:
    name: str
    script: str
    trigger: str
    trigger_args: Dict[str, Any]
    timezone: Optional[pytz.BaseTzInfo] = None
    enabled: bool = True
    timeout: int = 3600
    script_args: List[str] = field(default_factory=list)

class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = {}

    def load(self) -> Dict[str, Any]:
        """Load and parse the configuration file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            return self.config
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}

    def get_tasks(self) -> List[TaskConfig]:
        """Parse tasks from the loaded configuration"""
        if not self.config:
            self.load()

        tasks_data = self.config.get('tasks', [])
        task_configs = []

        for task in tasks_data:
            if not task.get('enabled', True):
                continue

            try:
                # Handle timezone
                tz = None
                if 'timezone' in task:
                    try:
                        tz = pytz.timezone(task['timezone'])
                    except pytz.UnknownTimeZoneError:
                        logger.error(f"Unknown timezone for task {task.get('name')}: {task['timezone']}")
                        continue

                # Prepare trigger arguments
                trigger_type = task.get('trigger', 'cron')
                trigger_args = {}
                
                # Copy extra trigger args like misfire_grace_time
                if 'trigger_args' in task:
                    trigger_args.update(task['trigger_args'])

                if trigger_type == 'cron':
                    for field in ['year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second']:
                        if field in task:
                            trigger_args[field] = task[field]
                elif trigger_type == 'interval':
                    for field in ['weeks', 'days', 'hours', 'minutes', 'seconds']:
                        if field in task:
                            trigger_args[field] = task[field]
                
                # Parse script arguments
                script_args = task.get('args', [])
                if isinstance(script_args, str):
                    script_args = script_args.split()
                
                # Create TaskConfig object
                task_config = TaskConfig(
                    name=task['name'],
                    script=task['script'],
                    trigger=trigger_type,
                    trigger_args=trigger_args,
                    timezone=tz,
                    enabled=task.get('enabled', True),
                    timeout=task.get('timeout', 3600),
                    script_args=script_args
                )
                task_configs.append(task_config)

            except Exception as e:
                logger.error(f"Error parsing task {task.get('name')}: {e}")
                continue

        return task_configs

    def get_global_settings(self) -> Dict[str, Any]:
        if not self.config:
            self.load()
        return self.config.get('global', {})
