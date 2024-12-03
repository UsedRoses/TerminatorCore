import traceback
from django.utils.deprecation import MiddlewareMixin
from TerminatorBaseCore.common.error_code import ERROR_CODE, SUCCESS_CODE
from TerminatorBaseCore.entity.exception import BusinessException, InfoException, ServiceException
from TerminatorBaseCore.entity.response import ServiceJsonResponse


class ExceptionHandlingMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):
        traceback.print_exc()
        if isinstance(exception, BusinessException):
            error_code = exception.code if exception.code else ERROR_CODE
            # 多语言处理
            return ServiceJsonResponse(error_code, exception.message)
        elif isinstance(exception, ServiceException):
            return ServiceJsonResponse(ERROR_CODE, exception.message)
        elif isinstance(exception, InfoException):
            return ServiceJsonResponse(SUCCESS_CODE, exception.message)
        elif isinstance(exception, Exception):
            # 保存错误日志
            return ServiceJsonResponse(ERROR_CODE, str(exception))