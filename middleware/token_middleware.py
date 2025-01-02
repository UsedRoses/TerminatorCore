

class TokenMiddleware:
    def __init__(self, get_response):
        """
        初始化中间件，并接收下一个中间件或视图的响应函数。
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        处理请求并传递给下一个中间件或视图。
        """
        # 先通过 get_response 处理请求
        response = self.get_response(request)

        # 检查是否有新生成的 token
        if hasattr(request, "new_token") and request.new_token:
            # 将 token 加入响应头
            response["X-Token"] = request.new_token

        return response

