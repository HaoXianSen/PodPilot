import os
import shutil
from PyQt5.QtCore import QProcess, QProcessEnvironment


class PodCacheService:
    """Pod缓存清理服务"""

    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.process = None

    def clean_cache(
        self,
        project_path: str,
        clean_pods: bool = True,
        clean_lock: bool = True,
        clean_cache: bool = True,
    ) -> bool:
        """清理Pod缓存"""
        if not clean_pods and not clean_lock and not clean_cache:
            return False

        if self.log_callback:
            self.log_callback("开始清理Pod缓存...")

        try:
            if clean_pods:
                pods_dir = os.path.join(project_path, "Pods")
                if os.path.exists(pods_dir):
                    if self.log_callback:
                        self.log_callback(f"删除Pods目录: {pods_dir}")
                    shutil.rmtree(pods_dir)
                    if self.log_callback:
                        self.log_message("Pods目录已删除")
                else:
                    if self.log_callback:
                        self.log_message("Pods目录不存在，跳过")

            if clean_lock:
                lock_file = os.path.join(project_path, "Podfile.lock")
                if os.path.exists(lock_file):
                    if self.log_callback:
                        self.log_callback(f"删除Podfile.lock: {lock_file}")
                    os.remove(lock_file)
                    if self.log_callback:
                        self.log_message("Podfile.lock已删除")
                else:
                    if self.log_callback:
                        self.log_message("Podfile.lock不存在，跳过")

            if clean_cache:
                if self.log_callback:
                    self.log_callback("清理CocoaPods缓存...")
                self._clean_cocoapods_cache()

            return True

        except Exception as e:
            if self.log_callback:
                self.log_callback(f"清理失败: {str(e)}")
            return False

    def _clean_cocoapods_cache(self):
        """清理CocoaPods缓存"""
        self.process = QProcess()
        self.process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())

        shell_cmd = """
source ~/.rvm/scripts/rvm 2>/dev/null || source ~/.rvm/bin/rvm 2>/dev/null || true
pod cache clean --all
"""

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

    def set_finished_callback(self, callback):
        """设置完成回调"""
        if self.process:
            self.process.finished.connect(callback)

    def stop(self):
        """停止清理"""
        if self.process:
            self.process.kill()

    def delete_process(self):
        """删除进程对象"""
        if self.process:
            self.process.deleteLater()
            self.process = None
