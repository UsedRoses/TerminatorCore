from django.utils.deprecation import MiddlewareMixin


class TokenMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        # 检查是否有新生成的 token
        if hasattr(request, "new_token") and request.new_token:
            # 可以将 token 加入响应头
            response["X-Token"] = request.new_token

        return response
