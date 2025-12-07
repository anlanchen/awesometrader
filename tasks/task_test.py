import sys
import time
from datetime import datetime

def main():
    print(f"Test task running at {datetime.now()}")
    print(f"Arguments: {sys.argv}")
    time.sleep(1) # Simulate some work
    print("Test task completed")

if __name__ == "__main__":
    main()

