# Windbrook EF Portal — Installation & Deployment Guide

> **Stack:** Python 3 · Flask · SQLite · ReportLab  
> **Hosting:** Railway  
> **Last updated:** April 2026

---


## 1. Prerequisites

Make sure you have the following installed on your machine before starting:

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.9 or higher | `python3 --version` |
| pip | Latest | `pip --version` |
| Git | Any recent | `git --version` |

You will also need:
- A **GitHub account** (free) — to host the code
- A **Railway account** (free tier works) — [railway.app](https://railway.app)

---

## 2. Local Setup

### Step 1 — Get the code

If it's already on GitHub, clone it:

```bash
git clone https://github.com/your-org/ef-portal.git
cd ef-portal
```

---

### Step 2 — Create a virtual environment

```bash
python3 -m venv venv
```

Activate it:

```bash
# macOS / Linux
source venv/bin/activate

You should see `(venv)` appear at the start of your terminal prompt.

---

### Step 3 — Install dependencies

```bash
pip install flask reportlab
```

This installs:
- `flask` — the web framework
- `reportlab` — the PDF generation library

That's it. No database server, no additional services.

---

## 3. Running Locally

```bash
python app.py
```
make sure you have this code block at the bottom of your app.py

```bash
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```	
	
Open your browser and go to:

```
http://YOUR-SERVER-IP:5000
```
Your app will run if your configuration is fine as you can see here:

![App Running Locally](./ReadMe-imgs/app%20run%20locally.png)


![Adding New Client](./ReadMe-imgs/adding%20new%20client.png)


![App running on Railway Hosting](./ReadMe-imgs/app%20run%20on%20Railway%20host.png)


**What happens on first run:**
- The `instance/` folder is created automatically
- `instance/ef_portal.db` (SQLite database) is created with all tables
- A sample client "John & Jane" is seeded so you have data to test with
- The `reports/` folder is created for storing generated PDFs

To stop the server: press `Ctrl + C`

To deactivate the virtual environment when done:

```bash
deactivate
```

---

## 4. Project Structure

```
ef-portal/
├── app.py                          ← Flask app entry point + DB init + seed data
├── requirements.txt                ← Python dependencies
├── Procfile                        ← Railway start command
├── README.md
│
├── models/
│   ├── __init__.py
│   └── database.py                 ← SQLite schema, queries, computed client properties
│
├── routes/
│   ├── __init__.py
│   ├── clients.py                  ← Client CRUD, account/liability management
│   └── reports.py                  ← Report generation, PDF serve + download
│
├── pdf_generators/
│   ├── __init__.py                 ← DictObj adapter for plain dict → attribute access
│   ├── sacs_pdf.py                 ← SACS (cashflow) 2-page PDF
│   └── tcc_pdf.py                  ← TCC (net worth) 1-page PDF
│
├── templates/
│   ├── base.html                   ← Nav + global CSS design system
│   ├── index.html                  ← Client list / dashboard
│   ├── client_detail.html          ← Client profile + account balance editor
│   ├── client_form.html            ← Add / edit client
│   ├── generate_report.html        ← Quarterly data entry + calculation preview
│   └── report_done.html            ← View + download generated PDFs
│
├── instance/                       ← Auto-created. Contains ef_portal.db
└── reports/                        ← Auto-created. Contains generated PDFs
```

## 5. Deploying to Railway

### Step 1 — Push code to GitHub

If your project is not yet on GitHub:

```bash
cd ef-portal
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-org/ef-portal.git
git push -u origin main
```

---

### Step 2 — Create a Railway project

1. Go to [railway.app](https://railway.app) and log in
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Select your `ef-portal` repository
5. Railway will detect Python automatically and begin the first deployment

---

### Step 3 — Add the Procfile

Make sure a `Procfile` exists in the project root with this content:

```
web: python app.py
```
or 

go to Railway console and on the project deployment go to settings>> Deploy>> Custom Start Command and put the code below
```
web: python app.py
```
or
```
gunicorn app:app
```

add start 

### Step 4 — Set environment variables

In Railway dashboard → your service → **Variables** tab, add:

```
SECRET_KEY=your-strong-random-secret-here
```

Railway automatically injects `PORT` — your app reads it with:

```python
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
```
So make sure your app.py has this code block above


### Step 5 — Add persistent volumes

The SQLite database and generated PDFs need to survive deployments. Without volumes, they reset every time you push.

In Railway dashboard → your service → **Volumes** tab:

| Mount path | Purpose |
|-----------|---------|
| `/app/instance` | SQLite database (`ef_portal.db`) |
| `/app/reports` | Generated PDF files |

Click **New Volume** for each, set the mount path, and save.

---

### Step 6 — Get your public URL

Once deployed, go to **Settings → Networking → Generate Domain**.

Railway gives you a URL like:
```
https://sagan-ef-railway-app-demo.up.railway.app/
```

The app is now live. Open it in your browser — the database and sample data are created automatically on first boot.

---

## 6. Persistent Storage on Railway

**Why this matters:** Railway containers are ephemeral — when you redeploy, any files written inside the container are lost unless they are on a mounted volume.

The two paths that need volumes are:

```
/app/instance   ← contains ef_portal.db (all client data, report history)
/app/reports    ← contains all generated PDF files
```

If you skip adding volumes:
- Every deployment will wipe your client data and reports
- The app will re-seed the sample client on each restart

Once volumes are attached, all data persists across deployments, restarts, and Railway plan changes.

---

## 7. Updating the App

After making code changes locally:

```bash
# Test locally first
python app.py

# Push to GitHub
git add .
git commit -m "Description of change"
git push
```

Railway watches your GitHub repository and **auto-deploys** on every push to `main`. Deployment takes about 60–90 seconds. The persistent volumes ensure your data is untouched.

---

## 8. Troubleshooting

### App won't start locally

```
ModuleNotFoundError: No module named 'flask'
```
→ Virtual environment is not activated. Run `source venv/bin/activate` first.

---

### Database errors on first run

```
sqlite3.OperationalError: no such table: clients
```
→ Delete the `instance/` folder and restart. `init_db()` will recreate it cleanly.

```bash
rm -rf instance/
python app.py
```

---

### PDFs not generating

```
FileNotFoundError: [Errno 2] No such file or directory: 'reports/...'
```
→ The `reports/` folder wasn't created. This usually means a permissions issue. Create it manually:

```bash
mkdir reports
```

---

### Railway: data resets after every deploy

→ Volumes are not attached. Follow [Step 5 — Add persistent volumes](#step-5--add-persistent-volumes) above.

---

### Railway: app crashes immediately

Check the Railway **Logs** tab. Common causes:

- Missing `Procfile` → create it with `web: python app.py`
- `PORT` binding issue → ensure `app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))`
- Missing dependency → check `requirements.txt` includes `flask` and `reportlab`

---

### PDFs open as download instead of browser tab

→ The `?download=1` query parameter controls behaviour:
- Without it: PDF opens inline in a new tab (browser viewer)
- With `?download=1`: PDF downloads as a file

Both options are available on the report done page.

---

*Windbrook Solutions · EF Portal v1.0 · April 2026*
