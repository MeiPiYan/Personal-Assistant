# UI 面板重构规划书

> 版本：v1.0
> 日期：2026-09-20
> 范围：`src/ui/**` 全部面板与控件（19 个文件 / 5149 行）
> 硬约束：**现有功能与用户可见行为保持不变**，纯结构 / 质量重构（不引入新特性、不改交互、不改视觉设计）

---

## 一、背景与动机

项目在完成 P0–P2（向量知识库）与 G-P0（知识图谱）两个迭代后，UI 层已累积到 **19 个文件、5149 行**。功能层面完整可用（全量回归 **297 passed / 0 failed**），但结构层面出现了多处可量化的问题，会持续放大后续每个迭代的改动成本与回归风险：

| 维度 | 现状 | 证据 |
|------|------|------|
| 主题重复 | 8 个面板各自手写 `_apply_theme()` + `ThemeManager.register_panel(self)` | grep：8 处定义 + 8 处注册调用 |
| 异步散落 | 35 处 `run_in_executor` / `ensure_future` / `create_task` 分散在 6 个面板 | grep 统计 |
| 超大文件 | `settings_panel.py` 816 行单一类；`styles.py` 1043 行 | wc -l |
| 日志缺失 | 异常用 `print` + 裸 `except: pass`，故障现场不可观测 | PROGRESS 遗留 + 源码 |
| 任务泄漏 | `create_task` 未保存引用；托盘 QMenu 局部变量有 GC 风险 | PROGRESS 遗留 |
| 状态丢失 | 窗口尺寸 / 分栏比例不持久化；`search.max_results` 配置未被消费 | PROGRESS 遗留 |

因此需要一轮**以"不改行为"为硬约束**的结构重构。

---

## 二、现状盘点

### 2.1 文件清单与规模

| 文件 | 行数 | 职责 | 备注 |
|------|------|------|------|
| styles.py | 1043 | 主题中心（ThemeColors + ThemeManager）+ 全局样式表 | 结构良好，作为基准 |
| settings_panel.py | 816 | 设置面板（AI 模型 / 向量库 / 图谱等多配置区块） | ⚠️ 最大单文件 |
| chat_reader_panel.py | 399 | 微信 / QQ 消息监控 | |
| knowledge_panel.py | 390 | 知识浏览 / 搜索 / 保存卡片 | 已含 graph_enter_requested |
| search_panel.py | 388 | 跨源搜索 | |
| chat_panel.py | 355 | 对话 + 流式 + RAG 来源 | |
| diary_panel.py | 318 | 日记 | |
| icons.py | 315 | 自绘图标 + 托盘图标 | |
| main_window.py | 240 | 侧边栏 + QStackedWidget 装配 | |
| graph_panel.py | 225 | 图谱画布（QGraphicsView） | G-P0 新增 |
| document_panel.py | 197 | 文档解析 + URL 提取 + 摘要 | |
| floating_ball.py | 121 | 悬浮球 | |
| widgets/（5 件） | 342 | graph_node / graph_edge / message_bubble / streaming_text / file_drop | 已模块化 |
| **合计** | **5149** | | |

### 2.2 现有主题机制（保留并复用）

`styles.py` 已实现一套健康可用的主题中心：
- `ThemeColors`：冻结 dataclass，约 40 个语义色字段
- `ThemeManager`：`apply()` / `toggle()` / `register_panel()` / `_refresh_all_panels()` / `save_pref()`

机制本身无需改动，问题在**消费侧**：每个面板都重复"取色 → 拼样式串 → 注册"三步。

### 2.3 面板与主题耦合现状

8 个面板（main_window / knowledge / search / chat / diary / chat_reader / settings / graph）各自实现 `_apply_theme()`，模式完全一致：

```python
def _apply_theme(self) -> None:
    c = ThemeManager.get_colors()
    self._xxx.setStyleSheet(f"color: {c.text_tertiary}; font-size: 12px;")
    ...
```

这是典型的可抽取到基类的样板代码。

---

## 三、问题诊断（按严重度分级）

### P0 — 正确性 / 资源安全（必修）
1. **异步任务引用丢失**：多处 `asyncio.create_task(coro())` 未保存返回值，任务可能被 GC 提前回收（CPython 会警告 "Task was destroyed but it is pending"）。
2. **托盘菜单 GC 风险**：托盘 `QMenu` 作为局部变量创建，若未正确 setParent / 保留引用，可能被回收导致菜单闪退或行为异常。
3. **裸 `except: pass`**：吞掉所有异常，故障现场不可观测（与此前混合检索静默失败同因）。

### P1 — 结构 / 可维护性
4. **主题样板代码重复**：8 处 `_apply_theme` 手写，新增面板必复制粘贴；颜色字段名笔误只会在运行时暴露。
5. **异步调用无统一入口**：35 处三种写法混用（executor / ensure_future / create_task），无法统一做"面板销毁时取消任务""任务异常统一上报"。
6. **settings_panel 816 行单类**：AI 模型、向量库、图谱等多个互不相关的配置区块挤在一个类，改动任一块都要重读整文件。
7. **硬编码样式串**：83 处内联 `setStyleSheet` 含字号 / 间距 / 颜色字面量，与 ThemeColors 并存形成两套事实来源。

### P2 — 体验 / 一致性
8. **窗口几何不持久化**：尺寸、QSplitter 比例每次启动重置。
9. **`search.max_results` 配置被忽略**：UI 未消费该配置项。
10. **未使用导入**：若干文件残留 import，增加阅读噪音。

---

## 四、重构方案

### 总原则
- **行为不变**：所有用户可见交互、布局、信号、槽、公开方法签名保持不变。
- **测试先行**：每步重构前确认 / 补充覆盖该模块的测试，重构后全量回归必须保持 **≥ 297 passed**。
- **小步提交**：每个 U 阶段独立提交，可随时中断不影响主干可用性。

### U-P0：正确性修复（无结构改动）
> 目标：消除资源泄漏与静默失败，不动任何文件结构。

1. 引入统一日志 `src/ui/logging.py`（`logging.getLogger("ui")`），替换全部 `print` 与裸 `except: pass` 为 `logger.exception(...)`。
2. 所有 `create_task` 调用点保存任务引用到面板级 `_tasks: set`，面板 `closeEvent` / 销毁时统一 `cancel()`。
3. 托盘 `QMenu` 显式 `setParent(self)` 或保留成员引用。
4. 清理未使用导入（ruff / 人工核对）。

**验收**：297 passed 不回退；启动应用无 "Task was destroyed" 警告；托盘菜单稳定。

### U-P1：主题基类 + 异步管理器
> 目标：消除两类最大的重复模式。

1. 新增 `src/ui/base_panel.py`：

   ```python
   class ThemedPanel(QWidget):
       def __init__(self, app=None, parent=None):
           super().__init__(parent)
           ThemeManager.register_panel(self)

       def _apply_theme(self) -> None:  # 子类按需重写具体样式
           ...
   ```

   8 个面板改为继承 `ThemedPanel`，删除各自重复的注册调用；各自 `_apply_theme` 的具体样式逻辑原样保留（行为不变）。

2. 新增 `src/ui/task_runner.py`：

   ```python
   class UITaskRunner:
       def __init__(self, owner):
           self._owner, self._tasks = owner, set()

       def spawn(self, coro) -> asyncio.Task:
           ...

       def cancel_all(self) -> None:
           ...
   ```

   面板持有 `self.tasks = UITaskRunner(self)`，替换全部散落的 `ensure_future` / `create_task`。

**验收**：297 passed；主题切换对 8 个面板即时生效（人工走查）；新增基类与任务管理器单元测试。

### U-P2：设置面板拆分
> 目标：将 816 行单类拆为"容器 + 子页"。

- `settings_panel.py` 保留为容器（信号、保存入口、装配），按配置域拆出：
  - `settings/ai_models_section.py`（AI 模型）
  - `settings/vector_kb_section.py`（向量库）
  - `settings/graph_section.py`（图谱）
- 每个 section 为独立 QWidget 子类，容器负责组合与 `settings_saved` 转发。
- 对外公开接口（`settings_saved`、`load_*` 方法）保持签名不变。

**验收**：297 passed；设置面板各区块渲染与保存行为与重构前一致（截图对比）。

### U-P3：样式与状态收尾
1. 将高复用的内联样式串（标题 / 次级文本 / 卡片）沉淀为 `styles.py` 的 `section_header_style(c)` 等工厂函数，替换各面板硬编码字面量。
2. 窗口几何 + 主要 QSplitter 比例用 `QSettings` 持久化（启动恢复）。
3. UI 消费 `search.max_results` 配置。
4. （可选）`styles.py` 1043 行按"主题数据 / 主题管理 / 全局样式表"拆 3 模块，保持 `from .styles import ...` 兼容导入。

**验收**：297 passed；重启后窗口尺寸恢复；调整 `search.max_results` 后搜索结果数量随之变化。

---

## 五、分阶段实施与工作量

| 阶段 | 内容 | 预计改动文件 | 风险 | 依赖 |
|------|------|------------|------|------|
| U-P0 | 日志 / 任务引用 / 托盘菜单 / 导入清理 | 6–8 | 低 | 无 |
| U-P1 | ThemedPanel 基类 + UITaskRunner | 9–10 | 中 | U-P0 |
| U-P2 | settings_panel 拆分 | 3–4 | 中 | U-P1 |
| U-P3 | 样式工厂 / 几何持久化 / 配置消费 | 5–7 | 低 | U-P1 |

每个阶段结束跑一次全量回归 + 一次人工冒烟（启动 → 切换 7 个页面 → 主题切换 → 图谱交互）。

---

## 六、测试与验收

- **回归基线**：当前 297 passed / 0 failed，重构全程不得回退。
- **新增测试**：
  - U-P1：`ThemedPanel` 子类自动注册 / 注销测试；`UITaskRunner.cancel_all` 测试。
  - U-P2：设置面板 section 组合测试（容器能找到各 section）。
- **人工验收清单**（每阶段）：
  - [ ] 应用正常启动、7 个页面可切换
  - [ ] 明 / 暗主题切换即时生效且无残影
  - [ ] 图谱页悬停 / 双击行为正常
  - [ ] 设置保存后对话面板模型列表刷新
  - [ ] （U-P3 后）重启恢复窗口尺寸

---

## 七、风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 主题基类改动波及 8 面板 | 样式回归 | 逐面板迁移 + 迁移后即时人工走查；保留旧 `_apply_theme` 逻辑原样 |
| settings 拆分引入循环导入 | 启动失败 | 先拆数据 / 信号，再拆 UI；容器只做组合 |
| 任务取消误伤进行中操作 | 数据不完整 | `cancel_all` 仅在面板销毁时触发；保存类任务标记 `shield` |
| 挂载目录 I/O 不稳定 | git 提交失败 | 沿用"沙箱本地提交 + 对象校验回传"机制 |

---

## 八、不做清单（Out of Scope）

- 不引入新功能 / 新页面 / 新交互
- 不改变 ThemeColors 字段与 ThemeManager 公开 API
- 不重写 QSS 全局样式表的视觉设计
- 不动 `src/search`、`src/graph`、`src/ai` 等非 UI 模块
- 不升级 PySide6 版本

---

## 九、交付物

1. 《UI面板重构规划书.md》（本文档）
2. U-P0 ~ U-P3 各阶段代码改动 + 独立提交
3. 更新后的 PROGRESS.md 记录
4. 全程保持 ≥ 297 passed 的测试基线
