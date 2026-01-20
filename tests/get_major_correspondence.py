import json
import sys
from pathlib import Path

import requests

# 将父目录添加到路径，以便导入 config 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import HEADERS_JSON as HEADERS
from config import PROXIES

# 查询专业方向
# url = "https://jw.hitsz.edu.cn/xjgl/xjxxgl/xsxxdate/queryZyFxList?sf_request_type=ajax"

# 查询大类专业
url = "https://jw.hitsz.edu.cn/xjgl/dlfzysq/querydlzyd?sf_request_type=ajax"

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
    "yzydm": "23L01",  # 原专业代码
}


resp = requests.post(url, headers=HEADERS, json=data, proxies=PROXIES)

# 解析返回的 JSON
resp_json = resp.json()

# print(resp_json)

# 过滤每个元素，只保留值不为 None 的字段
filtered_list = []
for item in resp_json:
    filtered_item = {k: v for k, v in item.items() if v is not None}
    filtered_list.append(filtered_item)

# 输出样例：
# {
#     "ZYDM": "050101",
#     "XSZYDM": "050101",
#     "ZYMC": "材料科学与工程",
# }
for _i, item in enumerate(filtered_list, 1):
    print(json.dumps(item, ensure_ascii=False, indent=2))
