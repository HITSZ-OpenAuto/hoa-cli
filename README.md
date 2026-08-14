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

名称包含“留学生”的培养方案不会进入研究生课程文件。正式抓取使用严格请求模式；
映射、课组或课程请求失败时会立即中止，避免以空数据或部分数据覆盖已有文件。

如果只想重抓少数几个研究生专业，可使用仓库内的辅助脚本：

```sh
PYTHONPATH=src python scripts/rebuild_postgrad_majors.py --bbh 202509 --major-codes 0813 085501
```

该脚本会复用当前研究生抓取逻辑，只重建指定 `major_code` 对应的 TOML 文件。

在调整研究生专业选修模块过滤规则前，可先运行只读审计脚本：

```sh
PYTHONPATH=src python scripts/audit_postgrad_modules.py --bbh 202509
```

脚本默认扫描原始课组树及所有叶子课组的课程结果，排除名称含“留学生”的培养方案，
并输出带时间戳的新报告（如 `postgrad_module_audit_202509_20260814-191500.json`）。报告会区分课组树中直接发现的模块、仅在课程
`kzmc` 中发现的隐式模块、推荐/其他模块关系以及涉及的专业和培养方案。使用 `--tree-only`
可进行较快但不完整的课组树扫描，使用 `--major-codes 0810 085402` 可限制审计范围。
如果任一培养方案无法获取课组树，报告会标记 `complete = false`、记录 `issues` 并以非零状态退出。

脚本在每份培养方案完成后原子更新报告。中断后使用与原命令相同的筛选参数，并通过
`--resume <报告路径>` 断点续跑。`--output` 只用于创建新报告，目标已存在时会拒绝覆盖；
只有显式使用 `--resume` 才会更新已有的 `schema_version = 2` 检查点。

```sh
PYTHONPATH=src python scripts/audit_postgrad_modules.py \
  --bbh 202509 --major-codes 0810 085402 \
  --resume postgrad_module_audit_202509_20260814-191500.json
```

## GitHub Action

```yaml
steps:
  - uses: actions/checkout@v6
  - uses: HITSZ-OpenAuto/hoa-cli@main
  - run: hoa plans
```
