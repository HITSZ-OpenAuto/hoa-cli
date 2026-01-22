"""
统一配置管理模块

从 .env 文件或环境变量中读取敏感配置信息。
"""

import logging
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hoa_majors")

# 尝试加载 python-dotenv（如果已安装）
try:
    from dotenv import load_dotenv

    # 加载 .env 文件
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    # 如果没有安装 python-dotenv，仅使用环境变量
    pass


def get_env(key: str, default: str = "") -> str:
    """获取环境变量，如果不存在则返回默认值"""
    return os.getenv(key, default)


# -------------------------------------------------------------------------------------------------
# Cookie 配置
# -------------------------------------------------------------------------------------------------

JW_COOKIE = get_env("JW_COOKIE", "")

# -------------------------------------------------------------------------------------------------
# 代理配置
# -------------------------------------------------------------------------------------------------

HTTP_PROXY = get_env("HTTP_PROXY", "")
HTTPS_PROXY = get_env("HTTPS_PROXY", "")

PROXIES = {}
if HTTP_PROXY:
    PROXIES["http"] = HTTP_PROXY
if HTTPS_PROXY:
    PROXIES["https"] = HTTPS_PROXY

# -------------------------------------------------------------------------------------------------
# 请求头配置
# -------------------------------------------------------------------------------------------------

# 通用请求头（表单类型）
HEADERS_FORM = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": JW_COOKIE,
    "RoleCode": "01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

# 通用请求头（JSON 类型）
HEADERS_JSON = {
    "Content-Type": "application/json",
    "Cookie": JW_COOKIE,
    "RoleCode": "01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

# -------------------------------------------------------------------------------------------------
# API URLs
# -------------------------------------------------------------------------------------------------

# 培养方案查询
FAH_URL = "https://jw.hitsz.edu.cn/faxq/query?sf_request_type=ajax"

# 课程列表查询
COURSE_URL = "https://jw.hitsz.edu.cn/Njpyfakc/queryList?sf_request_type=ajax"

# 大类专业列表查询
MAJOR_LIST_URL = "https://jw.hitsz.edu.cn/xjgl/dlfzysq/querydlzyd?sf_request_type=ajax"


# -------------------------------------------------------------------------------------------------
# 路径配置
# -------------------------------------------------------------------------------------------------

# 默认数据目录
DEFAULT_DATA_DIR = Path(__file__).parent / "data"

# 子目录：专业培养方案 TOML 集合
PLANS_SUBDIR = "plans"
