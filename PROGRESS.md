# 项目进度记录

> 更新日期：2026-09-20

## 项目状态总览

**个人 AI 助手**桌面应用：PySide6 + qasync + aiosqlite，约 8300 行 Python。

| 模块 | 状态 | 说明 |
|---|---|---|
| AI 对话 | ✅ 完成 | 8 家 Provider（OpenAI 兼容族 + Anthropic/Gemini 原生 API），真·流式输出 |
| 联网搜索 | ✅ 完成 | DuckDuckGo + trafilatura 正文抽取 |
| 本地搜索 | ✅ 完成 | FTS5 + 中文 LIKE 回退，特殊字符安全 |
| 文档处理 | ✅ 完成 | PDF/DOCX/TXT/MD/HTML 解析 + 分层摘要，解析不阻塞 UI |
| 日记 / 知识库 | ✅ 完成 | 心情/标签/分类 + 全文搜索 |
| QQ 监控 | ✅ 完成 | NapCat OneBot 11，轮询守护线程 |
| 微信监控 | ⚠️ 可选依赖 | 需安装 wechatauto-replica（当前未装，优雅降级） |
| 备份恢复 | ✅ 完成 | VACUUM INTO 一致性备份 + 恢复自动重连 + 密钥脱敏 |
| 主题 / 托盘 / 悬浮球 | ✅ 完成 | 明暗双主题，48px 悬浮球 |
| 测试 | ✅ 297 通过 | pytest，覆盖存储/搜索/AI 引擎/配置/工具/文档/布局/QQ 解析/图谱状态机/图谱 UI |

## 2026-09-11 修复记录（本轮）

### 高危
- **悬浮球崩溃**：`floating_ball.py` 补 `QPointF` 导入（原先每次重绘抛 NameError）。
- **设置保存丢配置**：`settings_panel._on_save` 改为保存**所有**云服务商的 key/model，不再只写当前选中者。
- **UI 线程阻塞**：文档面板 URL 抓取/PDF 解析、QQ 面板连接探测/群列表获取，全部移入 `run_in_executor`。

### 核心体验
- **真流式输出**：`engine.py` 三个 SSE 读取器（OpenAI/Anthropic/Gemini）每段增量文本实时 `response_token.emit()`。
- **中文搜索**：新增 `fts_escape`/`fts_like` 工具；FTS 命中为空自动回退 LIKE 子串扫描；FTS 特殊字符（`" - *`）转义，不再抛语法错误。
- **聊天历史截断**：仅发送最近 20 条历史给 API。
- **错误处理**：捕获 `asyncio.TimeoutError`（此前会以裸 TimeoutError 逃逸）；Gemini key 从 URL 查询串移至 `x-goog-api-key` 请求头。

### 数据可靠
- **备份数据库**：优先 SQLite `VACUUM INTO`（写入进行中也能得到一致副本），回退 copy2。
- **恢复数据库**：恢复前关闭连接、恢复后自动重连并重建表（修复 Windows 文件占用 + 旧连接问题）。
- **配置备份脱敏**：备份 yaml 中 api_key 写为 `__REDACTED__` 哨兵；恢复时自动回填当前生效的真实 key。
- **路径锚定**：数据库/备份默认路径锚定项目根目录（`Path(__file__)` 上溯），任意 CWD 启动不再数据分裂。
- **清理**：删除 `data/backups/` 下 6 个含泄漏 API key 的 settings 备份文件。

### 测试
- 填充空壳 `tests/test_ai_engine.py`（25 用例）与 `tests/test_chat_reader.py`（9 用例）。
- 修复 9 个历史失败用例：test_config 默认 provider 断言过期（openai→deepseek ×3）、test_storage 重复手动 FTS 插入（×6）。
- 根目录孤立脚本移至 `scripts/manual_wechat_reader_test.py`。
- 结果：**222 passed**（修复前基线 176 passed + 9 failed）。

## 遗留问题（低优先级，未处理）

- 全项目无 logging（5 处 print + 大量 `except: pass` 静默吞错）。
- 依赖清理：`markdown`/`pyperclip` 声明未使用；`duckduckgo-search` 已弃用（更名 `ddgs`）；pytest 应移入 dev 依赖组。
- 未使用导入若干（`application.py`、`main_window.py`、`engine.py` 的 `Qt` 等）。
- 托盘 QMenu 局部变量无引用可能被 GC；`create_task` 未保存引用。
- `search.max_results` 配置被硬编码忽略；窗口尺寸不持久化。
- QQ/微信轮询假设消息 ID 单调递增（NapCat 重启后可能漏消息）。
- 无 README、无 CI、无 lint 配置。
- 微信模块依赖可选库 wechatauto-replica，未实际验证。
- `.doc` 老格式实际 python-docx 不支持；TXT/MD 非 UTF-8（GBK）编码仍会解析失败。

## 安全待办

- [ ] **吊销泄漏的 DeepSeek API key**（`***REDACTED***...`，曾存在于 git 历史并已推送至 GitHub）。吊销后即使留在历史中也已失效。**此步只能由项目所有者在 DeepSeek 控制台操作，尚未完成；本地 `config/settings.yaml` 仍在使用该 key，吊销后请更换新 key。**
- [x] （可选）`git filter-repo` 清洗历史 + force-push —— 2026-09-13 完成：全部 8 个提交已重写脱敏（泄漏片段 → `***REDACTED***`）并强推 origin/main。重写前完整备份：`D:\project\Personal-Assistant-backup-before-rewrite.bundle`。注意 GitHub 服务器端旧提交短期内可能仍可通过旧 SHA 直链访问。
- [ ] 新 key 更新到 `config/settings.yaml`（已 gitignore，不会再入库）。

## 2026-09-20 知识图谱气泡可视化 G-P0

> 规划文档：`知识图谱气泡可视化规划书.md`。选中驱动的三级气泡图谱（0级绿=当前选中 / -1级红=上一步 / 1级蓝=关联知识），QGraphicsView 自绘，无新增重依赖。

- 新增 `src/graph/graph_state.py`：三级状态机（T1 检索进入 / T2 选中1级 / T3 回退 / T4 自选无操作 / T5 空关联 / T6 双击不改状态），剔除自身与回指、去重、不变量校验。
- 新增 `src/graph/graph_data.py`：1级判定（余弦相似度 ≥ 阈值，top-k 截断，float32 BLOB 解码）+ 离线关键词标签抽取（TF 兜底）。
- 新增 `src/ui/graph_panel.py`、`src/ui/widgets/graph_node.py`（悬停防抖 250ms / 单击选中 / 双击信号）、`graph_edge.py`（半透明连线，相似度映射不透明度）。
- `main_window` 注册图谱面板并注入 DAO；`icons.py` NAV_ICONS 新增"图谱"入口。
- 配置：`ai.graph`（level1_top_k=8 / similarity_threshold=0.35 / hover_debounce_ms=250）。
- 测试：test_graph_state.py（15）+ test_graph_data.py（12）；全量回归 293 passed / 0 failed。
- 顺带修复：icons.py 补 QRectF 导入与 "graph" 图标映射。

## 2026-09-20 UI 重构 U-P0：正确性修复

> 依据《UI面板重构规划书》U-P0 阶段实施，行为不变。全量回归 297 passed / 0 failed。

- **统一日志**：新增 `src/ui/logging.py`（logger "ui"）；graph_panel / chat_panel / main_window 的 print 输出改为 logger.warning。
- **任务引用管理**：新增 `src/ui/tasks.py`（spawn_ui，强引用+完成自清理）；9 个 UI 文件的 asyncio.ensure_future 全部替换，消除 fire-and-forget 任务被 GC 回收的风险。
- **托盘菜单 GC 修复**：application.py 托盘 QMenu 由局部变量改为成员引用 `self._tray_menu`。
- 全量回归 **297 passed / 0 failed**。

## 2026-09-20 隐患审计与修复（图谱 UI + 检索链）

> 针对新增 G-P0 图谱模块与 P0–P2 检索链的专项审计，共确认 2 项崩溃级 + 3 项功能缺失 + 4 项性能/健壮性隐患，全部修复。提交 `46ccbd1`。

- **崩溃级**：`graph_node.py` GraphNodeItem 原继承 QGraphicsEllipseItem（非 QObject），Signal/QTimer 构造即 TypeError——图谱渲染任何节点即崩；改用 QGraphicsObject 并手绘 paint/boundingRect/shape，同时补上遗漏的 Qt 导入。
- **功能接线**：`main_window` 连接 node_double_clicked → 定位来源内容（知识面板 focus_content 展示）；`knowledge_panel` 搜索卡片新增「在图谱中探索」按钮 → graph_enter_requested → enter_from_search，补齐 T1 进入与 T6 双击导航两条链路。
- **防重入**：`graph_panel` 节点激活协程加合并机制，快速扫过多个节点只执行最新一次重建，不再排队竞争。
- **性能**：`dao` 新增 get_chunk / get_document 主键点查；`graph_data.get_node` 由全表扫描改为点查。
- **数据可靠**：`vector_search.index_text` 先分块后插文档，空文本不再留下孤儿 document；`backfill` 以 deduped 字段判定去重，0-chunk 计入 failed 而非 deduped。
- **可观测**：`hybrid_search` 检索失败输出日志，不再静默吞异常。
- **测试**：新增 tests/test_graph_ui.py（4 例：节点构造+信号 / set_level / rebuild / 防重入合并）；全量回归 **297 passed / 0 failed**。

## 2026-09-18 向量检索与知识库改造（P0–P2）

> 方案文档：`向量检索与知识库改造方案.md`。技术路线：sqlite-vec 向量检索 + FTS5 关键词检索 + RRF 混合融合 + RAG 注入对话。Embedding 默认 hashing 离线后端（零依赖、可运行），可切换 local(bge) / ollama / OpenAI 兼容。

### P0 向量化最小闭环
- 新增 `src/ai/embedding.py`：Embedding 抽象与工厂（Hashing 离线默认 / LocalBge / Ollama / OpenAI 兼容）。
- 新增 `src/search/vector_search.py`：VectorStore，index_text / index_knowledge_item / search；sqlite-vec 优先，纯 Python cosine 兜底。
- `storage/database.py`：新增 documents / chunks / chunks_fts / vec_chunks 表（IF NOT EXISTS），vec_enabled 探测。
- `storage/dao.py`：insert_document / insert_chunks（同步写 FTS + 向量）/ delete_document / search_chunks_fts。
- `document/chunker.py`：新增 SemanticChunker（CJK≈1 token/字，默认 400/60 重叠）。
- `app/config.py` + `config/settings.yaml`：ai.embedding.* 配置段。
- `ui/knowledge_panel.py`：保存时向量化入库；搜索优先语义、失败回退关键词。
- 测试：tests/test_embedding.py（11）+ tests/test_vector_search.py（17）。

### P1 存量回填 + 文档入库接线
- 新增 `src/search/backfill.py`：backfill_knowledge / backfill_diaries / backfill_all（幂等、进度回调）。
- `ui/document_panel.py`：解析后自动 index_text；「存入知识库」按钮；set_vector_store。
- `ui/main_window.py`：set_dao 内构建共享 VectorStore 注入 knowledge/document 面板。
- `main.py`：run_backfill() 启动装配，受 ai.embedding.backfill_on_startup 控制（默认关）。
- 测试：tests/test_backfill.py（7）。

### P2 混合检索 + RAG 注入对话
- 新增 `src/search/hybrid_search.py`：rrf_fuse + HybridSearcher.search / build_context（FTS5 关键词 + 向量双通道，RRF 融合）。
- `ai/prompts/__init__.py`：RAG_PROMPT_TEMPLATE + build_system_prompt(context) + build_chat_messages(context=)。
- `ui/chat_panel.py`：set_vector_store + _dispatch（发送前召回→注入 system prompt），回复携带来源列表。
- `ui/widgets/message_bubble.py`：assistant 气泡新增「📎 引用来源」块。
- `ui/main_window.py`：注入 chat_panel.set_vector_store。
- 配置：ai.embedding.rag_enabled=true / rag_top_k=5。
- 测试：tests/test_hybrid_search.py（13 用例）。

### 测试基线
- P0+P1 新测试 34 passed；全量套件 254 passed / 2 failed（test_search 缺 trafilatura，属既有环境依赖缺失，非本次回归）。
- 注：P2 用例逻辑经等价副本独立验证通过；因本地挂载目录间歇 I/O 故障，未能在该环境内直接实跑全量套件，请在正常环境执行 `pytest tests/` 复核。

### 其他
- 依赖：pyproject.toml 新增 sqlite-vec / numpy；移除未使用的 litellm。

## 2026-09-20 U-P1 收尾（完成）
- 删除 chat_reader_panel.py / settings_panel.py 中残留的 ThemeManager.register_panel(self)，主题注册统一收口到 src/ui/base_panel.py 的 ThemedPanel/ThemedMainWindow
- 完整性核验：compileall 通过；register_panel 仅存在于 base_panel.py；7 个面板继承 ThemedPanel（document_panel 保持 QWidget 为例外）
- 全量回归：297 passed（pytest 9.1.1 + PySide6, QT_QPA_PLATFORM=offscreen）
