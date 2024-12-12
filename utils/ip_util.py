import socket
import struct

from rest_framework.request import Request


def get_ipv4():
    # 获取当前机器的主机名
    hostname = socket.gethostname()

    # 获取该主机的IPv4地址（第一优先）
    ip_address = socket.gethostbyname(hostname)

    return ip_address


def get_ipv4_to_int():
    ip = get_ipv4()
    # 将 IPv4 地址字符串转换为整数
    return struct.unpack("!I", socket.inet_aton(ip))[0]


def get_client_ip(request: Request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')  # 设置默认值
    return ip