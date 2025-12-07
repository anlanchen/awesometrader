#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from loguru import logger
from dotenv import load_dotenv
from scheduler.manager import SchedulerManager

def main():
    # Load environment variables
    load_dotenv()

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Configure logging
    logger.remove() # Remove default handler
    logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
    logger.add("logs/scheduler_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days", 
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    logger.info("Starting AwesomeTrader Task Scheduler...")
    
    try:
        manager = SchedulerManager()
        manager.start()
    except Exception as e:
        logger.critical(f"Scheduler crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

