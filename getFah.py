import requests
import json

url = "https://jw-hitsz-edu-cn.hitsz.edu.cn/faxq/query?sf_request_type=ajax"

headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "platformMultilingual_-_edu.cn=zh_CN; sdp_user_token=3f08ce29-36d8-4c79-9668-2c12062b8fda_c6eaa3cb-d96a-4eb6-8ee3-0f82c4d338ea; route=3b070995537f3ced53f80b7b8ee3a634; JSESSIONID=07E77EC3729B2A3DD47B1689369886E2",
    "RoleCode": "01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

data = {
    "sf_request_type": "ajax",
    "key": "",#选填，方案名称/专业名称的模糊搜索"AI"->"2025级/[600054]基础学部/[23L01]工科试验班（计算机与电子通信）"
    "xkdm": "",#课程代码（选填），空表示不过滤。
    "yxdm": "",#院系代码（选填），空表示获取所有院系方案。
    "zydm": "",#专业代码（选填），空表示获取所有专业方案。
    "zyfxdm": "",#专业方向代码（选填），空表示获取所有方向。
    "bbh": "",#可能是版本号的意思
    "ywdm": "",#选填，业务代码？不知道
    "falx": "3", #必填，方案类型，必须为3，不知道为什么
    "njdm": "2023",#选填，年级代码，查询某个年级的方案
    "cxby": "",#查询毕业要求？选填，空表示不过滤，似乎无用
    "pylb": "1",
    "order1": "",
    "order2": "",
    "falxdm": "",#关键，不过没搞明白为什么，填写1只能获取我的专业，空着可获取其他部分专业内容
    "kzsjqx": "0",
    "py_xssfcxzj_zx": "1",
    "py_xssfcxzj_fx": "1",
    "sfdl": "",
    "pageNum": "1",
    "pageSize": "200"
}

proxies = {
    "http": "http://127.0.0.1:7897",
    "https": "http://127.0.0.1:7897"
}


resp = requests.post(url, headers=headers, data=data, proxies=proxies)

# 解析返回的 JSON
resp_json = resp.json()

# 获取 content["list"]
raw_list = resp_json.get("content", {}).get("list", [])

# 过滤每个元素，只保留值不为 None 的字段
filtered_list = []
for item in raw_list:
    filtered_item = {k: v for k, v in item.items() if v is not None}
    filtered_list.append(filtered_item)

# 输出
for i, item in enumerate(filtered_list, 1):
    print(f"符合的培养方案 {i}:")
    print(json.dumps(item, ensure_ascii=False, indent=2))
