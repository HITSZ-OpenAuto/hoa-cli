# hoa-majors

## 项目简介

本项目用于从 **哈尔滨工业大学（深圳）教务系统** 抓取各年级、各专业的培养方案课程数据，并将其规范化后保存为 TOML 格式文件，便于后续查询与分析。

---

## 目录结构

```text
├── src/hoa_majors/       # 核心代码包
│   ├── cli/              # 命令行工具
│   │   ├── crawl.py      # 抓取数据
│   │   ├── table.py      # 查找表管理
│   │   ├── search.py     # 课程查询
│   │   └── audit.py      # 冲突审计
│   ├── core/             # 核心逻辑
│   ├── data/             # 培养方案数据 (打包在包内)
│   │   ├── SCHOOL_MAJORS/ # 专业课程 TOML 文件
│   │   ├── lookup_table.py # 课程代码查找表
│   │   └── major_mapping.json # 专业映射数据
│   └── config.py         # 配置管理
├── tests/                # 测试脚本
├── pyproject.toml        # 项目配置
├── .env.example          # 环境变量模板
└── README.md             # 项目文档
```

---

## 数据说明

本项目将抓取的培养方案数据打包在 `src/hoa_majors/data/` 目录下。当你通过 `pip` 或 `uv` 安装本项目后，CLI 工具会自动识别并使用这些内置数据。

如果你需要使用自定义的数据目录，可以通过 `--data-dir` 参数指定。

---

## 安装说明

推荐使用 `uv` 进行安装和管理：

```sh
# 安装依赖并创建虚拟环境
uv sync
```

---

## 使用流程

### 1. 配置环境

1. 复制 `.env.example` 为 `.env`：
   ```sh
   cp .env.example .env
   ```
2. 编辑 `.env` 文件，填入你的 `JW_COOKIE`。

### 2. 抓取数据

使用统一的抓取命令：

```sh
uv run hoa-crawl
```

该命令会先更新专业映射关系，然后抓取所有专业的课程数据并保存到内置的数据目录。

### 3. 维护查找表

初始化查找表：
```sh
uv run hoa-table init
```

增量更新查找表（添加新出现的课程）：
```sh
uv run hoa-table update
```

### 4. 课程查询

快速查找课程所在文件：
```sh
uv run hoa-search [课程代码]
```

### 5. 冲突审计

检测同名课程但代码不同的冲突：
```sh
uv run hoa-audit
```

---

## 开发与测试

### 运行测试脚本

可以使用 `uv run` 直接运行 `tests/` 目录下的脚本：

```sh
uv run python tests/get_course_single.py
```

### 代码格式化与检查

推荐使用 `ruff` 进行代码检查和格式化（已在 `pyproject.toml` 中配置）：

```sh
# 运行 linter
uv run ruff check .

# 运行 formatter
uv run ruff format .
```

---

## GitHub Action 使用

本项目提供了一个 GitHub Composite Action，方便其他仓库直接调用 CLI 工具。

### 示例用法

```yaml
steps:
  - uses: actions/checkout@v6
  - uses: HITSZ-OpenAuto/hoa-majors@main

  - name: List plans
    run: hoa-plans
```

---

## 输出格式示例

生成的 TOML 文件格式：

```toml
[info]
year = "2023"
major_name = "计算机科学与技术"
...

[[courses]]
course_code = "COMP1003"
course_name = "C语言程序设计I"
credit = 3.0
total_hours = 48
...
[courses.hours]
theory = 32
lab = 16
...
```

---

## 开发说明

本项目采用模块化设计：
- `hoa_majors.core.fetcher`: 负责 API 请求
- `hoa_majors.core.parser`: 负责数据清洗与 TOML 格式化
- `hoa_majors.core.writer`: 负责文件写入
- `hoa_majors.core.utils`: 共享工具函数
