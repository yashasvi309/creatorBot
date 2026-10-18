# 🚀 I Created It for Creators — Open-Source AI Creator Studio

> **An autonomous, 3-agent AI content production studio powered locally by Gemma 4 & Ollama (with seamless OpenRouter cloud support).**

---

## 💡 Why "I Created It for Creators"

Independent YouTubers, streamers, and solo creators face two massive bottlenecks:
1. **Creative Burnout:** Turning a single long-form video into tailored Instagram, X, and LinkedIn posts, designing high-CTR thumbnails, and writing YouTube SEO metadata takes hours of manual work.
2. **SaaS Subscription Fatigue:** Paying for Copy.ai, Jasper, and thumbnail tools easily costs **$50–$150+/month**, while requiring creators to upload unreleased scripts and personal face photos to third-party servers.

**I created it for Creators** to solve both problems at once. By orchestrating **Gemma 4** locally via **Ollama** and **FastAPI**, this studio gives every creator their own private, zero-marginal-cost AI production team.

---

## 🧠 3-Agent Architecture

When a creator enters a single **Video Topic**, **Raw Notes**, and points to their **Local Photo Assets**, three specialized agents execute sequentially:

1. **📱 Agent 01 — Social Media Captions Agent**
   * Converts raw bullet points into platform-native copy for **Instagram**, **X (Twitter)**, and **LinkedIn**, complete with scroll-stopping hooks, line breaks, and targeted hashtags.
2. **🎨 Agent 02 — Visual Selection & Thumbnail Strategy Agent**
   * Scans the creator's local subject photo directory, selects the facial expression/pose with the highest psychological **Click-Through Rate (CTR)** potential, writes a **FLUX.1 / SDXL** background generation prompt, and crafts a punchy 2–5 word text overlay in strict JSON format.
3. **▶️ Agent 03 — YouTube SEO & Copywriting Agent**
   * Generates **3 high-CTR titles** (<65 chars), a search-optimized **YouTube description** with automatic chapter timestamp placeholders, and **10 high-intent SEO tags**.

---

## 🔓 Why Open-Source AI Matters Here

- **💸 $0 Marginal Cost:** Run the pipeline 1 time or 1,000 times a month—local inference on Gemma 4 costs nothing.
- **🔒 100% Data Privacy:** Unreleased video scripts, sponsorship details, and personal face assets never leave your machine.
- **🔄 Zero Vendor Lock-In (Dual Engine):** Built primarily for **Local Ollama (`gemma4`)**, but includes a drop-in **OpenRouter engine** so users on low-spec hardware can hot-swap open-weight models in the cloud via `.env`.

---

## 🛠️ Tech Stack

- **AI / LLM Layer:** Google Gemma 4 (`gemma4` via Ollama locally / OpenRouter API)
- **Backend Orchestration:** Python 3, FastAPI, Uvicorn, Requests, Pydantic
- **Frontend Workspace:** HTML5, Tailwind CSS, Marked.js, DOMPurify

---

## ⚡ Quick Start Guide

### 1. Clone & Install Dependencies
```bash
git clone [https://github.com/YOUR_USERNAME/creatorBot.git](https://github.com/YOUR_USERNAME/creatorBot.git)
cd creatorBot
pip install fastapi uvicorn jinja2 requests python-dotenv pydantic