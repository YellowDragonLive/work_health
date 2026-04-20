# 久坐健康助手 — 架构设计文档

> **项目名称**: Work Health (久坐健康助手)  
> **平台**: Windows 桌面端 (Python + Tkinter + pystray)  
> **最后更新**: 2026-04-20 (v1.7)  

---

## 1. 项目概述

**久坐健康助手** 是一款 Windows 系统托盘常驻应用，核心功能是 **Pomodoro 式工作-休息计时器**，同时融合了 **每日生理健康指标追踪** 和 **Dan Koe "人生游戏"自省问答系统**。

### 1.1 核心价值主张

| 维度 | 功能 |
|------|------|
| 🧘 **身体健康** | 周期性强制休息提醒，防止久坐损伤 |
| 📊 **数据追踪** | 体重、血压、心率等生理指标的每日累计记录 |
| 💭 **心理自省** | 基于 Dan Koe "人生重启协议"的三阶段自省问答 |
| 🎮 **游戏化** | "人生游戏面板"将长期目标拆解为可操作的六组件系统 |

---

## 2. 系统架构总览 (System Architecture)

```mermaid
graph TB
    subgraph "主线程 (GUI Thread - Tkinter)"
        TK_ROOT["Tkinter Root<br/>隐藏根窗口/生命周期管理"]
        GUI_QUEUE["gui_queue<br/>多线程安全任务队列"]
        VIEW["view.py<br/>UI 入口总线"]
        WINDOW["window.py<br/>ReminderWindow<br/>三栏布局调度中心"]
        UI_L["ui_left.py<br/>人生游戏提示面板"]
        UI_R["ui_right.py<br/>生理指标录入面板"]
        THEME["theme.py<br/>视觉令牌/Token"]
        
        WINDOW --- UI_L
        WINDOW --- UI_R
        WINDOW --- THEME
    end
    
    subgraph "核心后台线程 (Logic Thread - Monitor)"
        MONITOR["monitor.py<br/>FSM 状态机控制器"]
        DETECTOR["Activity Detector<br/>系统锁定/空闲感应"]
        AUDITOR["Profile Auditor<br/>动态策略实时巡检"]
        
        MONITOR --> DETECTOR
        MONITOR --> AUDITOR
    end
    
    subgraph "外围子系统 (Services)"
        TRAY["pystray<br/>系统托盘 & 快捷操作"]
        AUDIO["audio.py<br/>AudioManager<br/>多阶段背景音控制"]
    end
    
    subgraph "持久化层 (Persistence)"
        CONFIG["config.json<br/>单源事实模式配置"]
        STORAGE["JSON Data<br/>health/journal"]
    end

    %% 交互链路
    TRAY -- "菜单指令" --> GUI_QUEUE
    MONITOR -- "UI 唤起/销毁请求" --> GUI_QUEUE
    GUI_QUEUE -- "主循环消费" --> VIEW
    VIEW -- "挂载/卸载" --> WINDOW
    MONITOR -- "状态回调" --> AUDIO
    WINDOW -- "数据持久化" --> STORAGE
    AUDITOR -- "热加载" --> CONFIG
    CONFIG -- "驱动策略" --> MONITOR
```

---

## 3. 核心逻辑状态机 (State Machine Lifecycle)

系统核心由 `monitor.py` 驱动的状态机控制，结合了 **动态时长巡检** 和 **生理感测隔离**。

```mermaid
stateDiagram-v2
    [*] --> WORK_INIT: 应用启动
    
    state WORK_INIT {
        [*] --> Checking: 加载当前时间 Profile
        Checking --> Running: 启动工作倒计时
    }

    state WORK_PHASE {
        Running: 正常计时中
        Idle_Paused: 已感应到空闲/锁定 (暂停)
        Running --> Idle_Paused: 系统锁定或 3min 无操作
        Idle_Paused --> Running: 用户回归
    }
    
    WORK_INIT --> WORK_PHASE
    
    WORK_PHASE --> PROMPT: 工作时长达到 Profile 阈值
    
    state PROMPT {
        [*] --> Waiting: 悬浮窗/通知提醒
        Waiting --> SNOOZE: 用户点击"稍后"
        Waiting --> BREAK: 用户点击"开始休息"
        Waiting --> BREAK: 30s 无操作自动进入休息
    }
    
    SNOOZE --> WORK_PHASE: 延时结束后回归
    
    state BREAK_PHASE {
        Countdown: 身体活动/饮水 (提醒音乐)
        Reflection: 深度自省/录入 (反思音乐)
        
        [*] --> Countdown
        Countdown --> Reflection: 倒计时结束
        Reflection --> Done: 提交数据并关闭
    }
    
    BREAK_PHASE --> WORK_INIT: `done_event` 触发
```

---

## 4. 核心组件说明 (Core Components)

- **`main.py`**: 应用程序入口，管理线程初始化与单例锁。
- **`monitor.py`**: 核心逻辑引擎，处理计时、状态切换与系统活动检测。
- **`view.py`**: UI 入口，协调窗口的显示与关闭。
- **`window.py`**: 提醒窗口主框架，协调各子面板与中心交互业务流。
- **`ui_left.py`**: 左侧"人生游戏"提示面板组件。
- **`ui_right.py`**: 右侧"生理指标"录入面板组件。
- **`theme.py`**: UI 视觉令牌（颜色、字体）。
- **`components.py`**: 可复用的 UI 基础组件。
- **`audio.py`**: 音频播放控制器，支持多轨道切换（提醒音 vs. 反思音）。
- **`questions.py`**: 自省问题库与金句库。
- **`config_manager.py`**: 数据持久化处理。
- **`utils.py`**: Windows 专用工具函数。

---

## 4. 模块职责 (Module Responsibilities)

### 4.1 `main.py` (The Orchestrator)
- **线程管理**: 启动 Monitor 和 Tray 线程。
- **消息路由**: 监听 `gui_queue` 并根据消息类型调用 `view.py` 中的渲染函数，确保所有 GUI 操作均在主线程执行。

### 4.2 `monitor.py` (The Engine)
- **状态管理**: 维护 `WORK`, `PROMPT`, `BREAK`, `SNOOZE` 状态。
- **活动检测**: 自动感应用户离开（锁定或空闲）并暂停计时。
- **动态策略 (Profile Auditing)**: 每次状态切换前自动巡检时间，根据 `config.json` 匹配当前模式（如晨间模式 10/5）。
- **时间解耦**: 支持 `virtual_time` 注入，实现无损的时间模拟测试。
- **多音轨调度**: 根据状态切换背景音乐。在 `PROMPT/BREAK` 播放提醒曲目，在进入 `Reflection` (回答) 阶段时精确切换到反思曲目。

### 4.3 `window.py` & `view.py` (The Interface)
- **调度中心**: `view.py` 负责线程隔离；`window.py` 负责全屏窗口的实例化与三栏布局编排。
- **子面板协作**: `window.py` 在休息开始时实例化 `ui_left.py` 和 `ui_right.py`。
- **交互逻辑**: 中栏的问题展示与多行文本回答逻辑保留在 `window.py` 中。

---

## 5. 模块详解 (核心 UI 拆分版)

### 5.1 布局总线 — `window.py`
**职责**: 负责 Toplevel 窗口属性管理、背景遮罩、主计时器 (`after`)、中心区域 (Question/Answer) 状态切换以及最终数据的持久化拦截（调用 `ui_right` 获取输入值）。

### 5.2 左侧栏 — `ui_left.py` (Life Game Panel)
**职责**: 独立封装"人生游戏六组件"的展示逻辑。自动从 `questions.py` 获取最新回答，并处理 `placeholder` (灰色未填写态) 与随机金句展示。

### 5.3 右侧栏 — `ui_right.py` (Health Panel)
**职责**: 封装生理指标录入表单。内置 `placeholder` 刷新逻辑（自动查找历史记录）与 `dirty` 状态追踪。提供 `get_real_values()` 供主窗口在提交时调用。

### 5.4 视觉系统 — `theme.py` & `components.py`
**职责**: 定义项目的设计规范，提供 `_C` (Color)、`_F` (Font) 以及 `_CircleTimer` 等原子化组件。

---

## 6. 数据流 (Data Flow)

### 6.1 休息数据保存逻辑
1. 用户在 `ui_right.py` 表单中修改健康数值。
2. 用户在 `window.py` 的中栏完成思考后点击“提交”。
3. `window.py` 调用 `ui_right.get_real_values()` 提取数据。
4. `window.py` 整合两者数据并调用 `config_manager` 写入磁盘。
5. 向后台发送 `done_event`，唤醒 `monitor.py` 回到工作状态。

---

## 7. 文件结构

```
work_health/
├── src/                              # 源码目录
│   ├── main.py                       # 入口 · 编排 · 托盘
│   ├── monitor.py                    # 状态机 · 计时 · 活动检测
│   ├── view.py                       # UI 入口 · 生命周期
│   ├── window.py                     # 核心布局 · 三栏调度器
│   ├── ui_left.py                    # 子组件: 左侧提示面板
│   ├── ui_right.py                   # 子组件: 右侧健康面板
│   ├── theme.py                      # 视觉令牌 (颜色/字体)
│   ├── components.py                 # UI 基础组件 (CircleTimer/按钮)
│   ├── questions.py                  # 自省问题库 (33题 + 6组件 + 金句)
│   ├── config_manager.py             # JSON 读写 (config/health/journal)
│   ├── audio.py                      # pygame 音频管理
│   ├── utils.py                      # Windows 工具 (隐藏控制台/自启动)
│   ├── config.json                   # 用户偏好 [.gitignore]
│   ├── health_data.json              # 健康数据 [.gitignore]
│   ├── journal_data.json             # 自省记录 [.gitignore]
│   └── assets/
│       ├── icon.png                  # 托盘图标
│       ├── article.md                # 核心协议参考 (英)
│       ├── article_zh.md              # 核心协议参考 (中)
│       └── default_music.wav         # 默认提示音
```

---

## 8. 演进记录

- **v1.0 - v1.5**: 基础架构实现、场景音乐引入与配置解耦。
- **v1.6**: **视觉规格大革命 (Dashboard Era)**。全屏矩阵布局、三栏指挥塔分工、Modern Card 感官重塑。
- **v1.7**: **工程鲁棒性与可观测性增强**。
    - **音频路径自愈 (Auto-Healing)**: 自动将无效的相对路径纠正为绝对路径，应对多级目录运行环境（如根目录 vs src 目录）。
    - **日志系统标准化 (Unified Logging)**: 全项目禁绝 `print`，统一接入 `logging` 模块并持久化至 `app.log`，强化后台运行的可追溯性。
    - **单例锁与编码优化**: 强制采用 UTF-8 编码读取持久化数据，避免 Windows 环境下的乱码风险。

---

## 9. 特色布局：全屏可视化矩阵 (Fullscreen Matrix)

系统在 v1.6 引入了基于全屏比例的布局逻辑：

| 区域 | 宽度规格 | 核心职责 | 视觉表现 |
|------|----------|----------|----------|
| **左侧面板** | `450px` (固定) | 人生游戏系统 6 组件 | 超宽展示，支持长文本阅读 |
| **中心舞台** | `Expand` (动态) | 计时器/深度自省/输入 | 文字包裹收紧至 `650-700px` 焦点区 |
| **右侧面板** | `420px` (固定) | 生理健康指标监控 | 宽阔的录入区域，仪表盘视觉 |

**设计理念**: 模拟高端驾驶舱视觉，两翼提供全量背景信息流，中心提供任务相关的精确深度交互。

---

## 10. 特色功能：多阶段场景音乐 (Scenario Audio)

系统通过 `audio.py` 实现了基于状态的背景音乐切换，增强了心理暗示的区分度：

| 阶段 | 状态 | 音乐类型 | 功能描述 |
|------|------|----------|----------|
| **提醒阶段** | `PROMPT` | 提醒歌曲 (A) | 唤回用户注意力，提示准备休息 |
| **休息阶段** | `BREAK` | 提醒歌曲 (A) | 延续提醒氛围，进行倒计时身体活动 |
| **反思阶段** | `ANSWER_INPUT` | 反思歌曲 (B) | 切换至专注/宁静旋律，引导深度思考录入 |

**实现机制**: `Monitor` 作为调度者，通过回调函数机制监听 `ReminderWindow` 的 UI 事件。当 UI 进度从倒计时转入回答框展示时，触发 `on_reflection_start` 回调，完成音轨的热切换。

---

## 11. 工程鲁棒性保证 (Engineering Robustness)

### 11.1 路径自愈机制 (Audio Path Self-Healing)
由于 Windows 环境下工作目录 (CWD) 的不确定性，系统在启动初期会进行“路径审计”：
1. 检测 `config.json` 中的音频路径是否真实存在。
2. 若失效，则尝试以项目根目录为基准重新定位同名文件。
3. 将最终定位到的**物理绝对路径**持久化回配置，确保后续状态机调度 100% 成功。

### 11.2 可观测性体系 (Observability)
系统完全弃用 `print`，所有模块均通过 `logging` 与主进程同步。日志文件 `app.log` 具备以下特征：
- **UTF-8 编码**: 完美记录包含中日文符号的音频路径。
- **逐秒同步**: 实时监控 Monitor 线程的心跳与 UI 事件队列。
- **精细化分级**: 覆盖资产加载、音频调度、UI 生命周期全过程。
