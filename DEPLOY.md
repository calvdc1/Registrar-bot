# How to Host Your Bot 24/7 for Free

To keep your bot running 24/7 without your computer being on, you need to host it on a cloud server. Here is the easiest free method using **Render**.

## Prerequisites
- A [Render.com](https://render.com) account.
- A [GitHub](https://github.com) account.
- Your Discord Bot Token.

## Deployment Steps

1. **Fork/Clone this Repository**: Ensure you have this code in your own GitHub repository.
2. **Create a New Web Service on Render**:
   - Go to your Render Dashboard.
   - Click **New +** -> **Web Service**.
   - Connect your GitHub repository.
3. **Configure the Service**:
   - **Name**: Give your bot a name.
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: Free
4. **Environment Variables**:
   - Scroll down to "Environment Variables".
   - Add Key: `DISCORD_TOKEN`
   - Value: (Paste your actual bot token here)
   - Add Key: `PYTHON_VERSION` (Optional, code handles this via .python-version file now)
   - Value: `3.10.12`
5. **Deploy**: Click **Create Web Service**.

## Troubleshooting
- **Bot not starting?** Check the "Logs" tab in Render.
- **"Invalid Syntax"?** Ensure Render is using Python 3.10+ (The included `.python-version` file should handle this).
- **Attendance not saving?** On the free tier, files are not persistent. Settings will reset if the bot restarts.

---

## Prevent "Sleeping" (Important)
Free servers go to sleep after 15 minutes of inactivity. To keep it awake 24/7:

1. Go to [UptimeRobot.com](https://uptimerobot.com/) and create a free account.
2. Click **"Add New Monitor"**.
3. **Monitor Type:** Select `HTTP(s)`.
4. **Friendly Name:** `My Discord Bot`.
5. **URL (or IP):** Paste the Render App URL you copied earlier.
6. **Monitoring Interval:** Set to `5 minutes`.
7. Click **"Create Monitor"**.

Now UptimeRobot will "ping" your bot every 5 minutes, ensuring it never goes to sleep.

## How to Update/Redeploy
When you make changes to your code (like the recent timezone update):

1. **Save** your files.
2. **Push** your changes to GitHub.
3. **Render** will automatically detect the new code and start redeploying within a minute.
4. You can check the progress in the "Events" or "Logs" tab on your Render dashboard.

If it doesn't deploy automatically:
1. Go to your service on Render.
2. Click the **"Manual Deploy"** button.
3. Select **"Deploy latest commit"**.
