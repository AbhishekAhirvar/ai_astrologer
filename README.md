---
title: AI Astrologer
emoji: 🪐
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.3.0
app_file: app.py
pinned: false
---

# 🪐 AI Astrologer

An AI-powered **Vedic & KP Astrology** platform powered by **OpenAI GPT-5** (2026 Responses API).

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/abhishekahirvar/ai_astrologer)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gradio 6.3](https://img.shields.io/badge/Gradio-6.3-orange.svg)](https://gradio.app/)

## ✨ Features

### 🕉️ Vedic AI Chat
- Traditional Parashara Vedic analysis
- 15+ instant quick questions
- Dasha timing predictions
- Shadbala strength analysis

### 🧭 KP AI Chat  
- Krishnamurti Paddhati (KP) system
- Sub-lord significator analysis
- House cusp-based predictions
- Ruling planets for timing

### 📊 Birth Chart Generator
- **D1 Rasi** - Birth chart
- **D9 Navamsa** - Marriage & destiny
- **Shadbala** - Planetary strength visualization
- **Vimshottari Dasha** - Complete timeline
- **20+ Divisional Charts** - D2 to D60

### 🤖 AI Models
- **GPT-5-nano** - Low reasoning (fast)
- **GPT-5-mini** - Minimal reasoning (balanced)

### 🎯 Bot Modes
- **PRO** - Maximum accuracy
- **LITE** - Token-optimized
- **LEGACY** - Classic behavior

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/AbhishekAhirvar/ai_astrologer.git
cd ai_astrologer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key
Create a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run
```bash
python app.py
```
Opens at: `http://localhost:7860`

## 🧪 Testing
```bash
pip install -r requirements-dev.txt
pytest tests/backend/ -v
```

## 📁 Project Structure
```
ai_astrologer/
├── app.py                 # Gradio UI
├── backend/
│   ├── ai.py              # OpenAI GPT-5 integration
│   ├── astrology.py       # Chart calculations
│   ├── chart_renderer.py  # North Indian chart SVG
│   ├── dasha_system.py    # Vimshottari Dasha
│   ├── shadbala.py        # Planetary strength
│   └── kp_significators.py # KP system
├── tests/                 # pytest test suite
└── requirements.txt
```

## 🔧 Tech Stack
- **Frontend**: Gradio 6.3
- **AI**: OpenAI GPT-5 (Responses API)
- **Astrology**: Swiss Ephemeris, Custom calculations
- **Charts**: Matplotlib, SVG rendering

## 📄 License
MIT License

## 🙏 Credits
Built with ❤️ by [Abhishek Ahirvar](https://github.com/AbhishekAhirvar)
