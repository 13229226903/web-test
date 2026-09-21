# 项目业务知识库

本目录是项目业务经验的检索层，不替代现有权威文件。

## 权威边界

- 测试执行硬规则、selector、截图、MCP、pytest / Allure 约束：`rule.md`、`artifacts/runtime/`、`skills/`
- 项目固定事实、账号、环境、素材：`PROJECT.md`
- 当前页面真实入口、状态、按钮、selector：`page_map/`
- 当前任务实际探索结果：`artifacts/<task_id>/sync.md`
- 当前任务确认用例：`artifacts/<task_id>/cases.md`
- 本目录：旧入口、业务规则、历史校验、权限差异、可复用业务坑点的结构化检索索引

知识库不得保存密码、验证码、Cookie、Token、API key 或其他敏感值；只能引用权威来源。

## 目录结构

```text
knowledge/
├── index.yaml                    # 检索目录，不放完整正文
├── shared.yaml                   # 跨模块业务知识
├── modules/                      # 按业务模块拆分
│   ├── seo-landing.yaml
│   └── <module>.yaml
├── candidates/pending.yaml       # 待确认经验候选
├── retired/retired.yaml          # 已废弃 / 被替代知识
├── schema/knowledge-slice.schema.yaml
└── README.md
```

模块较小时使用一个 `<module>.yaml`；单模块超过约 50 条知识、出现多个维护者或检索噪声明显时，再拆成 `entries.yaml`、`rules.yaml`、`validations.yaml`、`pitfalls.yaml`。

## 知识切片状态

- `active`：有证据，可作为默认检索结果
- `needs_verification`：可以作为探索候选，不能直接作为断言
- `conflict`：与需求、页面或其他权威来源冲突
- `superseded`：已被新知识替代
- `retired`：已废弃
- `ui_residue`：仅记录可见但不可操作的 UI 残留

默认检索只返回 `active` 与 `needs_verification`。

## 经验补充流程

1. 角色先在当前任务的 `sync.md`、`cases.md`、`impl.md` 或 `progress.log` 记录 `knowledge_candidate`。
2. `orchestrator` 在 `regression-archive gate` 汇总、去重并判断证据。
3. 同一经验出现至少 2 次，或单次但成本很高，才向用户提出沉淀确认。
4. 用户确认后，补入模块文件；未确认的经验留在 `candidates/pending.yaml`。
5. 写入后执行索引重建和校验：

```powershell
python scripts/knowledge.py validate
python scripts/knowledge.py rebuild-index
```

也可以先用命令生成待确认候选；该命令不会直接写入 `active`：

```powershell
python scripts/knowledge.py candidate-add `
  --knowledge-type validation_rule `
  --title "标题" `
  --subject-key "module.page.rule" `
  --summary "一句话经验" `
  --source-ref "artifacts/<task_id>/sync.md" `
  --evidence "当前任务实际验证结果"
```

## 后续新增知识的归档维度

正式知识按**当前项目的业务功能模块维度**归档，不按任务维度长期保存。

```text
正式知识：shared / module / page-feature-subject
临时经验：task artifact / candidates/pending.yaml
证据来源：task_id、sync.md、cases.md、回归结果
```

具体规则：

- 跨多个模块复用的业务规则放 `shared.yaml`，例如账号态、权限、环境顺序。
- 只属于一个功能模块的知识放 `modules/<module>.yaml`。
- 模块内通过稳定 `subject_key` 区分页面、功能、状态和规则，例如 `image_enhance.editor.upload_completed.validation`。
- 只属于某一个页面且不会跨任务复用的事实，优先留在对应 `page_map` 的 `notes`，不要进入通用知识库。
- 任务 ID 只作为候选来源、证据和验证记录，不作为正式知识目录。
- 同一主题跨任务再次出现时，更新原有 `knowledge_id` 的证据和 `last_verified_at`，不得按每个任务新建一条重复知识。
- 新版本规则替换旧规则时，创建新的 `knowledge_id`，复用同一 `subject_key`，先把旧条目标记为 `superseded`，并在 `supersedes` 中建立关系。
- 任务候选可以按任务维度临时记录，但用户确认后必须归并到模块或 shared 文件。

判断口诀：

> **任务是证据容器，模块是知识归档容器，subject_key 是稳定去重键。**

## 唯一权威和新增规则

每条正式切片必须明确 `source_of_truth`：

- `knowledge`：历史业务入口、业务校验、业务型历史坑点迁移后由知识库维护正文；
- `PROJECT.md`：账号、环境、素材和项目固定事实仍以 PROJECT.md 为准，知识库只保存检索摘要；
- `page_map`：当前 selector、按钮、状态和页面结构仍以当前版本 page_map 为准，知识库不得维护 selector 副本；
- `rule.md` / runtime / skill：测试硬规则和执行红线仍以原文件为准。

新增 `active` 切片必须同时具备：

1. 唯一 `knowledge_id` 和 `subject_key`；
2. 明确 `source_of_truth`；
3. 非空 `source_refs`；
4. 至少一条 `evidence`；
5. `last_verified_at`；
6. 结构化 `rule.given / when / then`；
7. 与现有 active / needs_verification 切片无重复主题，或明确 `supersedes` / `related_ids`。

经验候选只有在用户确认、证据满足沉淀条件并完成 `validate` 后，才能从 `candidates/pending.yaml` 生成正式切片；正式切片写入后必须执行 `rebuild-index`。

状态迁移只能按以下方向进行：

```text
needs_verification → active | conflict | retired
active             → conflict | superseded | retired
conflict            → active | superseded | retired
superseded / retired 不复活；如需恢复，创建新 knowledge_id 并通过 supersedes 关联旧条目。
```

同一 `subject_key` 不允许同时存在两个 `active` / `needs_verification` 切片；新版本必须先把旧版本改为 `superseded`，再重建索引。

## 检索流程

新业务任务不全量读取知识库。先查 `index.yaml`，再按任务的模块、页面、入口、状态、账号、环境和检索目的读取 Top-K 切片。

```powershell
# 初始化：最多返回 5 条
python scripts/knowledge.py search --mode init --module seo-landing --purpose entry --limit 5 --details

# MCP 探索运行时：最多返回 4 条
python scripts/knowledge.py search --mode runtime --module seo-landing --page landing --purpose validation --limit 4 --details

# 异常兜底：最多返回 3 条
python scripts/knowledge.py search --mode exception --query "入口未挂载 502" --purpose pitfall --limit 3 --details
```

检索脚本默认只读取索引；只有 `--details` 才读取命中的知识切片。每次检索都应记录命中、无命中或冲突状态，以及已消费的 `knowledge_id`。
