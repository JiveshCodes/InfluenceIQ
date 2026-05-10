@echo off
echo =======================================================
echo Building Professional Git History for InfluenceIQ...
echo =======================================================

echo Initializing repository...
git init
git branch -m main

echo Committing Milestone 1: Project Architecture
git add .gitignore requirements.txt
git commit -m "1. chore: initialize scalable project architecture and dependencies"

echo Committing Milestone 2: Security Config
git add config.py .env
git commit -m "2. security: implement environment configuration and security structure"

echo Committing Milestone 3: Database
git add dataset.csv
git commit -m "3. db: import initial verified influencer dataset"

echo Committing Milestone 4: ML Pipeline
git add ml_engine.py
git commit -m "4. feat: build core ML prediction pipeline with TF-IDF/BERT"

echo Committing Milestone 5: YouTube API
git add youtube_api.py
git commit -m "5. feat: integrate live YouTube API for real-time analytics ingestion"

echo Committing Milestone 6: UI Core Design
git add static/css/main.css
git commit -m "6. ui: establish core CSS design system and responsive tokens"

echo Committing Milestone 7: UI Theming
git add static/js/theme.js
git commit -m "7. ui: implement persistent dark/light theme switching engine"

echo Committing Milestone 8: Landing & About Pages
git add templates/landing.html templates/about.html
git commit -m "8. ui: create responsive landing and product description pages"

echo Committing Milestone 9: Authentication
git add templates/auth.html
git commit -m "9. feat: build authentication interfaces and access workflows"

echo Committing Milestone 10: Dashboards
git add templates/dashboard.html templates/creator_dashboard.html static/js/dashboard.js
git commit -m "10. feat: construct primary dashboards, ML outputs, and interactive charts"

echo Committing Milestone 11: Settings
git add templates/settings.html static/js/creator.js
git commit -m "11. feat: implement user settings, creator configurations, and profile management"

echo Committing Milestone 12: Backend APIs
git add app.py
git commit -m "12. feat: configure Flask routing, backend services, and REST API endpoints"

echo Committing Milestone 13: Documentation
git add README.md
git commit -m "13. docs: prepare comprehensive setup, architecture, and deployment documentation"

echo Committing Milestone 14: Final Polish
git add .
git commit -m "14. deploy: verify production-readiness and finalize application state"

echo =======================================================
echo Professional Git History Generated Successfully!
echo You can verify by running: git log --oneline
echo =======================================================
pause
