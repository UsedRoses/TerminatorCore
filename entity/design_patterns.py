class Singleton:
    """
    单例模式
    """
    _instances = {}

    def __new__(cls, *args, **kwargs):
        # 检查是否已经存在实例
        if cls not in cls._instances:
            print("singleton:" + cls.__name__)
            # 创建实例并存储
            instance = super().__new__(cls)
            cls._instances[cls] = instance
        return cls._instances[cls]
