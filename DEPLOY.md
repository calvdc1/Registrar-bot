# How to Host Your Bot 24/7 for Free

To keep your bot running 24/7 without your computer being on, you need to host it on a cloud server. Here is the easiest free method using **Render**.

## Prerequisites
Ensure you have uploaded these 5 files to your GitHub repository:
1. `bot.py`
2. `requirements.txt`
3. `keep_alive.py`
4. `Procfile`
5. `attendance_data.json`

*(Do NOT upload `.env`)*

## Step-by-Step Guide

### 1. Create Account on Render
1. Go to [dashboard.render.com](https://dashboard.render.com/register).
2. Sign up using your **GitHub** account (this makes it easier to link your code).

### 2. Create a Web Service
1. On the dashboard, click the **"New +"** button (top right).
2. Select **"Web Service"**.
3. Click **"Build and deploy from a Git repository"**.
4. You should see your `autonickname-bot` repository in the list. Click **"Connect"**.

### 3. Configure the Service
Fill in the form with these exact settings:

| Setting | Value |
| :--- | :--- |
| **Name** | `autonickname-bot` (or any name you like) |
| **Region** | Choose the one closest to you (e.g., Singapore, Oregon) |
| **Branch** | `main` |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python bot.py` |
| **Instance Type** | **Free** ($0/month) |

### 4. Add Your Password (Token)
1. Scroll down to the **"Environment Variables"** section.
2. Click **"Add Environment Variable"**.
3. Enter these details:
   - **Key:** `DISCORD_TOKEN`
   - **Value:** *(Copy the token from your `.env` file and paste it here)*
4. Click **"Create Web Service"**.

### 5. Wait for Deployment
- Render will now download your code and install dependencies.
- Watch the logs window.
- When you see **"Bot is ready to auto-nickname users!"**, your bot is online!
- **Copy your App URL:** It will look like `https://autonickname-bot.onrender.com`. You need this for the next step.

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
