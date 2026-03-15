# 🪞 SellerMirror

**SellerMirror** is a competitive intelligence and strategy analytics platform designed for e-commerce sellers. It unifies proprietary product data with competitor metrics to detect market shifts, quantify trust gaps, and recommend high-leverage strategic actions.

Instead of presenting raw, uninterpretable data points, SellerMirror distills complex market signals into a single pane of glass, ultimately generating plain-spoken, AI-driven strategic advice.

## 🏗️ Technical Architecture & Pipeline Flow

The platform operates on a robust data processing pipeline consisting of five core stages:

1. **Data Ingestion (`ingestion/`)**: Loads and standardizes historical reviews and core product metrics (price, daily purchases, etc.) for both your product and the competitor's. 
2. **Trend Validation (`trend_validator/`)**: Filters out seasonal noise and unvalidated spikes to extract genuine weekly mathematical trends (e.g., rating velocity, review volume).
3. **Scoring Engine (`scoring/`)**: Computes a proprietary out-of-100 **Product Health Score** and **Competitor Vulnerability Score**.
4. **AI Analytics (`analytics/`)**: Operates three distinct competitive breakdown modules:
   - **Complaint Matchup**: Uses Zero-Shot NLP to categorize negative reviews and find out who is failing in what domain (e.g., quality, listing, delivery).
   - **Customer Trust**: Compares your repeat purchase rate against the competitor's rating velocity.
   - **Momentum**: Detects panic-discounting (streak price drops) combined with review volume declines.
5. **Alert Gate (`alerts/`)**: A multi-signal evaluation gate that acts as a circuit breaker, firing strategic alerts (Red/Yellow/Green) when specific market conditions converge (e.g., high vulnerability + price dropping + stable ghost rate).

All of these backend processes are orchestrated and visualized by the **Streamlit Dashboard** (`dashboard/app.py`).

---

## 🧠 AI Models Used

The SellerMirror architecture heavily leverages two distinct AI models for separate layers of the stack:

### 1. `facebook/bart-large-mnli` (Hugging Face Transformers)
- **Role:** Data Analytics & Categorization
- **Where:** `analytics/analytics.py`
- **Why it's used:** This is a **Zero-Shot Classification** model. Rather than relying on rigid, hardcoded keyword matching (which breaks easily with slang or misspellings), this transformer model can take pure review text and classify it into semantic categories (like *“product quality issue”* or *“packaging damage”*) without requiring any prior domain-specific fine-tuning.
- **Advantage:** It scales instantly to new products or niches. You don't need a labeled dataset of 10,000 phone case reviews to start classifying complaints accurately.

### 2. `mistral-large-latest` (Mistral AI API)
- **Role:** Strategy Agent & Chief Strategy Officer
- **Where:** `agents/strategy_agent.py`
- **Why it's used:** Once all the hard data (health scores, complaint counts, price drop streaks) is aggregated, it needs to be interpreted. Mistral Large is a state-of-the-art Large Language Model (LLM) employed here to synthesize the complex JSON pipeline output into a **human-readable, highly actionable 3-point strategic summary.** Furthermore, it acts as an interactive chat agent capable of answering specific seller questions grounded strictly in the pipeline's data.
- **Advantage:** Mistral is highly capable of following strict formatting instructions and reasoning over provided context. It prevents the user from suffering "dashboard fatigue" by explicitly telling them exactly what the data means and what to do next (e.g., *"Hold your price, their price drop signals desperation"*).

---

## ⚡ Strategic Advantages of the Platform

1. **Calculated Contrarianism:** The platform is designed to stop sellers from knee-jerk reacting. If a competitor drops their price for 7 days, most sellers will panic and drop theirs. SellerMirror correlates that price drop with a declining *rating velocity* to correctly identify it as desperation, advising the user to hold price and preserve margins.
2. **Actionable Over Aesthetic:** Every module in the platform is tied to an action. The *Complaint Matchup* explicitly tells the seller which keywords to target in their ad spend (e.g., "You win on delivery, amplify that").
3. **Human-Readable Metrics:** Complex statistical regressions (like rating velocity measured in negative decimals/week) are translated into plain English (e.g., *"Dropping 0.3★/wk"*), making enterprise-grade analytics accessible to everyday sellers.
4. **Agentic Strategy:** The integrated Mistral agent means sellers don't have to hire a data scientist to interpret their dashboard. They can chat directly with their data.

---

## 🚀 Running the Platform

Ensure you have a `.env` file at the project root containing your Mistral API key:
```env
MISTRAL_API_KEY=your_key_here
```

Install the dependencies:
```bash
pip install mistralai python-dotenv pandas transformers torch streamlit numpy plotly
```

Launch the dashboard:
```bash
streamlit run dashboard/app.py
```
