# schema2doc — 基于 OpenCode 的 Spec-Driven Development 工作流

本文档记录了一个真实项目从概念到完成的开发流程，用于展示如何使用 OpenCode（AI 编排能力）
以「契约驱动」的方式从零构建一个零外部依赖的 Python CLI 工具。

---

## 方法论：Spec-Driven Development

整个开发过程严格遵循 **Spec-Driven Development** 原则：

1. **Spec First — 先写需求再实现.** 每个阶段都以一份明确的规格（PR/任务卡）为起点，
   spec 在交付前不可更改，保证行为可测。
2. **Separation of Concerns — 关注点分离.** 数据模型（DTO）、Inspector（采集）、
   Generators（渲染）、CLI（编排）各司其职，互不耦合，单一职责。
3. **Test-Driven Development — 测试驱动验收.** 每个数据结构、每个生成器方法都有对应单元测试；
   每个 CLI 入口都有 E2E subprocess 测试覆盖失败与成功路径。
4. **No External Dependencies — 零外部依赖内核.** 强制使用 Python 标准库，
   保证在任何环境都能运行，不引入编译、安装或版本锁定风险。

贯穿整个过程的核心约束是：**任何 UI/渲染代码都不应该自己读取数据库，只能消费 DTO。**
这就是关注点分离在工程实践中的体现。

---

## Architecture Decisions

### 1. DTO 与渲染解耦 (Data Transfer Objects vs Rendering)

```
Database (sqlite)  --PRAGMA-->  Inspector  --DTO-->  Generator  --Markdown/Mermaid-->  Output
```

- `models.py` 只定义纯 dataclass 数据结构，**不包含任何渲染逻辑**。
- `generators/mermaid.py` 和 `generators/markdown.py` 只负责把 DTO 转成文风不同的输出格式，
  无法访问数据库，无法修改数据。新增渲染器只需新建一个文件引用 `BaseInspector` 和 `Table` 即可。
- 验证刻意以「给定 DTO → 给定输入 → 期望输出」为主，确保两种层彼此独立。

### 2. 使用原生 PRAGMA 而非重 Inspector

SQLiteInspector 直接调用标准库 `sqlite3.connect(path)` 并执行 PRAGMA：

| PRAGMA | 用途 | 返回字段含义 |
|---|---|---|
| `sqlite_master` + `type='table'` | 表列表 | 名称、类型、权限 |
| `PRAGMA table_info('t')` | 列元数据 | cid, name, type, notnull, dflt_value, pk |
| `PRAGMA foreign_key_list('t')` | 外键定义 | from_column, target_table, target_column, on_delete, on_update |
| `PRAGMA index_list('t')` | 索引列表 | name, unique |
| `PRAGMA index_info(index_name)` | 索引列 | columns 内名字列表 |

为什么不用 `sqlparse` / `sqlalchemy` / `sqlglot` 这种「重」工具？
- 标准库零安装，PIE（预解释环境）里秒跑。
- PRAGMA 是 SQLite 的原生元数据接口，信息完整（PK、默认值、FK ON DELETE/UPDATE、索引归属）。
- 推理层（RAG）负责复杂场景（PostgreSQL），但本项目的核心目标是「跨平台快速文档化」，所以坚持标准库。

### 3. Mermaid 类型归一化 (Type Normalization)

Mermaid 的 ERDiagram 语法对类型名很苛刻——不允许空格、括号、特殊字符。因此写了
`MermaidGenerator.normalize_type()`，把 SQL 类型安全压缩：

```
VARCHAR(255)  →  string
INTEGER       →  int
REAL          →  float
DATETIME      →  datetime
NUMERIC/DECIMAL → number
                → fallback: 去括号小写
```

这个函数被 mermaid 和 markdown 两条渲染线复用，杜绝了因大小写、括号、分号导致的 Mermaid 语法错误。

### 4. CLI 设计：argparse + 默认值 + 可测试入口

`cli.py` 的 `main(argv: list[str] | None = None)` 接受可选参数列表，使
unittest 可以直接调用而无需依赖系统终端。exit code 通过 return 返回，
`__main__.py` 包装为 `sys.exit(main())`，便于 E2E 子进程测试。

---

## Iterative Phases

### Phase 1: Defects Contracts & SQLite Inspection

- **Spec:** 创建 `models.py` 四个 dataclass；实现 `base.py` 抽象基类；
  实现 `inspectors/sqlite.py` 通过 PRAGMA 从 `:memory:` 采集完整 schema。
- **Acceptance:** 测试创建 3-табличное тестовое дерево（users / orders / order_items）
  и проверяет没错：columнам, types, PK flags, FKs.
- **Tests:** `tests/test_sqlite_inspector.py` (5 тестов).
- **Outcome:** Neutral inspector，DTO 完全可用，为下一步渲染奠定数据基础。

### Phase 2: Renderer Mermaid ERD & Markdown Reports

- **Spec:** 给定 DTO → 生成 ```mermaid erDiagram；再给定同样的 DTO → 生成对应规范表格
  (Schema Details)。类型名必须规范化，FK 必须标注 PK/FK 标记符，orphan table 也应保留。
- **Acceptance:** 测试 `test_generators.py` (4 теста) + 字面验证生成的文件含三组关键内容：
  关系箭头 `}}o--||`、normalized types (`int`, `string`, `float`)、包含表/索引/外键区块。
- **Outcome:** 双输出管线（Markdown 文档带 Mermaid 图，干净、自包含、可在 GitHub 渲染）。

### Phase 3: CLI Interface & E2E Tests

- **Spec:** argparse CLI：`source` (positional), `-o/--output` (default SCHEMA.md),
  `--title` (default = source stem) + понятное stderr на отсутствие source.
- **Acceptance:** 
  - 无源文件时 exit code != 0;
  - 成功路径输出 stdout: `Tables found: X` + `Foreign keys found: Y`;
  - 为每个交互点生成 subprocess E2E 测试 (`tests/test_cli.py` 3 теста)。
- **Outcome:** 用户可 `python -m schema2doc examples/ecommerce.db -o SCHEMA.md`
  — одна команда, результат сразу inspectable.

---

## Reliability Metrics

| Metric | Value |
|---|---|
| Automated tests | 12 (0 external packages — `unittest` stdlib) |
| External runtime dependencies | 0 (`sqlite3`, `dataclasses`, `argparse`) |
| Modular structure | 顶级文件: models, inspectors/, generators/, cli, __main__ + tests |
| Test coverage hits | 5/5 (inspector), 4/4 (generators), 3/3 (CLI) |
| Zero regression risk | 所有测试针对生成的真实输出做正则/内容断言，非空字符串断言 |

---

## Lessons Learned

1. **АТЕСТ:首个测试方向即采集层**，在写任何代码前先建一遍 PRAGMA API，避免出现乱签和类型映射错误（如 nullable 误判）。
2. **RENDERER 只是 GLUE**，不读数据库，不解析 SQL；否则换一种数据库或改方言就需重写渲染。
3. **MVVM 模式跨层** — Inspector 写 DTO → Generator 读 DTO，干净分离；新增 Renderer 不动其它层。
4. **EXIT CODING: `unittest discover -s tests -v`** — 端到端验证所有分支，包括缺失文件路径。
5. **TYPE FINAL: 避免内联于 f-string 变量名解析** — 测试显示 `key.name` / `pk` / `f"{x}"` 等常出现 f-string 反引号歧义，写成独立方法更安全。
