# 🌬️ AeroSense AI

A **Conversational Analytics & Multimodal** assistant for air quality in Asia-Pacific cities.
Built for **Gen AI Academy APAC (Cohort 2)** — Problem Statement 1: *AI for Better Living*.

Developed as a **Solo Developer / Lone Wolf** project to maintain strict architectural control and scalable execution.

## The Problem
APAC cities (Jakarta, Delhi, Bangkok, etc.) face serious air pollution, yet PM2.5 data is often difficult for the general public to interpret. AeroSense transforms raw tabular data, real-time weather APIs, and sky images into actionable health recommendations using natural language.

## Key Features (The "WOW" Factors)
- 💬 **Natural Language to SQL:** Ask about historical air quality in everyday language. The agent autonomously writes and executes safe (read-only) SQL against BigQuery.
- 📸 **Multimodal Vision Analysis:** Users can upload photos of their local sky. Gemini 2.5 Flash analyzes the visual smog/visibility and correlates it with database metrics.
- 🌐 **Real-Time Internet Grounding:** Custom search tool integration using Open-Meteo API and Wikipedia to fetch live weather data and medical guidelines, preventing LLM hallucinations.
- 📊 **Smart Markdown Rendering:** Automatically formats complex multi-city comparisons into clean, readable Markdown tables with color-coded health indicators (🔴🟡🟢).

## Tech Stack (Google Cloud Ecosystem)
- **Gemini 2.5 Flash** — The core LLM brain (Multimodal & Fast)
- **Google Agent Development Kit (ADK)** — Advanced agentic orchestration and tool calling
- **BigQuery** — Robust data storage and fast SQL execution
- **Streamlit** — Interactive, chat-based user interface

## How The Agentic Routing Works
1. User provides input (Text + Optional Image).
2. The **ADK Router** evaluates the request.
3. If data is needed, it triggers the `query_air_quality` tool (writes SQL -> executes in BigQuery -> parses results).
4. If real-time weather/news is needed, it triggers the `search_internet_for_news` tool.
5. Gemini synthesizes all context (Visual + SQL Data + Internet) into a final, user-friendly response.

## Running Locally
1. Install dependencies: `pip install -r requirements.txt`
2. Create `aerosense/.env` and add:
   ```env
   GOOGLE_API_KEY="your_api_key_here"
   GOOGLE_CLOUD_PROJECT="aerosense-ai-501007"
3. Authenticate with Google Cloud for BigQuery access: gcloud auth application-default login
4. Run the app: streamlit run app.py