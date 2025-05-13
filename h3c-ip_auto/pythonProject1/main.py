import csv
import os
import subprocess

# 基础配置
CREDENTIALS = "admin:password"  # 带外管理凭证
OOB_TOOL = "ipmitool"  # 带外管理工具
LOG_FILE = "ip_config.log"
STATE_FILE = "progress.state"
CSV_FILE = "ip1.csv"  # \


def load_ip_list():
    """加载ip1.csv文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, CSV_FILE)

    # 文件存在性检查
    if not os.path.exists(csv_path):
        print(f"错误：文件 {csv_path} 不存在")
        print("请确认：")
        print(f"1. 文件 {CSV_FILE} 是否在目录 {current_dir} 中")
        print(f"2. 文件名是否拼写正确")
        exit(1)

    # 读取CSV内容
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        return [row for row in csv.DictReader(f)]


def save_progress(index):
    """保存进度"""
    with open(STATE_FILE, 'w') as f:
        f.write(str(index))


def load_progress():
    """读取进度"""
    try:
        with open(STATE_FILE) as f:
            return int(f.read().strip())
    except:
        return 0


def set_ip(address_info):
    """执行IP配置"""
    cmd = [
        OOB_TOOL,
        '-H', address_info['current_ip'],
        '-U', CREDENTIALS.split(':')[0],
        '-P', CREDENTIALS.split(':')[1],
        'lan', 'set', 'ipsrc', 'static',
        address_info['ip'], address_info['netmask'], address_info['gateway']
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=10)
        return True
    except subprocess.CalledProcessError as e:
        with open(LOG_FILE, 'a') as f:
            f.write(f"Failed,{address_info['位置标签']},{address_info['ip']},{e.stderr}\n")
        return False
    except Exception as e:
        with open(LOG_FILE, 'a') as f:
            f.write(f"Error,{address_info['位置标签']},{address_info['ip']},{str(e)}\n")
        return False


def interactive_cli():
    """命令行交互界面"""
    ip_list = load_ip_list()
    current_index = load_progress()

    print(f"已加载 {len(ip_list)} 台服务器配置")

    while current_index < len(ip_list):
        current = ip_list[current_index]

        print(f"\n[{current_index + 1}/{len(ip_list)}] 服务器 {current['位置标签']}")
        print(f"默认IP: {current['current_ip']} -> 新IP: {current['ip']}/{current['netmask']}")

        action = input("执行配置？ (y)es/(n)ext/(b)ack/(j)ump/(q)uit: ").lower()

        if action == 'y':
            print("正在配置...")
            if set_ip(current):
                print("✅ 配置成功")
                current_index += 1
                save_progress(current_index)
            else:
                print("❌ 配置失败，请检查日志")
                retry = input("重试？ (y/n): ").lower()
                if retry != 'y':
                    current_index += 1

        elif action == 'n':
            current_index += 1
            save_progress(current_index)

        elif action == 'b' and current_index > 0:
            current_index -= 1
            save_progress(current_index)

        elif action.startswith('j'):
            try:
                new_index = int(input("请输入目标序号 (1-100): ")) - 1
                if 0 <= new_index < len(ip_list):
                    current_index = new_index
                    save_progress(current_index)
                else:
                    print("无效的序号范围")
            except ValueError:
                print("输入无效")

        elif action == 'q':
            save_progress(current_index)
            print("退出程序")
            break

        else:
            print("无效操作，可用命令: y/n/b/j/q")


if __name__ == "__main__":
    # 初始化日志文件
    with open(LOG_FILE, 'a') as f:
        f.write("\n\n=== 新的配置会话开始 ===\n")

    interactive_cli()