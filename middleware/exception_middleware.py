import traceback
import os
from django.http import JsonResponse
from TerminatorBaseCore.common.error_code import ERROR_CODE, SUCCESS_CODE
from TerminatorBaseCore.components.dynamic_call import HandleRegister, BusinessExceptionAfterHandle, \
    ServiceExceptionAfterHandle, InfoExceptionAfterHandle, ExceptionAfterHandle, SysExceptionAfterHandle
from TerminatorBaseCore.entity.exception import BusinessException, InfoException, ServiceException, SysException
from TerminatorBaseCore.entity.response import ServiceJsonResponse


class ExceptionHandlingMiddleware:
    def __init__(self, get_response):
        # 这个方法在每次请求时只会被调用一次，通常用于初始化配置
        self.get_response = get_response

    def __call__(self, request):
        # 通过 get_response 传递给下一个中间件或视图
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, BusinessException):
            error_code = exception.code if exception.code else ERROR_CODE
            HandleRegister.instance_and_execute(BusinessExceptionAfterHandle.AfterHandleName, request,
                                                message=exception.message)
            return ServiceJsonResponse(error_code, exception.message)

        elif isinstance(exception, ServiceException):
            stack_info = log_exception_with_stack(exception)
            HandleRegister.instance_and_execute(ServiceExceptionAfterHandle.AfterHandleName, request,
                                                message=exception.message, stack_info=stack_info)
            return ServiceJsonResponse(ERROR_CODE, exception.message)

        elif isinstance(exception, InfoException):
            HandleRegister.instance_and_execute(InfoExceptionAfterHandle.AfterHandleName, request,
                                                message=exception.message)
            return ServiceJsonResponse(SUCCESS_CODE, exception.message)

        elif isinstance(exception, SysException):
            stack_info = log_exception_with_stack(exception)
            HandleRegister.instance_and_execute(SysExceptionAfterHandle.AfterHandleName, request,
                                                message=str(exception), stack_info=stack_info)
            return JsonResponse(
                {"detail": exception.message},
                status=exception.status_code
            )

        elif isinstance(exception, Exception):
            stack_info = log_exception_with_stack(exception)
            HandleRegister.instance_and_execute(ExceptionAfterHandle.AfterHandleName, request,
                                                message=str(exception), stack_info=stack_info)
            return ServiceJsonResponse(ERROR_CODE, str(exception))


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def log_exception_with_stack(exception):
    """
    捕获调用链并记录日志，优化性能
    """
    # 提取异常堆栈信息
    formatted_stack = traceback.format_tb(exception.__traceback__)

    # 过滤非项目路径
    filtered_stack = []
    for frame in formatted_stack:
        # 如果路径包含 .venv 或 site-packages，跳过
        if ".venv" in frame or "site-packages" in frame:
            continue

        filtered_stack.append(frame)

    # 根因：记录最初抛出异常的地方
    root_cause = filtered_stack[-1] if filtered_stack else "Unknown location"

    # 拼接堆栈信息
    stack_trace = "\n".join(filtered_stack)


    # 抛出异常，附带过滤后的堆栈信息
    return (
        f"Exception occurred: {exception}\n"
        f"Root cause: {root_cause}\n"
        f"Stack trace:\n{stack_trace}"
    )
