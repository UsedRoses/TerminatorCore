class BusinessException(Exception):
    """
    业务异常
    记录业务逻辑上的异常
    """
    def __init__(self, message, code: int = None):
        self.message = message
        self.code = code


class ServiceException(Exception):
    """
    服务异常
    服务本身存在异常,如链接关闭,代码错误等,需要额外进行处理的异常
    """
    def __init__(self, message, code: int = None):
        self.message = message
        self.code = code


class InfoException(Exception):
    """
    日志级别的异常
    通常不用特殊处理,记录日志后即可
    """
    def __init__(self, message, code: int = None):
        self.message = message
        self.code = code


class SysException(Exception):
    """
    系统级别的异常,返回错误状态码
    """
    def __init__(self, message, status_code: int = 530):
        self.message = message
        self.status_code = status_code

