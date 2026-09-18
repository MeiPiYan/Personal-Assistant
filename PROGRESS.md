# 项目进度记录

> 更新日期：2026-09-18

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
| 测试 | ✅ 222 通过 | pytest，覆盖存储/搜索/AI 引擎/配置/工具/文档/布局/QQ 解析 |

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
