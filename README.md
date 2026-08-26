# EasyTimePro to Zoho People Attendance Middleware

Real-time biometric attendance connector bridging **EasyTimePro** and **Zoho People**.

## 🚀 Features
- **Real-Time Webhook Receiver**: Receives push attendance punches from EasyTimePro over HTTP/HTTPS.
- **Biometric ID Mapping (`mapId`)**: Automatically syncs punches using biometric mapper IDs to Zoho People Employee Profiles.
- **Zoho OAuth Token Management**: Automatically generates, caches, and refreshes OAuth tokens with scope `ZOHOPEOPLE.attendance.ALL`.
- **Duplicate Prevention**: In-memory and persistent record deduplication.
- **Past Punch Filtering**: Configurable cutoff (`SYNC_FROM_DATE`) to sync only live/onward punches.
- **Production-Ready Logging**: Rotating log file with automatic 5MB rotation.

---

## 🛠️ Deploy to Render

1. Create a new **Web Service** on [Render](https://render.com/).
2. Connect this repository: `zordial-dev/attendance_easytime`.
3. Configure the build & start settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
4. Set Environment Variables:
   - `ZOHO_CLIENT_ID`: Your Zoho Client ID
   - `ZOHO_CLIENT_SECRET`: Your Zoho Client Secret
   - `ZOHO_REFRESH_TOKEN`: Your Zoho Refresh Token
   - `SYNC_FROM_DATE`: `today` (or specific timestamp)
5. Click **Deploy**.

---

## ⚙️ EasyTimePro Configuration

1. In **EasyTimePro** Web Panel -> **System Settings** -> **Integration / API Settings**.
2. Set the Webhook/Push URL to your live Render URL:
   ```text
   https://<your-render-app-name>.onrender.com/
   ```
3. Save settings.
