from abc import ABC, abstractmethod

_subclasses = {}


class HandleRegister(ABC):

    @classmethod
    def set_subclasses(cls, name, sub_cls):
        if name not in _subclasses:
            _subclasses[name] = sub_cls
            print(f"Registered subclass: {sub_cls.__name__} for {name}")

    @classmethod
    def get_instance(cls, code_name):
        code_class = _subclasses.get(code_name)
        if not code_class:
            return None
        return code_class()

    @abstractmethod
    def execute(self, *arg, **keyword):
        pass

    @classmethod
    def instance_and_execute(cls, code_name, *arg, **keyword):
        instance = cls.get_instance(code_name)
        if instance:
            instance.execute(*arg, **keyword)


class BusinessExceptionAfterHandle(HandleRegister):
    AfterHandleName = "BusinessExceptionAfter"

    def __init_subclass__(cls, **kwargs):
        """动态注册子类"""
        super().__init_subclass__(**kwargs)
        HandleRegister.set_subclasses(cls.AfterHandleName, cls)


class ServiceExceptionAfterHandle(HandleRegister):
    AfterHandleName = "ServiceExceptionAfter"

    def __init_subclass__(cls, **kwargs):
        """动态注册子类"""
        super().__init_subclass__(**kwargs)
        HandleRegister.set_subclasses(cls.AfterHandleName, cls)


class InfoExceptionAfterHandle(HandleRegister):
    AfterHandleName = "InfoExceptionAfter"

    def __init_subclass__(cls, **kwargs):
        """动态注册子类"""
        super().__init_subclass__(**kwargs)
        HandleRegister.set_subclasses(cls.AfterHandleName, cls)


class ExceptionAfterHandle(HandleRegister):
    AfterHandleName = "ExceptionAfter"

    def __init_subclass__(cls, **kwargs):
        """动态注册子类"""
        super().__init_subclass__(**kwargs)
        HandleRegister.set_subclasses(cls.AfterHandleName, cls)


class SysExceptionAfterHandle(HandleRegister):
    AfterHandleName = "SysExceptionAfter"

    def __init_subclass__(cls, **kwargs):
        """动态注册子类"""
        super().__init_subclass__(**kwargs)
        HandleRegister.set_subclasses(cls.AfterHandleName, cls)
