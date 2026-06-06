# hoa-cli

[![Build and Verify](https://github.com/HITSZ-OpenAuto/hoa-cli/actions/workflows/build.yml/badge.svg)](https://github.com/HITSZ-OpenAuto/hoa-cli/actions/workflows/build.yml)
[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

本项目用于从 **哈尔滨工业大学（深圳）教务系统** 抓取各年级、各专业的培养方案课程数据，并将其规范化后保存为 TOML 格式文件，便于后续查询与分析。

当前同时支持：

- 本科培养方案抓取（按 `grade`）
- 研究生培养方案抓取（按 `bbh`，即年份月份版本号）

## 安装

直接安装 CLI 工具到系统中：

```sh
uv tool install git+https://github.com/HITSZ-OpenAuto/hoa-cli.git
```

## 快速开始

```sh
# 设置环境
make prepare

# 配置 cookie
cp .env.example .env
# 编辑 .env 填入 JW_COOKIE

# 抓取培养方案与课程数据
uv run hoa crawl

# 抓取研究生培养方案与课程数据
uv run hoa crawl-postgrad --bbh 202509

# 列出所有已抓取的培养方案
uv run hoa plans

# 列出特定培养方案的所有课程
uv run hoa courses <plan_id>

# 获取培养方案中特定课程的详细信息
uv run hoa info <plan_id> <course_code>
```

## 研究生抓取

研究生抓取使用独立子命令：

```sh
uv run hoa crawl-postgrad --bbh 202509
```

常用参数：

- `--bbh`：必填，可传一个或多个研究生培养方案版本号，例如 `202509`、`202603`
- `--data-dir`：数据输出目录，默认使用 `src/hoa_cli/data`
- `--mapping-file`：可选，自定义研究生映射文件路径；默认输出到 `{data_dir}/postgrad_mapping.json`

输出内容：

- 研究生专业映射文件：`src/hoa_cli/data/postgrad_mapping.json`
- 研究生培养方案课程文件：`src/hoa_cli/data/plans/{bbh}_研_{专业名}.toml`

如果只想重抓少数几个研究生专业，可使用仓库内的辅助脚本：

```sh
PYTHONPATH=src python scripts/rebuild_postgrad_majors.py --bbh 202509 --major-codes 0813 085501
```

该脚本会复用当前研究生抓取逻辑，只重建指定 `major_code` 对应的 TOML 文件。

## GitHub Action

```yaml
steps:
  - uses: actions/checkout@v6
  - uses: HITSZ-OpenAuto/hoa-cli@main
  - run: hoa plans
```
