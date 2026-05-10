# InfluenceIQ — AI-Powered Influencer Discovery Platform
![Status](https://img.shields.io/badge/Status-Production--Ready-success)
![Version](https://img.shields.io/badge/Version-v2.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.12-yellow)
![Flask](https://img.shields.io/badge/Flask-2.3-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

> A production-ready SaaS platform utilizing transformer-based Machine Learning to accurately match brands with the right influencers across multiple platforms.

---

## 📖 Overview

InfluenceIQ is a robust, scalable application designed to bridge the gap between brands and creators. By leveraging natural language processing and advanced heuristics, the platform intelligently ranks influencers based on deep semantic matching, engagement rates, audience authenticity, and budget constraints.

### Key Capabilities
- **ML Semantic Matching**: Uses TF-IDF or `Sentence-BERT` embeddings to score contextual relevance between brand needs and influencer profiles.
- **Fraud Detection Engine**: Live scoring of audience authenticity to mitigate influencer fraud.
- **Explainable AI (XAI)**: Provides human-readable reasoning behind match scores to build trust.
- **Live YouTube Sync**: Connects directly to the YouTube Data API to fetch real-time engagement and subscriber metrics.
- **Dynamic Localization**: Instant, zero-latency client-side currency conversions (USD, INR, EUR, GBP, CAD, AED).

---

## 🏗️ Architecture & Project Structure

The project is structured according to professional Flask Application Factory and modular design principles.

```text
influenceiq/
├── config.py            # Environment configurations (Dev, Prod, Test)
├── app.py               # Main Application initialization
├── ml_engine.py         # Core Machine Learning pipeline & Data Access
├── youtube_api.py       # External Service Integrations
├── dataset.csv          # Verified Influencer Corpus
├── requirements.txt     # Dependency lockfile
├── .env.example         # Environment variable templates
├── .gitignore           # Git ignore definitions
├── templates/           # Server-side rendered HTML views
└── static/              # Static Assets (CSS, JS, Images)
```

---

## ⚙️ Development Setup

### Prerequisites
- Python 3.10+
- pip (Python Package Installer)

### 1. Environment Initialization
Clone the repository and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory and configure your secrets:
```env
FLASK_ENV=development
SECRET_KEY=your_secure_random_key
YOUTUBE_API_KEY=your_youtube_api_key
```

### 3. Running the Server
Start the Flask development server:
```bash
python app.py
```
The application will be accessible at: `http://localhost:5000`

---

## 🧠 Machine Learning Pipeline

1. **Query Preprocessing**: Brand inputs (category, budget, target platform) are parsed and expanded using domain-specific keyword mapping.
2. **Embedding Generation**: Both the influencer corpus and the brand query are embedded using `Sentence-BERT` (384-dim) or fallback `TF-IDF` (256-dim).
3. **Similarity Scoring**: Cosine similarity is computed across the matrix.
4. **Weighted Composition**: 
   - *Semantic Similarity* (30%)
   - *Engagement Quality* (25%)
   - *Category Alignment* (20%)
   - *Keyword Overlap* (15%)
   - *Fraud Safety* (10%)
5. **Dynamic Updates**: Live API syncing overwrites static historical data to ensure high-fidelity accuracy.

---

## 🚀 Deployment (Production)

This application is ready for deployment on platforms like Render, Railway, or Heroku. 

For production use, ensure you run the app using a WSGI server like `gunicorn`:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
Ensure `FLASK_ENV` is set to `production` and all API keys are securely stored in the production environment's secret manager.

---

## 📄 License
This project is licensed under the MIT License.
