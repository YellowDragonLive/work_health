# 🧘 久坐健康助手 (Work Health) - 人生重启协议版

> **“如果你不为自己设定目标，你就会沦为别人达成目标的工具。” — Dan Koe**

一款深度融合 **Dan Koe “人生游戏”协议** 的 Windows 桌面助手。它不仅是一个极简、强制的久坐提醒工具，更是一个旨在打断你的“自动驾驶模式” (Autopilot)、引导你进行深度心理自省与生理健康追踪的系统性助手。

---

## 💎 核心价值主张 (Our Philosophy)

基于 Dan Koe 的《如何用 1 天修复整个人生》，本项目通过强制性的物理中断，强迫用户跳出日常的无意识惯性（Conditioning），进入 **[人生重启协议]**：

1.  **打断自动驾驶 (Interrupt Autopilot)**：利用 25/5 或自定义的工作/休息循环，在休息期间通过深度自省问题，迫使你审视当前的身份保护行为。
2.  **构建反愿景 (Anti-Vision)**：通过不断询问“我正在逃避什么？”和“如果一切不改变，5年后我的样子？”，利用痛苦的推张力将你推向更好的生活。
3.  **人生游戏化 (The Life Game)**：内置“人生游戏面板”，将长期愿景（最终胜场）拆解为 1年任务（主线）、1月项目（BOSS战）和每日杠杆（日常任务）。

---

## 🌟 核心特性 (Features)

### 1. 强制性心理中断 (Psychological Interrupts)
- **深层提问系统**：休息触发时，系统会根据当前时间段（早晨、全天、晚间）随机挑选 Dan Koe 协议中的自省问题。
- **心理挖掘 (Morning Excavation)**：早晨侧重于挖掘不满与反愿景。
- **模式打断 (Daytime Interrupts)**：白天侧重于觉察逃避行为。
- **综合洞察 (Evening Synthesis)**：晚间侧重于总结、定义真理与设定明日杠杆。

### 2. 生理指标实时追踪 (Physiology Tracking)
- **闭环记录**：在休息结束前，引导用户记录体重、血压、心率等核心生理指标。
- **趋势积累**：所有数据按日期累计保存，为长期的身体健康提供数据支撑。

### 3. “人生游戏”长效面板
- **六组件视图**：在提醒界面左侧常驻显示你的反愿景、愿景、1年/1月目标及每日杠杆。
- **身份锚点**：不断用“那个你正在成为的人会怎么做？”来校准你的日常行为。

### 4. 纯净的 Windows 系统体验
- **Midnight Aurora 审美**：深邃、奢华的暗色调设计，致力于创造宁静的思考空间。
- **智能活动检测**：自动识别锁屏状态与长时间空闲，确保计时器真实反映你的工作状态。
- **全局媒体联动**：提醒触发时自动关闭浏览器视频/播放器，休息结束（可选）手动恢复。

---

## 🚀 快速开始 (Getting Started)

### 1. 安装要求
- Windows 10/11
- Miniconda / Anaconda（推荐）或 Python 3.10+
- 独立 conda 环境隔离依赖，避免污染全局 Python

### 2. 环境准备（首次安装）
```bash
# 创建独立 conda 环境（Python 3.10）
conda create -n work_health python=3.10

# 安装依赖（conda-forge 优先，DLL 兼容性更好）
conda install -n work_health -c conda-forge pystray pillow
conda install -n work_health -c conda-forge pygame
```

> **为什么用 conda env 而非全局 pip？**
> Windows 多 Python 共存时，`pip install` 可能落到 user site 导致 DLL 交叉加载崩溃。conda env 沙盒化依赖，彻底隔离。详见 [ARCHITECTURE.md](ARCHITECTURE.md) §9。

### 3. 初始化与运行
```bash
# 生成默认图标与提示音（仅需执行一次）
conda run -n work_health python generate_assets.py

# 启动程序（二选一）
#   方式 A：双击 bat（推荐，自动定位 env）
work_health_start.bat

#   方式 B：激活 env 后运行
conda activate work_health
python src/main.py
```

### 4. 开机自启
程序运行后，在系统托盘图标右键菜单点击 **"启用开机自启"**。注册表项将写入：
```
HKCU\Software\Microsoft\Windows\CurrentVersion\Run\HealthAssistant
  → "C:\Users\<用户名>\.conda\envs\work_health\pythonw.exe" "...\src\main.py"
```

> 自启动路径在 `src/utils.py` 的 `WORK_HEALTH_ENV_PYTHONW` 常量中硬编码为 work_health env 的 pythonw。如迁移 env 或换用户，需同步更新此常量。

### 5. 测试模式
如果想快速预览流程（1分钟工作，10秒休息），请直接运行：
```bash
run_test_mode.bat
```

> 测试模式默认使用 PATH 中的 python，需先 `conda activate work_health` 或确保全局 python 有依赖。

---

## 📖 设计系统 (Design System)

本项目遵循 **Midnight Aurora** 视觉规范：
- **VOID 背景**: 深邃的灰黑底色，减少视觉干扰。
- **琥珀金与青蓝强调**: 琥珀色代表警告/警示，青蓝色代表理智与进度。
- **环形倒计时**: 动态 Canvas 动画，实时反馈紧迫感。

---

## 📄 架构与协议 (Architecture)

详细的系统设计与调用链请参考 [ARCHITECTURE.md](ARCHITECTURE.md)。

> **注意**：本项目建议配合 Dan Koe 的文章（内置于 `src/assets/article.md`）共同阅读，以获得最佳的心理干预效果。

---
MIT License | 愿你在这个游戏中获得真正的智能。

