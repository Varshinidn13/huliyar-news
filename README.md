# ಹುಳಿಯಾರು ಸುದ್ದಿ ಸಮಾಚಾರ

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3-000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Live](https://img.shields.io/badge/Live-🌐-c0392b?style=for-the-badge)](https://huliyarbabunews.pythonanywhere.com)

> **Huliyar News** — A Kannada-language rural news website built with Flask. Features a rich editor dashboard for publishing news articles with images, categories, breaking news alerts, and a clean mobile-first frontend.

---

## Features

| Feature | Description |
|---|---|
| **News Feed** | Homepage with categorized articles, sidebar with trending & latest |
| **Category Filtering** | ಸ್ಥಳೀಯ, ರಾಜಕೀಯ, ರೈತ ಸುದ್ದಿ, ಶಿಕ್ಷಣ, ಕ್ರೀಡೆ, ಧಾರ್ಮಿಕ, ವಾಣಿಜ್ಯ, ತಾಲ್ಲೂಕಿನ ಸುದ್ದಿ, ಅಪರಾಧ |
| **Rich Editor** | Bold, color (red/blue/green/black/custom), image uploads per article |
| **Breaking News** | Ticker bar with auto-scrolling headlines |
| **Trending Widget** | Sidebar sorted by view count (top 7) |
| **SEO / Open Graph** | `og:image`, `og:title`, `og:description` for social share previews |
| **Mobile-first** | Responsive design with Kannada fonts (Noto Sans/Serif Kannada) |
| **Image Upload** | Hero image + inline block images, auto-strip EXIF metadata |
| **Dashboard** | Editor panel to post, edit, delete articles with live preview |

---

## Screenshots

| Homepage | Editor |
|---|---|
| ![Home](https://img.shields.io/badge/View-Live%20Site-c0392b?style=flat-square) | ![Editor](https://img.shields.io/badge/View-Live%20Site-c0392b?style=flat-square) |
| [huliyarbabunews.pythonanywhere.com](https://huliyarbabunews.pythonanywhere.com) | `/editor/login` from the live site |

---

## Tech Stack

- **Backend:** Python / Flask 2.3
- **Database:** SQLite 3
- **Frontend:** Vanilla HTML + CSS + JS (responsive, no framework)
- **Fonts:** Google Noto Sans Kannada & Noto Serif Kannada
- **Deployment:** PythonAnywhere

---

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/Varshinidn13/huliyar-news.git
cd huliyar-news

# 2. Install dependencies
pip install flask pillow pytz

# 3. Run
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

---

## Project Structure

```
├── app.py              # Flask application
├── wsgi.py             # WSGI entry point (PythonAnywhere)
├── .gitignore
├── requirements.txt
├── static/
│   ├── logo.png
│   └── uploads/        # Uploaded images
├── templates/
│   ├── base.html           # Base layout
│   ├── index.html          # Homepage
│   ├── news_detail.html    # Article detail page
│   ├── editor_login.html   # Editor login
│   ├── editor_dashboard.html
│   ├── editor_post.html    # New article editor
│   └── editor_edit.html    # Edit article editor
└── news.db             # SQLite database (auto-generated)
```

---

## Deployment

This site is deployed on **PythonAnywhere**. To deploy your own copy:

1. Upload all files to PythonAnywhere
2. Set up the WSGI file to point to `wsgi.py`
3. Create a MySQL/SQLite database (SQLite is local)
4. Reload the web app

---

## License

[MIT](LICENSE)

---

<p align="center">
  <sub>Built with ❤️ for Huliyar, Karnataka</sub>
</p>
