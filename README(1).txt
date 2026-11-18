Oliver Forex AI — Streamlit demo

Files:
- streamlit_app.py: Streamlit dashboard
- requirements.txt: Python dependencies

GitHub:
1. Upload BOTH files to the root of the Oliver_forex repository.
2. In Streamlit Community Cloud choose that repository and branch main.
3. Main file path: streamlit_app.py
4. Deploy.

API key:
In Streamlit app settings -> Secrets, add:
TWELVE_DATA_API_KEY = "YOUR_TWELVE_DATA_KEY"

Do not put the API key in a public GitHub file.

This is educational/paper-only. It does not place trades or connect to a broker.
It checks seven forex pairs and refreshes the dashboard every 60 seconds while
the app is running. Provider plan limits may prevent checking all pairs each minute.
