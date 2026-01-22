import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from hoa_majors.config import (
    COURSE_URL,
    FAH_URL,
    HEADERS_FORM,
    HEADERS_JSON,
    JW_COOKIE,
    MAJOR_LIST_URL,
    PROXIES,
    logger,
)


def create_session() -> requests.Session:
    """创建带有重试机制的 requests Session"""
    session = requests.Session()
    session.proxies = PROXIES

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


# 全局 session 实例
_session = create_session()
_warned_missing_cookie = False


def _ensure_cookie_warning():
    """Log a warning once if JW_COOKIE is missing when making JW requests."""
    global _warned_missing_cookie
    if _warned_missing_cookie:
        return
    if not JW_COOKIE:
        logger.warning("JW_COOKIE 未配置，请在 .env 文件或环境变量中设置")
        logger.info("提示: 可以复制 .env.example 为 .env 并填入你的 Cookie")
        _warned_missing_cookie = True


def fetch_courses_by_fah(fah: str) -> list[dict]:
    """
    Crawl the JW API for a specific FAH (培养方案号).
    Return a list of raw course dicts.
    """
    _ensure_cookie_warning()
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

    try:
        resp = _session.post(COURSE_URL, headers=HEADERS_FORM, data=payload, timeout=15)
        resp.raise_for_status()
        resp_json = resp.json()
        raw_list = resp_json.get("content", {}).get("list", [])
        return [{k: v for k, v in item.items() if v is not None} for item in raw_list]
    except Exception as e:
        logger.error(f"获取培养方案 {fah} 的课程列表失败: {e}")
        return []


def get_fah_list(njdm: str) -> list[dict]:
    """
    获取指定年级的培养方案列表
    """
    _ensure_cookie_warning()
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

    try:
        resp = _session.post(FAH_URL, headers=HEADERS_FORM, data=data, timeout=15)
        resp.raise_for_status()
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
    except Exception as e:
        logger.error(f"获取年级 {njdm} 的培养方案列表失败: {e}")
        return []


def get_major_list_by_dalei(yzydm: str, xn: str = "2024-2025", xq: str = "2") -> list[dict]:
    """
    根据大类专业代码查询其下的分流专业列表
    """
    _ensure_cookie_warning()
    data = {
        "kglx": "0",
        "xn": xn,
        "xq": xq,
        "yzydm": yzydm,
    }

    try:
        resp = _session.post(MAJOR_LIST_URL, headers=HEADERS_JSON, json=data, timeout=10)
        resp.raise_for_status()
        resp_json = resp.json()
        return [{k: v for k, v in item.items() if v is not None} for item in resp_json]
    except Exception as e:
        logger.error(f"查询大类 {yzydm} 的专业列表失败: {e}")
        return []
