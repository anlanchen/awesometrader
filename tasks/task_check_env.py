import os
import sys

def main():
    print(f"Checking environment variables...")
    # 打印一些关键环境变量的存在性（不打印值，以防泄露）
    keys_to_check = ['DINGDING_WEBHOOK', 'DINGDING_SECRET', 'LONGPORT_APP_KEY']
    
    for key in keys_to_check:
        value = os.getenv(key)
        status = "✅ Found" if value else "❌ Not Found"
        print(f"{key}: {status}")

if __name__ == "__main__":
    main()

