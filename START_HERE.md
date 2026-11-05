# Start here

Run the app locally without installing MongoDB or creating a database account.
The demo uses an in-memory fake database; its data is cleared whenever the app
stops.

## Step 1 — Install dependencies

In PowerShell, from the project folder:

```powershell
python -m pip install -r requirements.txt
```

## Step 2 — Configure the demo

Copy the example environment file if you do not already have `.env`:

```powershell
Copy-Item .env.example .env
```

The example configuration sets `USE_FAKE_MONGO=1`, so no real MongoDB URI is
needed for the demo.

## Step 3 — Run it

```powershell
python app.py
```

Open **http://localhost:5000** and create an account on the register page.

## Troubleshooting

- **"ModuleNotFoundError"** — run `python -m pip install -r requirements.txt`.
- **MongoDB connection refused** — check that `.env` contains `USE_FAKE_MONGO=1`.
- **Port 5000 already in use** — close the other app using it, or change
  `port=5000` at the bottom of `app.py`.

The fake database is for a presentation/demo only: its data is temporary and is
not shared between app restarts. For persistent data, set `USE_FAKE_MONGO=0`
and configure `MONGO_URI` to point to a real MongoDB server.
