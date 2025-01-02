import hashlib
import time
from functools import wraps

from django.conf import settings
from django_redis import get_redis_connection
from TerminatorBaseCore.common.error_code import ERROR_CODE
from TerminatorBaseCore.entity.exception import ServiceException
from rest_framework.request import Request

from TerminatorBaseCore.utils.ip_util import get_client_ip

# 记录用户的行为（Bitmap中用1位表示）
BITMAP_KEY = "rate_limit_bitmap"

redis = get_redis_connection("default")

product_name = settings.PROJECT_NAME if settings.PROJECT_NAME else "T800"


def _get_bitmap_offset(limit_key):
    # 使用md5对user_id进行哈希，生成128位的哈希值
    user_id_hash = hashlib.md5(limit_key.encode('utf-8')).hexdigest()
    # 转换为整数，然后对位数进行取模，避免过大的偏移量
    return int(user_id_hash, 16) % (1 << 24)  # 大约占用2M空间,可存16,777,216条数据


def check_rate_limit(limit_key, limit, refill_rate, freq_threshold):
    # 定义Bitmap的位偏移量（用user_id来计算）
    bitmap_offset = _get_bitmap_offset(limit_key)

    # 判断用户是否已超过频率阈值
    user_flag = redis.getbit(BITMAP_KEY, bitmap_offset)

    current_count_key = f"{product_name}:request_count:{limit_key}"
    if not user_flag:
        # 初始阶段，未达到阈值
        current_count = redis.get(current_count_key)

        if current_count is None:
            current_count = 0
        current_count = int(current_count) + 1

        # 更新请求次数
        redis.set(current_count_key, current_count, ex=1800)  # 请求计数器15min后过期

        # 达到阈值后，标记Bitmap
        if current_count >= freq_threshold:
            redis.setbit(BITMAP_KEY, bitmap_offset, 1)
            redis.expire(BITMAP_KEY, 600)

        return True  # 允许请求

    else:
        if redis.exists(current_count_key):
            # 达到阈值后进入令牌桶限流
            return _token_bucket_rate_limit(limit_key, limit, refill_rate)
        else:
            redis.setbit(BITMAP_KEY, bitmap_offset, 0)
            redis.expire(BITMAP_KEY, 600)
            return True


def _token_bucket_rate_limit(limit_key, limit, refill_rate):
    """
    令牌桶算法限流
    """
    key = f"{product_name}:token_bucket:{limit_key}"
    current_time = time.time()

    # 获取桶的状态
    bucket_data = redis.hmget(key, "tokens", "last_refill")
    tokens = int(bucket_data[0]) if bucket_data[0] else limit
    last_refill = float(bucket_data[1]) if bucket_data[1] else current_time

    # 计算自上次请求以来生成的令牌数
    time_since_last_refill = current_time - last_refill
    # 每5分钟生产refill_rate个令牌
    new_tokens = int(time_since_last_refill / 300) * refill_rate

    # 更新令牌数，并确保不超过桶的上限
    tokens = min(limit, tokens + new_tokens)
    last_refill = current_time

    # 判断请求是否可以通过
    if tokens > 0:
        tokens -= 1
        # 更新 Redis 中的桶状态
        redis.hmset(key, {"tokens": tokens, "last_refill": last_refill})
        redis.expire(key, 1800)
        return True
    else:
        raise ServiceException(code=ERROR_CODE, message="Too many requests. Please try again later.")


def rate_limit(limit, refill_rate, freq_threshold, key_params=None):
    """
    :param limit: 令牌桶最大令牌数
    :param refill_rate: 令牌桶每5分钟生成的令牌数, 一般是小于limit的
    :param freq_threshold: 15分钟内达到该阈值后进入令牌桶限流
    :param key_params:
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成限流 key，根据指定的参数名从 kwargs 或 args 中获取
            if key_params:
                keys = []
                for key_param in key_params:
                    keys.append(str(get_param_value(key_param, args, kwargs, func)))
                # 使用 f"" 拼接多个 key 参数
                limit_key = ":".join(keys)
            else:
                limit_key = func.__name__
                for arg in args:
                    if isinstance(arg, Request):
                        request = args[1]
                        # 默认使用请求IP限流
                        limit_key = limit_key + ':' + get_client_ip(request)

            check_rate_limit(limit_key, limit, refill_rate, freq_threshold)
            # 执行被装饰的函数
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_param_value(param, args, kwargs, func):
    """
    获取参数值，支持参数名或对象属性（如 token_request.email）
    """
    if '.' in param:
        # 处理对象属性访问，例如 token_request.email
        param_name, attr_name = param.split('.')
        if param_name in kwargs:
            obj = kwargs[param_name]
        else:
            arg_names = func.__code__.co_varnames
            index = list(arg_names).index(param_name)
            obj = args[index]
        # 使用 getattr 获取属性值
        return getattr(obj, attr_name)
    else:
        # 处理普通参数名
        if param in kwargs:
            return kwargs[param]
        else:
            arg_names = func.__code__.co_varnames
            index = list(arg_names).index(param)
            return args[index]
