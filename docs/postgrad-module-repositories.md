# 研究生专业选修模块仓库映射

本清单根据 `202509` 版研究生培养方案审计结果整理，用于创建
HITSZ-OpenAuto 的研究生专业选修聚合仓库和分模块仓库。

## 约定

- 所有研究生专业统一展示聚合入口 `PostgradElectives`。
- 分模块仓库使用 `Postgrad-*` 前缀，并按学科而不是培养层次拆分。
- 同一学科的硕士、博士模块写在同一仓库的不同章节中。
- `MA`、`DA` 等模块代码只用于核对培养方案，不作为仓库名。
- 具体课程由各分模块仓库的 Markdown 维护，不由培养方案数据决定。
- `选修课清单` 与 `选修课程清单` 视为同一种名称；因此两个 `MD` 条目合并。

## 聚合仓库

| 仓库 | 页面标题 | 用途 |
| --- | --- | --- |
| `PostgradElectives` | 研究生专业选修 | 所有研究生专业共用入口，按学科链接到分模块仓库 |

## 分模块仓库

| 仓库 | 学科 | 硕士模块 | 博士模块 |
| --- | --- | --- | --- |
| `Postgrad-ComputerScience` | 计算机科学与技术 | MA | DA |
| `Postgrad-InformationCommunication` | 信息与通信工程 | MC | DC |
| `Postgrad-MechanicalEngineering` | 机械工程 | MD | DD |
| `Postgrad-PowerEngineering` | 动力工程及工程热物理 | ME | DE |
| `Postgrad-ElectricalEngineering` | 电气工程 | MF | DF |
| `Postgrad-Control` | 控制科学与工程 | MG | DG |
| `Postgrad-Materials` | 材料科学与工程 | MJ | DJ |
| `Postgrad-Architecture` | 建筑学 | ML | DL |
| `Postgrad-Chemistry` | 化学 | MQ | DQ |
| `Postgrad-Design` | 设计学 | MS | DS |
| `Postgrad-Aerospace` | 航空宇航科学与技术 | MT | DT |
| `Postgrad-IntegratedCircuits` | 集成电路科学与工程 | MV | DV |
| `Postgrad-BiomedicalEngineering` | 生物医学工程 | MW | DW |
| `Postgrad-IntelligentScience` | 智能科学与技术 | MX | DX |
| `Postgrad-ManagementScience` | 管理科学与工程 | — | DM |
| `Postgrad-Transportation` | 交通运输工程 | — | DU |
| `Postgrad-OpticalEngineering` | 光学工程 | MB | — |
| `Postgrad-CivilEngineering` | 土木工程 | MH | — |
| `Postgrad-EnvironmentalEngineering` | 环境科学与工程 | MI | — |
| `Postgrad-UrbanPlanning` | 城乡规划学 | MK | — |
| `Postgrad-AppliedEconomics` | 应用经济学 | MM | — |
| `Postgrad-BusinessAdministration` | 工商管理学 | MN | — |
| `Postgrad-Mathematics` | 数学 | MO | — |
| `Postgrad-Physics` | 物理学 | MP | — |
| `Postgrad-Mechanics` | 力学 | MR | — |
| `Postgrad-Marxism` | 马克思主义理论 | MU | — |

## 完整性核对

- 聚合仓库：1 个。
- 分模块仓库：26 个。
- 硕博合并学科：14 个。
- 仅博士学科：2 个。
- 仅硕士学科：10 个。
- 模块代码：硕士 24 个、博士 16 个，共 40 个，无重复、无遗漏。

## 后续执行顺序

1. 确认上述仓库 ID。
2. 创建 `PostgradElectives` 和 26 个分模块仓库。
3. 在分模块仓库中建立硕士、博士章节；没有对应培养层次时不创建空章节。
4. 在 `PostgradElectives` 中按学科列出 26 个入口。
5. 等待现有 `repos-management` workflow 自动更新 `repos_list.txt`。
6. 确认仓库已被收录后，再修改 `hoa-major-data` 和 `hoa-backend`。
