import platform
import subprocess
import hashlib
import uuid
import tkinter as tk
from PIL import Image, ImageTk
import requests
import json
import qrcode
import sys

# 获取硬件信息
def get_hardware_info():
    """获取硬件信息"""
    system = platform.system()
    if system == "Windows":
        # 获取主板序列号（适用于 Windows）
        try:
            result = subprocess.run(
                'wmic baseboard get serialnumber',
                shell=True,
                capture_output=True,
                text=True
            )
            serial_number = result.stdout.strip().split("\n")[-1].strip()
            return serial_number if serial_number else None
        except Exception as e:
            print(f"获取主板序列号失败: {e}")
            return None
    elif system in ["Linux", "Darwin"]:
        # 获取 MAC 地址（适用于 Linux 和 macOS）
        mac_addr = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                            for elements in range(0, 2 * 6, 8)][::-1])
        return mac_addr
    else:
        print("不支持的操作系统")
        return None

# 生成机器码
def generate_machine_code(hardware_info):
    """根据硬件信息生成机器码"""
    if not hardware_info:
        print("无法获取硬件信息，无法生成机器码。")
        return None
    
    # 使用 SHA-256 哈希算法生成机器码
    machine_code = hashlib.sha256(hardware_info.encode()).hexdigest()
    return machine_code

# 下载并解析 JSON 数据
def fetch_machine_codes_from_url(urls):
    """从指定 URL 列表中依次下载并解析机器码列表"""
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # 解析 JSON 数据为列表
                try:
                    machine_codes = json.loads(response.text)
                    if isinstance(machine_codes, list):
                        return [code.strip() for code in machine_codes if isinstance(code, str) and code.strip()]
                    else:
                        print(f"JSON 数据格式错误，不是数组类型（URL: {url}）。")
                except json.JSONDecodeError as e:
                    print(f"解析 JSON 数据失败: {e} (URL: {url})")
            else:
                print(f"无法下载 JSON 数据，状态码: {response.status_code} (URL: {url})")
        except Exception as e:
            print(f"下载 JSON 数据失败: {e} (URL: {url})")
    return []

# 对比机器码
def compare_machine_code(machine_code, machine_codes):
    """对比生成的机器码是否存在于列表中"""
    return machine_code in machine_codes

# 显示二维码弹窗
def show_qr_code_popup(machine_code, qr_data):
    """显示当前机器码和二维码图片"""
    root = tk.Tk()
    root.title("机器码校验失败")
    root.geometry("512x512")

    # 显示消息
    label_message = tk.Label(root, text="机器码校验失败，请确保您已购买该工作流的服务，并联系客服激活！", font=("Arial", 14))
    label_message.pack(pady=10)

    # 显示当前机器码（允许复制）
    text_widget = tk.Text(root, height=2, width=50, font=("Arial", 12))
    text_widget.insert(tk.END, f"当前机器码: {machine_code}")
    text_widget.config(state=tk.NORMAL)  # 允许编辑（以便复制）
    text_widget.pack(pady=10)

    # 如果有二维码数据，则生成并显示二维码
    if qr_data:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # 将二维码转换为 Tkinter 图片
        img_tk = ImageTk.PhotoImage(img)
        label_qr = tk.Label(root, image=img_tk)
        label_qr.image = img_tk  # 防止垃圾回收
        label_qr.pack(pady=10)

    # 关闭按钮
    close_button = tk.Button(root, text="关闭", command=root.destroy)
    close_button.pack(pady=10)

    root.mainloop()

# 自定义节点类
class MachineCodeValidationNode:
    @staticmethod
    def INPUT_TYPES():
        return {
            "required": {},
            "optional": {}
        }

    RETURN_TYPES = ("STRING", "FLOAT", "FLOAT", "INT", "INT", "INT")
    FUNCTION = "validate"
    CATEGORY = "Machine_Verify"

    def validate(self):
        # 获取硬件信息并生成机器码
        hardware_info = get_hardware_info()
        if not hardware_info:
            raise ValueError("无法获取硬件信息，生成机器码失败。")

        machine_code = generate_machine_code(hardware_info)
        if not machine_code:
            raise ValueError("无法生成机器码。")

        # 定义多个 JSON 文件链接
        json_urls = [
            "https://ghproxy.net/https://raw.githubusercontent.com/IAMJOYBO/machine_code/main/machine_code.json",
            "https://ghfast.top/https://raw.githubusercontent.com/IAMJOYBO/machine_code/main/machine_code.json",
            "https://github.3x25.com/https://raw.githubusercontent.com/IAMJOYBO/machine_code/main/machine_code.json",
            "https://github.com/IAMJOYBO/machine_code/raw/refs/heads/main/machine_code.json",
            "https://raw.gitcode.com/xiaobeing/machine_code/raw/main/machine_code.json"
        ]

        # 下载并解析 JSON 数据
        machine_codes = fetch_machine_codes_from_url(json_urls)
        if not machine_codes:
            raise ValueError("网络连接失败，无法校验机器码，请检查网络连接。")

        # 对比机器码
        is_valid = compare_machine_code(machine_code, machine_codes)

        if is_valid:
            # 如果机器码校验成功，返回 5 个输出参数
            return (
                "机器码校验成功",        # STRING
                50,                     # FLOAT
                3.5,                    # FLOAT
                255,                    # 红
                0,                      # 绿        
                0                       # 蓝
            )
        else:
            # 如果机器码校验失败，显示二维码并中断工作流
            qr_data = "https://mp.weixin.qq.com/s/m1evNxJWKvYSQRhqAa0Bxg"  # 替换为实际的好友二维码链接
            show_qr_code_popup(machine_code, qr_data)
            raise ValueError(f"机器码校验失败，请确保您已购买该工作流的服务，并联系客服激活！\r\n 您的机器码为：{machine_code}")

# 注册节点
NODE_CLASS_MAPPINGS = {
    "MachineCodeValidation": MachineCodeValidationNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MachineCodeValidation": "@小江的独家参数"
}
