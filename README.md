# hoa-majors

[![Build and Verify](https://github.com/HITSZ-OpenAuto/hoa-majors/actions/workflows/build.yml/badge.svg)](https://github.com/HITSZ-OpenAuto/hoa-majors/actions/workflows/build.yml)
[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

本项目用于从 **哈尔滨工业大学（深圳）教务系统** 抓取各年级、各专业的培养方案课程数据，并将其规范化后保存为 TOML 格式文件，便于后续查询与分析。

## 快速开始

```sh
# 设置环境
make prepare

# 配置 cookie
cp .env.example .env
# 编辑 .env 填入 JW_COOKIE

# 抓取培养方案与课程数据
uv run hoa crawl

# 列出所有已抓取的培养方案
uv run hoa plans

# 列出特定培养方案的所有课程
uv run hoa courses <plan_id>

# 获取培养方案中特定课程的详细信息
uv run hoa info <plan_id> <course_code>

# 通过课程代码找出培养方案
uv run hoa search <course_code>

# 审计课程名称与代码的冲突
uv run hoa audit
```

## GitHub Action

```yaml
steps:
  - uses: actions/checkout@v6
  - uses: HITSZ-OpenAuto/hoa-majors@main
  - run: hoa plans
```
