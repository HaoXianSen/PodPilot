import os
import subprocess
import sys


def get_shell_path():
    """获取用户shell中的PATH"""
    try:
        # 获取用户shell的PATH
        shell_path = subprocess.check_output('echo $PATH', shell=True, text=True).strip()
        return shell_path
    except:
        return ""


# 应用启动时添加环境变量
def setup_environment():
    # 添加可能的pod安装路径
    paths = [
        "/usr/local/bin",
        "/usr/bin",
        os.path.expanduser("~/.rvm/gems/ruby-3.0.0/bin"),
        os.path.expanduser("~/.rbenv/shims"),
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin"
    ]

    # 获取shell的PATH并添加
    shell_path = get_shell_path()
    if shell_path:
        paths.append(shell_path)

    # 设置PATH环境变量
    current_path = os.environ.get('PATH', '')
    os.environ['PATH'] = ':'.join(paths) + ':' + current_path


# 执行环境设置
setup_environment()