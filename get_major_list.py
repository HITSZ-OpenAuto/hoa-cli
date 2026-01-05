import json

import requests

# 查询专业方向
# url = "https://jw.hitsz.edu.cn/xjgl/xjxxgl/xsxxdate/queryZyFxList?sf_request_type=ajax"

# 查询大类专业
url = "https://jw.hitsz.edu.cn/xjgl/dlfzysq/querydlzyd?sf_request_type=ajax"


headers = {
    "Content-Type": "application/json",
    "Cookie": "_qimei_uuid42=196031207051009c516abefb4710507b8457eedf87; _qimei_i_3=76ed518a9c5902dd9797fc310e8c7ae1a6e6f1f8410f0282e2dd7b092794243d676433943c89e29e8295; _qimei_h38=; tenantId=default; _qimei_i_1=54c552e1c132; _qimei_fingerprint=1418c5a93b1a523ba3a18392c8f2792d; route=35e0bb97cd8b3ec63836645aa32ed39c; JSESSIONID=E094FF2680F6427212E3B0902CF8FDE9",
    "RoleCode": "01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

# 查询专业方向
# data = {
#     "pylx": "1",
#     "yxdm": "600002",
#     "zydm": "050102",
# }

# 查询大类专业
data = {
    "kglx": "0",  # 开关类型
    # "xh": "",  # 学号
    "xn": "2024-2025",  # 学年
    "xq": "2",  # 学期
    "yzydm": "23L02",  # 原专业代码
}

proxies = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}


resp = requests.post(url, headers=headers, json=data, proxies=proxies)

# 解析返回的 JSON
resp_json = resp.json()

# print(resp_json)

# 过滤每个元素，只保留值不为 None 的字段
filtered_list = []
for item in resp_json:
    filtered_item = {k: v for k, v in item.items() if v is not None}
    filtered_list.append(filtered_item)

# 输出
for i, item in enumerate(filtered_list, 1):
    print(json.dumps(item, ensure_ascii=False, indent=2))
