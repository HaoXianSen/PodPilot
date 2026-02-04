import os
from PyQt5.QtCore import QProcess, QProcessEnvironment


class PodInstallService:
    """Pod Install服务"""

    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.process = None

    def run_pod_install(self, project_path: str) -> bool:
        """运行pod install"""
        if not os.path.exists(project_path):
            if self.log_callback:
                self.log_callback(f"项目路径不存在: {project_path}")
            return False

        podfile_path = os.path.join(project_path, "Podfile")
        if not os.path.exists(podfile_path):
            if self.log_callback:
                self.log_callback("未找到Podfile")
            return False

        if self.log_callback:
            self.log_callback(f"项目路径: {project_path}")
            self.log_callback("正在运行 pod install...")

        self.process = QProcess()
        self.process.setWorkingDirectory(project_path)
        self.process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())

        shell_cmd = f'''
source ~/.rvm/scripts/rvm 2>/dev/null || source ~/.rvm/bin/rvm 2>/dev/null || true
cd "{project_path}" && pod install
'''

        if self.log_callback:
            self.process.readyReadStandardOutput.connect(
                lambda: self.log_callback(
                    self.process.readAllStandardOutput().data().decode()
                )
            )
            self.process.readyReadStandardError.connect(
                lambda: self.log_callback(
                    self.process.readAllStandardError().data().decode()
                )
            )

        user_shell = os.environ.get("SHELL", "/bin/zsh")
        if not os.path.exists(user_shell):
            user_shell = "/bin/zsh"

        self.process.start(user_shell, ["-l", "-c", shell_cmd])
        return True

    def set_finished_callback(self, callback):
        """设置完成回调"""
        if self.process:
            self.process.finished.connect(callback)

    def stop(self):
        """停止pod install"""
        if self.process:
            self.process.kill()

    def delete_process(self):
        """删除进程对象"""
        if self.process:
            self.process.deleteLater()
            self.process = None
