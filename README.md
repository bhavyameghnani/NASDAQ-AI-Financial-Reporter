# 🎙️ AI News Podcast Generator

## Project Overview

The **AI News Podcast Generator** is a sophisticated multi-agent system designed to fully automate the process of researching the latest artificial intelligence news, analyzing its financial impact on NASDAQ-listed US companies, compiling a detailed report, and synthesizing a conversational audio podcast.

This project showcases the use of multiple tools (Google Search, Yahoo Finance), structured data models (`pydantic`), agent chaining (`podcaster_agent`), and custom callbacks for advanced data processing (source filtering, freshness checks, log injection).

## 🚀 Key Features

* **Automated Research:** Searches for the most recent AI-related news, focusing specifically on **NASDAQ-listed US companies**.
* **Financial Context:** Automatically fetches **current stock prices** and **daily changes** for mentioned companies using the `yfinance` library.
* **Structured Reporting:** Compiles all findings into a structured `AINewsReport` and saves it as a **Markdown file** (`ai_research_report.md`).
* **Audio Synthesis:** Converts the report into a natural, conversational script between two hosts (**Joe** and **Jane**) and uses a Text-to-Speech model to generate a **WAV audio file** (`ai_today_podcast.wav`).
* **Data Integrity:** Custom **pre- and post-tool callbacks** enforce data freshness, restrict search to whitelisted, high-quality tech news domains, and inject a detailed processing log into the final report.

## 🛠️ Components and Agents

The system is orchestrated by two primary agents and several support functions:

### 1. `root_agent` (`ai_news_researcher`)
* **Role:** The main orchestrator. It handles the full workflow from initial search to final audio generation request.
* **Tools Used:** `Google Search`, `get_financial_context` (for financial data), `save_news_to_markdown`, and `podcaster_agent` (for audio).
* **Key Logic:** It manages the state, extracts tickers, handles missing financial data gracefully, structures the final report, and creates the podcast script.

### 2. `podcaster_agent`
* **Role:** Audio Generation Specialist. Its sole purpose is to convert a text script into a multi-speaker audio file.
* **Tool Used:** `generate_podcast_audio` (which interfaces with the Gemini API's TTS capability).

### 3. Core Tools & Functions
* `get_financial_context`: Fetches financial data via `yfinance`.
* `wave_file`: A helper for saving raw audio data to a `.wav` format.
* `save_news_to_markdown`: Saves the final structured report to disk.

## ⚙️ Data Flow & Workflow

1.  **Start:** User prompts the `root_agent`.
2.  **Search & Filter:** `root_agent` calls `Google Search`. Pre-tool callbacks modify the query to enforce:
    * **Freshness:** Results from the last week (`tbs=qdr:w`).
    * **Source Quality:** Only whitelisted domains (e.g., `techcrunch.com`).
3.  **Log Injection:** Post-tool callback injects the final `process_log` (including domains sourced) back into the search output.
4.  **Financial Check:** `root_agent` identifies companies and calls `get_financial_context` for stock data.
5.  **Report Structure:** All data is mapped to the `AINewsReport` schema.
6.  **Save Report:** The structured data is formatted as Markdown and saved via `save_news_to_markdown`.
7.  **Scripting:** `root_agent` generates a conversational podcast script.
8.  **Audio Generation:** `root_agent` calls the `podcaster_agent`, passing the script.
9.  **Finish:** `podcaster_agent` generates the audio and saves it as `ai_today_podcast.wav`. The `root_agent` returns the final success message to the user.

## 📄 Schemas

The project relies on strict Pydantic schemas for data integrity:

### `NewsStory`
Defines the structure for each individual news item: `company`, `ticker`, `summary`, `why_it_matters`, `financial_context`, `source_domain`, and `process_log`.

### `AINewsReport`
The top-level output structure: `title`, `report_summary`, and a `stories` list of `NewsStory` objects.