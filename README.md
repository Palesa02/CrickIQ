# CrickIQ 🏏 - Cricket Intelligence

AI-powered match predictions and player performance forecasts for men's & women's T20 and Test cricket.

**🚀 Live Demo:** https://crickiq-8ecs5mneeqjewks8laaacv.streamlit.app

### What it does
- Predicts match winners with win probability (e.g. SA 74.4% vs India 25.6%)
- Trained on 6,766 real matches (2005-2026)
- Player ratings, venue stats, chase win rate & toss impact
- Covers T20 & Test, Men's & Women's cricket

### Built with
Python | Streamlit | scikit-learn | pandas | GitHub Releases (for 803MB model hosting)

### How I built it
Trained a machine learning model on 6,766 matches, then solved the 803MB deployment challenge by hosting the model via GitHub Releases and auto-downloading it in Streamlit Cloud.

### Data
- t20s_male: 3646 files (2005-2026)
- t20s_female: 2199 files (2009-2026)
- Tests: 897 files
