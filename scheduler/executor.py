import subprocess
import sys
import os
from loguru import logger
from typing import Optional, List

class TaskExecutor:
    @staticmethod
    def run_script(script_path: str, task_name: str, timeout: int = 3600, args: List[str] = None) -> bool:
        """
        Run a python script in a subprocess
        
        Args:
            script_path: Path to the python script
            task_name: Name of the task for logging
            timeout: Timeout in seconds
            args: List of command line arguments
            
        Returns:
            bool: True if execution was successful, False otherwise
        """
        logger.info(f"Starting task: {task_name} (Script: {script_path}, Args: {args})")
        
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            return False

        try:
            # Prepare the command - use the same python interpreter
            cmd = [sys.executable, script_path]
            
            # Append arguments if any
            if args:
                cmd.extend(args)
            
            # Run the subprocess
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy() # Pass current environment variables
            )
            
            # Log output
            if process.stdout:
                logger.info(f"[{task_name}] STDOUT:\n{process.stdout.strip()}")
            
            if process.stderr:
                logger.warning(f"[{task_name}] STDERR:\n{process.stderr.strip()}")
                
            if process.returncode == 0:
                logger.success(f"Task finished successfully: {task_name}")
                return True
            else:
                logger.error(f"Task failed with return code {process.returncode}: {task_name}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Task timed out after {timeout} seconds: {task_name}")
            return False
        except Exception as e:
            logger.error(f"Error executing task {task_name}: {e}")
            return False
