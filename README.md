# EasyTimePro & ZKTeco to Zoho People Attendance Middleware

Real-time biometric attendance connector bridging **ZKTeco Biometric Devices** / **EasyTimePro** and **Zoho People**.

## 🚀 Features
- **Dual-Mode Integration**:
  - **Option 1 (Direct ZKTeco Biometric Machine)**: Connects directly to ZKTeco hardware via ADMS push protocol (`/iclock/cdata`). **No local laptop or PC required!**
  - **Option 2 (EasyTimePro Webhook)**: Ingests webhook pushes from local EasyTimePro software.
- **Biometric ID Mapping (`mapId`)**: Automatically syncs punches using biometric user IDs (`EMP_CODE`) to Zoho People Employee Profiles.
- **Zoho OAuth Token Management**: Automatically generates, caches, and refreshes OAuth tokens with scope `ZOHOPEOPLE.attendance.ALL`.
- **Threaded Concurrency**: Multi-threaded request handling prevents connection drops during heavy punch bursts.
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
   - `ZOHO_DOMAIN`: `in` (or `com`, `eu`)
5. Click **Deploy**.

---

## ⚙️ Option 1: Direct ZKTeco Machine Setup (No Laptop Needed!)

1. On the physical ZKTeco device screen, press **M/OK** to enter the Menu.
2. Navigate to **Comm.** (Communication) -> **Cloud Server Setting** (or **ADMS** / **Web Server**).
3. Configure:
   - **Server Address**: `attendance-easytime-1.onrender.com` (without `https://`)
   - **Server Port**: `443` (for HTTPS)
   - **Enable Domain Name**: `ON` (Yes)
   - **Enable Proxy Server**: `OFF`
4. Save and restart the device if prompted.
5. Once connected, punches will upload directly to your Render server and sync straight to Zoho People!

---

## ⚙️ Option 2: EasyTimePro Webhook Setup

1. In **EasyTimePro** Web Panel -> **System Settings** -> **Integration / API Settings**.
2. Set the Webhook/Push URL to your live Render URL:
   ```text
   https://attendance-easytime-1.onrender.com/
   ```
3. Save settings.

