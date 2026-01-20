import requests

from hoa_majors.config import (
    COURSE_URL,
    FAH_URL,
    HEADERS_FORM,
    HEADERS_JSON,
    MAJOR_LIST_URL,
    PROXIES,
)


def fetch_courses_by_fah(fah: str) -> list[dict]:
    """
    Crawl the JW API for a specific FAH (培养方案号).
    Return a list of raw course dicts.
    """
    payload = {
        "bglx": "",
        "multiple": "false",
        "sfcx": "",
        "pylx": "1",
        "pylb": "1",
        "fah": fah,
        "bgid": "",
        "kcmc": "",
        "yxdm": "",
        "xqdm": "",
        "kclbdm": "",
        "kcxzdm": "",
        "order1": "",
        "order2": "",
        "pageNum": 1,
        "pageSize": 999,
    }

    resp = requests.post(COURSE_URL, headers=HEADERS_FORM, data=payload, proxies=PROXIES)
    resp_json = resp.json()

    raw_list = resp_json.get("content", {}).get("list", [])
    clean_list = [{k: v for k, v in item.items() if v is not None} for item in raw_list]

    return clean_list


def get_fah_list(njdm: str) -> list[dict]:
    """
    获取指定年级的培养方案列表
    """
    data = {
        "sf_request_type": "ajax",
        "key": "",
        "xkdm": "",
        "yxdm": "",
        "zydm": "",
        "zyfxdm": "",
        "bbh": "",
        "ywdm": "",
        "falx": "3",
        "njdm": njdm,
        "cxby": "",
        "pylb": "1",
        "order1": "",
        "order2": "",
        "falxdm": "",
        "kzsjqx": "0",
        "py_xssfcxzj_zx": "1",
        "py_xssfcxzj_fx": "1",
        "sfdl": "",
        "pageNum": "1",
        "pageSize": "500",
    }

    resp = requests.post(FAH_URL, headers=HEADERS_FORM, data=data, proxies=PROXIES)
    resp_json = resp.json()

    raw_list = resp_json.get("content", {}).get("list", [])

    result = []
    for item in raw_list:
        if item.get("falxdm") != "1":
            continue
        result.append(
            {
                "fah": item.get("fah"),
                "zydm": item.get("zydm"),
                "zymc": item.get("zymc"),
                "yxmc": item.get("yxmc"),
            }
        )
    return result


def get_major_list_by_dalei(yzydm: str, xn: str = "2024-2025", xq: str = "2") -> list[dict]:
    """
    根据大类专业代码查询其下的分流专业列表
    """
    data = {
        "kglx": "0",
        "xn": xn,
        "xq": xq,
        "yzydm": yzydm,
    }

    try:
        resp = requests.post(
            MAJOR_LIST_URL, headers=HEADERS_JSON, json=data, proxies=PROXIES, timeout=10
        )
        resp_json = resp.json()
        result = []
        for item in resp_json:
            filtered_item = {k: v for k, v in item.items() if v is not None}
            result.append(filtered_item)
        return result
    except Exception as e:
        print(f"查询大类 {yzydm} 的专业列表失败: {e}")
        return []
