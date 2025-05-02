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

Story="""
# 角色
你是一位提示词优化师，旨在帮用户生成优质提示词，使其更完整、更具电影感和表现力。参考{query}的格式和书写方式，随机生成一个分镜脚本，要求如下：
1、需要5个分镜镜头，需要符合故事线
2、对分镜脚本的描述都是目前发生的故事，描述这一定格的时刻，不要考虑后续的发展
3、分镜脚本之间需要有关联
4、分镜脚本内容需要非常贴合场景故事线
5、分镜尽量描述场景的构图方式、视角、分镜场景中的动态与静态元素、人物的动态与位置关系。
6、输出的提示词，要用适合FLUX大模型的自然语言进行描述
7、字数必须精简，使用中文输出

# 严格限制的输出格式：
[MOVIE-SHOTS] 场景---[SCENE-1] 分镜描述---[SCENE-2] 分镜描述---[SCENE-3] 分镜描述---[SCENE-4] 分镜描述---[SCENE-5] 分镜描述

#严格要求
禁止输出要求外的任何东西，提示词不允许分段，一段输出
"""

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

# 自定义节点类
class MachineCodeValidationNode:
    @staticmethod
    def INPUT_TYPES():
        return {
            "required": {},
            "optional": {}
        }

    RETURN_TYPES = ("STRING", "FLOAT", "FLOAT", "INT", "INT", "INT", "STRING", "INT", "INT", "FLOAT", "FLOAT")
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
                f"机器码校验成功",        # STRING
                50,                     # FLOAT
                3.5,                    # FLOAT
                255,                    # 红
                0,                      # 绿        
                0,                      # 蓝
                Story,
                20,
                40,
                7.5,
                1
            )
        else:
            # 如果机器码校验失败，显示链接并中断工作流
            raise ValueError(f"机器码校验失败，请确保您已购买该工作流的服务，并联系客服激活！\r\n 您的机器码为：{machine_code}\r\n详情访问：https://mp.weixin.qq.com/s/m1evNxJWKvYSQRhqAa0Bxg")

# 注册节点
NODE_CLASS_MAPPINGS = {
    "MachineCodeValidation": MachineCodeValidationNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MachineCodeValidation": "@小江的独家参数"
}
