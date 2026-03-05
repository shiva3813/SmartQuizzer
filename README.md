# SmartQuizzer Live

SmartQuizzer Live is a Streamlit app that:
- Generates quizzes from uploaded PDF notes
- Stores quiz data and attempts in a backend SQLite database
- Shows interactive live analytics (trend + accuracy distribution)

## Run locally

```bash
pip install -r requirement.txt
streamlit run app.py
```

## Backend datastore

The backend database is `data/smartquizzer.db` and is auto-created on app start.

## GitHub integration

Run these commands in this project folder:

```bash
git init
git add .
git commit -m "Upgrade SmartQuizzer to realtime interactive app with SQLite backend"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

If your repository already exists locally with a remote:

```bash
git add .
git commit -m "Upgrade SmartQuizzer to realtime interactive app with SQLite backend"
git push
```
