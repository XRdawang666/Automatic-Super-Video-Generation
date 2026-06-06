---
name: Automatic-Super-Video-Generation
description: 全自动视频/图片生成与剪辑。视频：深度思考 → 提示词优化 → 即梦生成 → video-use 自动剪辑。图片：深度思考 → 提示词优化 → 即梦生成 → 下载返回。全程用户只需描述想法。
---

# Auto Video — 全自动视频生成与剪辑

## 核心理念

用户只做两件事：**说想法** + **提剪辑要求**。其余全部自动化。

```
用户输入 → 深度思考 → 提示词优化 → 即梦生成 → 自动剪辑 → 交付成品
```

## 何时使用

**🎬 视频模式（完整流水线）：**
- 用户说「帮我做一个 X 的视频」
- 用户说「生成一个关于 X 的短片」
- 用户说「自动做一条 XX 类视频」

**🖼️ 图片模式（短流水线，到生成即止）：**
- 用户说「帮我生成一张 X 的图」
- 用户说「画一张 XX」
- 用户说「做一张 XX 风格的海报/插画/壁纸」

> 判断规则：用户提到"视频/短片/剪辑"走视频模式，提到"图片/图/照片/海报/插画/壁纸/画"走图片模式。

## 依赖清单

本 skill 是编排层，依赖以下组件。启动时自动检查，缺失则引导安装：

| 组件 | 用途 | 安装方式 |
|------|------|----------|
| `dreamina` CLI | 即梦视频生成引擎 | `curl -s https://jimeng.jianying.com/cli \| bash` |
| `video-use` skill | AI 视频剪辑 | 见下方「video-use 一键安装（含 Deepgram 替换）」 |
| `Deepgram API Key` | 视频转译（video-use 依赖） | 注册 https://console.deepgram.com → 写 Key 到 `~/Developer/video-use/.env` |
| `ffmpeg` | 音视频处理 | `winget install Gyan.FFmpeg` (Win) / `brew install ffmpeg` (Mac) |
| `superpowers` 插件 | 深度思考 brainstorming | `claude plugin install superpowers@claude-plugins-official` |

### video-use 一键安装（含 Deepgram 替换）

在**任何新电脑**上，不需要手动改 transcribe.py。直接执行：

```bash
# 1. 克隆 video-use
git clone https://github.com/browser-use/video-use ~/Developer/video-use
cd ~/Developer/video-use

# 2. 安装 Python 依赖
pip install -e .

# 3. 用 Deepgram 补丁替换 Scribe（本 skill 自带补丁）
cp ~/.claude/skills/Automatic-Super-Video-Generation/patches/transcribe.py ~/Developer/video-use/helpers/transcribe.py

# 4. 写入 Deepgram API Key
printf 'DEEPGRAM_API_KEY=<你的key>\n' > ~/Developer/video-use/.env

# 5. 注册 skill
ln -sfn ~/Developer/video-use ~/.claude/skills/video-use
```

补丁 `patches/transcribe.py` 与本 skill 一起分发。你要做的就是拿到 Deepgram Key 替换 `<你的key>`，其他全自动。

## 环境自检（每次启动时执行）

**在执行任何生成/剪辑操作之前，必须先跑一遍自检：**

```bash
# 1. dreamina CLI
which dreamina && dreamina user_credit --help >/dev/null 2>&1 && echo "✅ dreamina" || echo "❌ dreamina 未安装，运行: curl -s https://jimeng.jianying.com/cli | bash"

# 2. video-use skill + Deepgram 补丁
if [ -f ~/.claude/skills/video-use/SKILL.md ]; then
  if grep -q "Deepgram" ~/Developer/video-use/helpers/transcribe.py 2>/dev/null; then
    echo "✅ video-use (已打 Deepgram 补丁)"
  else
    echo "⚠️ video-use 需要打 Deepgram 补丁，执行: cp ~/.claude/skills/Automatic-Super-Video-Generation/patches/transcribe.py ~/Developer/video-use/helpers/transcribe.py"
    cp ~/.claude/skills/Automatic-Super-Video-Generation/patches/transcribe.py ~/Developer/video-use/helpers/transcribe.py && echo "   ✅ 已自动打补丁"
  fi
else
  echo "❌ video-use 未安装，一键安装命令见上方「video-use 一键安装」"
fi

# 3. Deepgram Key
grep -q '^DEEPGRAM_API_KEY=..' ~/Developer/video-use/.env 2>/dev/null && echo "✅ Deepgram" || echo "❌ Deepgram Key 未配置，去 https://console.deepgram.com 注册"

# 4. ffmpeg
ffmpeg -version >/dev/null 2>&1 && echo "✅ ffmpeg" || echo "❌ ffmpeg 未安装"
```

如果任一检查失败，**暂停**，告诉用户缺少什么 + 安装命令，不要继续。

## 完整流水线

### 阶段 0：接收输入

从用户那里收集两样东西：

1. **视频创意** — 主题、内容、风格、想要表达什么
2. **剪辑要求** — 时长、节奏、字幕风格、配乐需求、调色偏好

如果用户只给了创意没给剪辑要求，先用合理默认值（60秒、快节奏、bold-overlay字幕、warm_cinematic调色），生成后让用户提修改。

### 阶段 1：AI 引擎选择 + 深度思考 + 提示词优化

这是整个流水线最关键的环节。提示词质量直接决定视频质量。

**步骤 1.0 — 确认 AI 提示词引擎（启动时首先执行）**

你需要一个 AI 来生成高质量提示词。按以下优先级选择：

```
优先级 1：当前运行的 AI（DeepSeek/Claude）— 直接使用，无需任何配置
优先级 2：OpenAI API（GPT-4o/GPT-4）— 需要用户提供 OPENAI_API_KEY
优先级 3：Groq Cloud API（免费）— 需要用户提供 GROQ_API_KEY
优先级 4：Google Gemini API — 需要用户提供 GEMINI_API_KEY
优先级 5：本地 Ollama — 需要用户已安装并运行 ollama serve
优先级 6：纯模板模式 — 不依赖外部 AI，用规则模板生成基础提示词（质量最低，但零依赖）
```

**选择流程：**

```bash
# 检查环境变量
[ -n "$OPENAI_API_KEY" ] && echo "OpenAI 可用" || echo "OpenAI 不可用"
[ -n "$GROQ_API_KEY" ] && echo "Groq 可用" || echo "Groq 不可用"  
[ -n "$GEMINI_API_KEY" ] && echo "Gemini 可用" || echo "Gemini 不可用"
curl -s http://localhost:11434/api/tags >/dev/null 2>&1 && echo "Ollama 可用" || echo "Ollama 不可用"
```

如果除了当前运行的 AI 之外还有其他可用引擎，告诉用户有哪些选择，让用户决定用哪个。如果只有当前 AI 可用，直接用。

**向用户询问的模板：**

> 我检测到以下可用的 AI 提示词引擎：
> - ✅ 当前 AI（我）
> - ✅ OpenAI GPT-4o
> - ❌ Groq（未配置）
> 
> 默认用我来生成提示词就行。如果你想用 OpenAI 获得不同风格，告诉我。

**如果所有外部 AI 都不可用且当前 AI 也无法胜任：** 降级到纯模板模式（步骤 1.3-Alt）。

**步骤 1.1 — 理解需求**

用中文与用户深入交流，至少覆盖这些维度：

| 维度 | 要搞清楚的事情 |
|---|---|
| **主题与内容** | 讲什么故事？核心信息是什么？ |
| **目标受众** | 给谁看的？平台是哪里（抖音/B站/YouTube）？ |
| **视觉风格** | 写实/动漫/赛博朋克/极简/电影感/复古？ |
| **色调与氛围** | 暖色调/冷色调/高饱和/低饱和/电影调色？ |
| **节奏与情绪** | 快节奏燃向/舒缓治愈/紧张悬疑/温馨感人？ |
| **画幅比例** | 9:16竖屏 / 16:9横屏 / 1:1正方形？ |
| **时长** | 目标成片多长？ |

**步骤 1.2 — 拆解场景**

将一个完整视频拆解为多个场景（segments）。每个场景 = 一个即梦 text2video 调用。

场景拆解原则：
- 每个场景 4-8 秒（即梦单次生成最佳范围）
- 场景之间要有视觉变化（景别、角度、色调的对比）
- 遵循经典叙事结构：**开场钩子 → 展开 → 高潮 → 收尾**
- 例：60秒视频 ≈ 8-12个场景

输出场景列表格式：
```
场景1 [0-5s] 开场钩子：XXX — 镜头描述：XXX
场景2 [5-10s] 问题展示：XXX — 镜头描述：XXX
场景3 [10-18s] 解决方案：XXX — 镜头描述：XXX
...
```

**步骤 1.3 — 生成即梦提示词**

为每个场景生成极其详细的 English prompt（即梦 Seedance 模型对英文响应更好）。

提示词公式（Seedance 优化版）：

```
[Shot type] + [Subject & action] + [Lighting] + [Color palette] + [Camera movement] + [Mood & atmosphere] + [Quality keywords]

Shot type: Cinematic wide shot / Medium close-up / Extreme close-up / Tracking shot / Aerial drone shot / Dutch angle
Subject & action: 精确描述主体和动作，越具体越好
Lighting: Golden hour backlight / Soft diffused studio light / Neon noir / Natural window light / Volumetric fog light
Color palette: Warm amber and teal / Muted pastels / High contrast monochrome / Vibrant saturated
Camera movement: Slow push-in / Smooth dolly right / Static locked-off / Handheld subtle shake / Crane up
Mood & atmosphere: Dreamy and ethereal / Gritty and raw / Polished and commercial / Intimate and warm
Quality keywords: 8K, cinematic, photorealistic, shallow depth of field, anamorphic lens, film grain
```

每个场景的 prompt 至少 50 个词，越详细越好。同时记录中文描述供后续剪辑参考。

**步骤 1.3-Alt — 纯模板模式（当没有 AI 引擎可用时）**

如果所有 AI 引擎都不可用，降级到此模式。用规则模板将用户需求拼接成基础英文 prompt：

```python
# 视频模板
TEMPLATES = {
    "cinematic": "Cinematic wide shot, {subject}, {action}, {lighting}, {color} color palette, smooth camera movement, {mood} atmosphere, 8K, photorealistic, shallow depth of field, film grain",
    "anime": "Anime style, {subject}, {action}, {lighting}, vibrant colors, {color} tones, dynamic composition, Studio Ghibli inspired, 4K, highly detailed",
    "realistic": "Photorealistic, {subject}, {action}, natural {lighting}, {color} tones, sharp focus, professional photography, 8K, detailed textures",
    "cyberpunk": "Cyberpunk aesthetic, {subject}, {action}, neon lighting, {color} accents, rain-slicked streets, Blade Runner style, 8K, cinematic, fog, lens flare",
}

# 用户输入 → 模板
# subject = 用户描述的主体
# action = 用户描述的动作
# lighting = 根据用户说的"白天/晚上/室内"映射
# color = 用户说的色调
# mood = 用户说的氛围
```

纯模板模式生成的质量不如 AI，但在没有 AI API 的时候能保证流水线不中断。生成后跳过步骤 1.4（确认），直接进入生成阶段。

**步骤 1.4 — 用户确认**

向用户展示：
1. 场景拆解列表（每个场景一句话描述 + 时长）
2. 每个场景的第一个 prompt（作为示例）
3. 总体风格方向、画幅、调色方案
4. 预估消耗即梦积分

用户确认后再进入生成阶段。

### 阶段 2：即梦视频生成

**步骤 2.1 — 检查状态**

```bash
dreamina user_credit
```

如果积分不足（< 场景数 × 10），提前告知用户。

**步骤 2.2 — 创建工作目录**

```bash
mkdir -p ~/auto-video-output/<project-name>/
```

**步骤 2.3 — 逐场景生成**

对每个场景：

```bash
dreamina text2video \
  --prompt "<阶段1生成的精美英文prompt>" \
  --duration <4-8> \
  --ratio "<根据平台: 9:16竖屏/16:9横屏>" \
  --model_version seedance2.0fast \
  --poll 120
```

关键参数说明：
- `--model_version`：默认用 `seedance2.0fast`（快且质量好），用户要求最高质量时用 `seedance2.0`
- `--duration`：4-8秒最佳，生成时间短成功率高
- `--poll 120`：等待最多120秒，适合 fast 模型
- `--ratio`：竖屏9:16，横屏16:9

**重要规则：**
- 每次只提交一个场景，等 `query_result` 返回成功后再提交下一个
- 如果某个场景生成失败（`gen_status: fail`），最多重试 2 次，每次都微调 prompt
- 生成成功后立即 download 到工作目录并重命名为场景编号：

```bash
dreamina query_result --submit_id=<id> --download_dir ~/auto-video-output/<project-name>/raw/
# 然后重命名
mv ~/auto-video-output/<project-name>/raw/<原始文件名>.mp4 ~/auto-video-output/<project-name>/raw/scene_01.mp4
```

**步骤 2.4 — 生成进度跟踪**

维护一个进度表，实时向用户报告：

```
场景 1/8 ✅ 完成 (submit_id: xxx)
场景 2/8 🔄 生成中...
场景 3/8 ⏳ 等待中
...
已消耗积分: 40/225
```

### 阶段 3：整理素材

所有场景生成完毕后：

```
~/auto-video-output/<project-name>/
├── raw/                     # 即梦生成的原始视频
│   ├── scene_01.mp4
│   ├── scene_02.mp4
│   ├── ...
│   └── scene_08.mp4
├── edit/                    # video-use 工作目录（留空，由 video-use 自动填充）
└── project-brief.md         # 项目摘要（中文场景描述 + 剪辑要求）
```

创建 `project-brief.md`：

```markdown
# <项目名称>

## 场景列表
| 编号 | 文件 | 时长 | 内容描述 | 中文提示词 |
|------|------|------|----------|------------|
| 01 | scene_01.mp4 | 6s | 开场钩子 | ... |
| 02 | scene_02.mp4 | 5s | 问题展示 | ... |

## 剪辑要求
- 目标时长: XX秒
- 节奏: 快/中/慢
- 字幕: bold-overlay / natural-sentence / 无
- 调色: warm_cinematic / neutral_punch / 无
- 转场: 硬切 / 淡入淡出
- 其他: ...
```

### 阶段 4：自动剪辑（video-use）

**步骤 4.1 — 启动 video-use**

切换到素材目录，按照 video-use skill 的流程进行：

```bash
cd ~/auto-video-output/<project-name>/
```

然后在此目录下启动 Claude Code（或直接在当前会话中调用 video-use skill），按照 video-use 的流程：

1. **Inventory**：运行 `transcribe_batch.py` 转译所有场景
2. **Pack**：运行 `pack_transcripts.py` 打包转录
3. **策略**：基于 `project-brief.md` 和实际素材，提出剪辑策略
4. **执行**：生成 EDL → 渲染 → 自检
5. **交付**：输出 `edit/final.mp4`

**步骤 4.2 — 剪辑策略要点**

因为是 AI 生成的素材（非实拍），剪辑时有特殊考量：
- 每个场景已经是精选片段，不需要大幅裁剪
- 重点在于**转场衔接**和**统一调色**
- 如果用户要求字幕，用 project-brief.md 中的中文描述作为字幕基础
- 默认用硬切转场，简洁有力
- 统一应用调色 preset 让所有场景视觉一致

**步骤 4.3 — 自检**

按 video-use 规则自检：每一刀切点 ±1.5s 检查画面和音频，字幕是否被遮挡，3次自检上限。

### 阶段 5：交付

向用户报告：

```
🎬 视频生成完成！

📁 项目目录: ~/auto-video-output/<project-name>/
📹 原始素材: raw/ (8个场景)
✂️ 成片: edit/final.mp4
📊 统计:
  - 总时长: XX秒
  - 即梦积分消耗: XX
  - Deepgram 转译: 免费 ($200额度)
  - 总耗时: XX分钟

🔗 成片路径: ~/auto-video-output/<project-name>/edit/final.mp4
```

## 🖼️ 图片模式（短流水线）

图片模式只走到即梦生成那一步，不涉及 video-use 剪辑。流程：

```
用户输入 → AI引擎选择 → 深度思考 → 提示词优化 → 即梦生成图片 → 下载返回
```

### 图片模式 - 阶段 0：AI 引擎选择

与视频模式相同，按优先级选择 AI 提示词引擎。详细逻辑见视频模式「步骤 1.0」，此处复用同一套检测和选择流程。

如果所有 AI 均不可用，降级到图片纯模板模式：

```python
TEMPLATES_IMAGE = {
    "photorealistic": "Photorealistic, {subject}, {pose}, {environment}, {lighting}, {color} tones, {composition}, 8K, hyperdetailed, sharp focus, professional photography",
    "anime": "Anime style, {subject}, {pose}, {environment}, {lighting}, {color} palette, {composition}, highly detailed, Studio Ghibli inspired, 4K",
    "oil_painting": "Oil painting, {subject}, {pose}, {environment}, {lighting}, {color} palette, {composition}, masterpiece, detailed brushstrokes, classical art style",
    "cyberpunk": "Cyberpunk, {subject}, {pose}, neon-lit {environment}, {lighting}, {color} neon accents, {composition}, Blade Runner aesthetic, 8K, detailed",
    "minimalist": "Minimalist, {subject}, {pose}, clean {environment}, {lighting}, {color}, {composition}, simple composition, negative space, elegant",
}
```

### 图片模式 - 阶段 1：理解需求

与视频模式类似，但更聚焦于单帧画面：

| 维度 | 要搞清楚的事情 |
|---|---|
| **画面内容** | 主体是什么？在做什么？环境/背景？ |
| **视觉风格** | 写实/动漫/赛博朋克/油画/水墨/3D渲染/极简/复古？ |
| **构图** | 特写/中景/全景？三分法/对称/引导线？ |
| **光影** | 自然光/棚拍/逆光/侧光/霓虹灯/黄金时刻？ |
| **色调** | 暖色/冷色/黑白/低饱和/电影调色/鲜艳？ |
| **画幅** | 1:1 正方形 / 16:9 横屏 / 9:16 竖屏 / 3:4 / 21:9？ |
| **用途** | 海报/壁纸/社交媒体配图/插画/头像？ |
| **数量** | 几张？单张还是系列（同一风格多张）？ |

### 图片模式 - 阶段 2：生成即梦提示词

为每张图生成极其详细的 English prompt（即梦模型对英文理解更好）。

**提示词公式（即梦图片优化版）：**

```
[Subject] + [Action/Pose] + [Environment] + [Lighting] + [Color palette] + [Composition] + [Style] + [Quality keywords]

Subject: 精确描述主体外观，年龄/性别/穿着/表情/材质
Action/Pose: 动态还是静态，什么姿态
Environment: 室内/室外/城市/自然/抽象背景，具体细节
Lighting: Golden hour sunlight / Soft studio light / Moody chiaroscuro / Neon night / Diffused natural light
Color palette: Warm amber + teal / Muted earth tones / Vibrant pop colors / Moody dark + accent
Composition: Rule of thirds / Symmetrical / Leading lines / Shallow DOF / Wide angle
Style: Photorealistic / Oil painting / Anime / 3D render / Minimalist / Cyberpunk
Quality: 8K, hyperdetailed, masterpiece, sharp focus, professional photography
```

每个 prompt 至少 40 个词。

### 图片模式 - 阶段 3：即梦生成

```bash
# 1. 检查积分
dreamina user_credit

# 2. 创建工作目录
mkdir -p ~/auto-video-output/<project-name>/images

# 3. 生成（单张）
dreamina text2image \
  --prompt "<精美英文prompt>" \
  --ratio "<1:1 / 16:9 / 9:16 / 3:4 / 21:9>" \
  --model_version 4.7 \
  --resolution_type 2k \
  --poll 60
```

**参数选择逻辑：**
- `--model_version`：默认 `4.7`（最新稳定版），追求极致质量用 `5.0`
- `--resolution_type`：`2k` 日常够用，海报/壁纸用 `4k`
- `--ratio`：根据用途选（头像 1:1，手机壁纸 9:16，桌面壁纸 16:9）
- `--poll 60`：图片生成比视频快，60秒够用

**多张图片：** 如果用户要系列图（如一套表情包、一套插画），**并行提交**再逐个下载：

```bash
# 并行提交
dreamina text2image --prompt "..." --ratio 1:1 --poll 90 &
dreamina text2image --prompt "..." --ratio 1:1 --poll 90 &
wait

# 逐个下载
dreamina query_result --submit_id=<id_1> --download_dir ~/auto-video-output/<project-name>/images/
```

### 图片模式 - 阶段 4：交付

向用户报告：

```
🖼️ 图片生成完成！

📁 输出目录: ~/auto-video-output/<project-name>/images/
🖼️ 图片数量: X 张
📊 即梦积分消耗: XX (剩余 XX)
```

---

## 重要注意事项

### 即梦积分管理

- 每次 text2video 消耗约 5-10 积分（视参数而定）
- 每次 text2image 消耗约 1-3 积分（视参数/分辨率而定）
- `seedance2.0fast` 消耗较少，`seedance2.0` 消耗较多
- 必须在阶段1确认时告知用户预估消耗
- 积分不足时不要继续，先让用户充值

### 提示词规范

- **必须用英文**，即梦 Seedance 对英文 prompt 理解更好
- **越详细越好**，50词以上的 prompt 质量显著高于短 prompt
- **避免否定词**，AI 视频模型对 "no X" 不如 "X-free" 效果好
- **加质量关键词**：8K, cinematic, photorealistic, film grain 等
- **时间连续性**：如果场景之间有时间关系，在 prompt 中保持连贯

### 错误处理

- 生成失败（gen_status: fail）：检查 fail_reason，微调 prompt 重试，最多2次
- 下载失败：重试 query_result --download_dir
- 转译失败：检查 Deepgram API key 和音频轨道
- 积分不足：暂停并告知用户

### 画幅对应表

| 平台 | ratio | 分辨率 |
|------|-------|--------|
| 抖音/快手/Reels/Shorts | 9:16 | 1080×1920 |
| B站/YouTube | 16:9 | 1920×1080 |
| 小红书/Instagram | 1:1 或 3:4 | 1080×1080 / 1080×1440 |
| 宽银幕电影感 | 21:9 | 2520×1080 |

## 反模式

- ❌ 不限积分就直接全部用 seedance2.0（又贵又慢）
- ❌ 用中文 prompt（Seedance 对英文理解好得多）
- ❌ 每个场景生成超过 8 秒（成功率下降）
- ❌ 不等上一个完成就提交下一个（可能触发限流）
- ❌ 不向用户确认就进入生成阶段（烧了积分用户不满意就白烧了）
- ❌ 跳过 video-use 自检直接交付
- ❌ 场景之间没有视觉变化（全是一个景别，剪出来像一镜到底）
