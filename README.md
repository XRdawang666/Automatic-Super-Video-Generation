# Automatic-Super-Video-Generation

All-in-one AI video/image generation & editing skill for Claude Code / Codex.

## Features

- 🎬 **Video Mode**: Idea → brainstorm → prompt engineering → Dreamina Seedance → video-use auto-edit → final.mp4
- 🖼️ **Image Mode**: Idea → brainstorm → prompt engineering → Dreamina text2image → download
- 🤖 **Multi-AI Engine**: Auto-detect available AI (DeepSeek/Claude/OpenAI/Groq/Gemini/Ollama), fallback to template mode
- 🔑 **Free Transcription**: Built-in Deepgram patch replaces ElevenLabs Scribe in video-use

## Quick Install

```bash
# 1. Install this skill
git clone https://github.com/XRdawang666/Automatic-Super-Video-Generation.git ~/.claude/skills/Automatic-Super-Video-Generation

# 2. Install Dreamina CLI (video/image generation)
curl -s https://jimeng.jianying.com/cli | bash

# 3. Install video-use + Deepgram patch (AI editing)
git clone https://github.com/browser-use/video-use ~/Developer/video-use
cd ~/Developer/video-use && pip install -e .
cp ~/.claude/skills/Automatic-Super-Video-Generation/transcribe.py ~/Developer/video-use/helpers/transcribe.py
ln -sfn ~/Developer/video-use ~/.claude/skills/video-use

# 4. Configure Deepgram API Key (free $200 credit)
# Sign up at https://console.deepgram.com → get API Key
echo 'DEEPGRAM_API_KEY=your-key-here' > ~/Developer/video-use/.env

# 5. Install ffmpeg
# Windows: winget install Gyan.FFmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

## New Computer Setup

```bash
git clone https://github.com/XRdawang666/Automatic-Super-Video-Generation.git ~/.claude/skills/Automatic-Super-Video-Generation
# Then say "check auto-video environment" in Claude Code — it auto-detects missing deps
```

## Dependencies

| Component | Purpose | Install |
|-----------|---------|---------|
| [Dreamina CLI](https://jimeng.jianying.com/cli) | Video/image generation | `curl -s https://jimeng.jianying.com/cli \| bash` |
| [video-use](https://github.com/browser-use/video-use) | AI video editing | `git clone ... && pip install -e .` |
| [Deepgram](https://console.deepgram.com) | Free transcription ($200 credit) | Sign up → get API Key |
| ffmpeg | Media processing | `winget install Gyan.FFmpeg` / `brew install ffmpeg` |

## Cross-Platform

| Platform | Skill Path | Status |
|----------|-----------|--------|
| Claude Code | `~/.claude/skills/` | ✅ Full support |
| Codex | `~/.codex/skills/` | ✅ Core features work |

> Codex users: replace `~/.claude/skills/` with `~/.codex/skills/` in install commands.

## Usage

In Claude Code or Codex:

- "Make me a 60-second product launch video" — 🎬 Video mode
- "Generate a cyberpunk-style poster" — 🖼️ Image mode

All output lands in `~/auto-video-output/<project-name>/`.
