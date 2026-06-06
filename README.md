# Automatic-Super-Video-Generation

全自动视频/图片生成与剪辑 Claude Code Skill。

## 功能

- 🎬 **视频模式**：用户输入创意 → AI 深度思考 → 提示词优化 → 即梦 Seedance 生成 → video-use 自动剪辑 → 成品
- 🖼️ **图片模式**：用户输入想法 → AI 深度思考 → 提示词优化 → 即梦 text2image 生成 → 下载返回
- 🤖 **多引擎支持**：自动检测可用 AI 引擎（DeepSeek/Claude/OpenAI/Groq/Gemini/Ollama），无 API 时降级模板模式
- 🔑 **零成本转译**：内置 Deepgram 补丁，替换 video-use 的 ElevenLabs 为免费 Deepgram

## 安装

```bash
git clone https://github.com/xur6883/Automatic-Super-Video-Generation.git ~/.claude/skills/Automatic-Super-Video-Generation
```

## 依赖

- [dreamina CLI](https://jimeng.jianying.com/cli) — 即梦视频/图片生成
- [video-use](https://github.com/browser-use/video-use) — AI 视频剪辑（自动打 Deepgram 补丁）
- [Deepgram](https://console.deepgram.com) — 免费语音转译（00 新用户额度）
- ffmpeg — 音视频处理
## 使用

在 Claude Code 中：

「帮我做一个 60 秒的产品宣传片」— 视频模式
「帮我生成一张赛博朋克风格的海报」— 图片模式
