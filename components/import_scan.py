import os
import importlib
import inspect

from TerminatorBaseCore.components.dynamic_call import HandleRegister

# 已加载的模块集合，避免重复加载
loaded_modules = set()


class ImportScan:
    discovered_classes = []
    loaded_modules = set()
    target_dir = "components"

    def scan_modules(self, app_path, app_name):
        """
        扫描指定 app 下的 components 目录，查找继承了 A 的子类。
        """
        target_dir = os.path.join(app_path, 'components')  # 指定只扫描的一级目录

        if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
            return

        for root, dirs, files in os.walk(target_dir):
            # 排除无关目录（如 __pycache__ 等）
            dirs[:] = [d for d in dirs if d != '__pycache__']

            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    module_path = os.path.relpath(os.path.join(root, file), app_path)
                    module_name = f"{app_name}.{module_path.replace(os.sep, '.')[:-3]}"  # 去掉扩展名

                    if module_name not in self.loaded_modules:
                        self._load_module(module_name)

    def _load_module(self, module_name):
        """
        动态加载模块，并记录已加载模块。
        """
        try:
            module = importlib.import_module(module_name)
            self.loaded_modules.add(module_name)  # 记录已加载模块
            self._discover_classes(module)
        except Exception as e:
            # 捕获加载错误，避免程序中断
            print(f"Failed to import {module_name}: {e}")

    def _discover_classes(self, module):
        """
        查找模块中所有继承了 A 的子类。
        """
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, HandleRegister) and obj is not HandleRegister:  # 过滤掉 A 自身
                self.discovered_classes.append(obj)
