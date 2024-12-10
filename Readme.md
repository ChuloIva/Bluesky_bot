# Project Overview: Politician Bot

This project leverages various APIs, libraries, and models to create an automated conversational bot designed for simulating politically polarized discussions. The system operates in a controlled environment where two distinct personas engage in back-and-forth interactions to emulate debates or discussions. Below is a detailed overview of the project's components and workflow:

---

## Key Features and Components

### Libraries and Dependencies
- **`rich`**: For enhanced console output with styling and colors.
- **`dotenv`**: For managing environment variables securely.
- **`atproto`**: For interaction with decentralized protocol platforms.
- **`google.generativeai`**: For using Google's Generative AI models.
- **`praw`**: For accessing Reddit's API and retrieving discussions.
- **`wikipedia`**: For fetching concise summaries of topics.
- **`newsapi`**: For retrieving news articles from various sources.
- **`fuzzywuzzy`**: For text similarity analysis to find relevant matches.
- **`requests`**: For handling HTTP requests, including error handling.

---

### Workflow Overview

#### **1. Initialization**
- Environment variables (e.g., API keys, user credentials) are loaded using `dotenv`.
- Generative AI models from Google's GenAI are configured (e.g., `gemini-1.5-pro`, `gemini-1.5-flash`).
- File paths for persona and task prompts are defined and loaded.

#### **2. News Data Gathering**
- News articles are retrieved using the **NewsAPI**.
- Articles are filtered and stored as structured data, including titles, descriptions, and content.

#### **3. Context Enrichment**
- **Keyword Extraction**: Keywords are extracted from news data using small generative models for further exploration.
- **Brave Search Integration**: Bias-specific context (left/right) is added using Brave Search's goggles feature.
- **Wikipedia Summaries**: Summaries of keywords are fetched to provide factual context.
- **Reddit Discussions**: Top discussions related to the topic are retrieved from Reddit.

#### **4. Generative Content Creation**
- Prompts are dynamically generated using the gathered data, including:
  - News data.
  - Bias-specific search results.
  - Wikipedia and Reddit insights.
- Responses are crafted by a large generative model to simulate biased political opinions.

#### **5. Thread Simulation**
- A conversation begins with one persona posting an initial tweet.
- The other persona replies, creating a thread.
- Context from the ongoing thread is fed into the generative models to maintain continuity.
- Replies alternate between personas until a specified number of interactions (e.g., 10) is reached.

#### **6. Interaction Logic**
- Responses are designed to align with predefined personas and maintain consistency in tone and perspective.
- Text similarity analysis ensures relevance in replies by identifying the best matching comment in a thread.

---

### Use Cases
- **Political Simulation**: Mimicking polarized discussions for educational or research purposes.
- **Debate Training**: Providing examples of argumentation styles for debate preparation.
- **Content Generation**: Producing content for scenarios requiring simulated multi-perspective analysis.

---

### Technical Specifications
- **Programming Language**: Python
- **APIs and Services**:
  - Google GenAI
  - Brave Search API
  - NewsAPI
  - Reddit API (via PRAW)
  - Wikipedia API
- **Generative Models**: Multiple configurations of Google's Gemini models for diverse task handling.

---

This project demonstrates how AI and APIs can collaborate to emulate complex human-like interactions in a politically charged context, making it a powerful tool for research, education, and content generation.