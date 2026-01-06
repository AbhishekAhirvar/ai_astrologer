---
title: AI Astrologer
emoji: 🪐
colorFrom: indigo
colorTo: indigo
sdk: gradio
sdk_version: 6.2.0
app_file: app.py
pinned: false
---

# AI Astrologer

An AI-powered Vedic & KP Astrologer chatbot built with Python and Google Gemini 3.0 Flash.

## Features
- **Vedic AI Chat**: Traditional Vedic analysis with 15+ quick questions.
- **KP AI Chat**: Specialized Krishnamurti Paddhati analysis using Sub-lords and Significators.
- **Vedic Chart Generation**: Support for D1, D9, D10, D12 charts.
- **Dynamic Suggestions**: 3 AI-generated follow-up questions after every response.
- **Interactive UI**: Clean sidebar layout using Gradio.

## Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Google Gemini API key in a `.env` file or environment variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
4. Run the application:
   ```bash
   python app.py
   ```
