# How to Host Your Bot 24/7 for Free

To keep your bot running 24/7 without your computer being on, you need to host it on a cloud server. Here is the easiest free method using **Render**.

## Option 1: Render (Recommended)

1.  **Upload to GitHub**
    *   Create a GitHub account if you don't have one.
    *   Create a new repository (name it `autonickname-bot`).
    *   Upload all the files in this folder to that repository (or push them using Git).
    *   *Note: Do NOT upload your `.env` file containing the token for security reasons.*

2.  **Create Account on Render**
    *   Go to [render.com](https://render.com) and sign up (you can login with GitHub).

3.  **Create a Web Service**
    *   Click **"New +"** and select **"Web Service"**.
    *   Connect your GitHub repository.
    *   **Name:** Give it a name (e.g., `my-discord-bot`).
    *   **Runtime:** Select **Python 3**.
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `python bot.py`
    *   **Free Plan:** Select the "Free" instance type.

4.  **Add Environment Variables**
    *   Scroll down to the **"Environment Variables"** section.
    *   Click **"Add Environment Variable"**.
    *   **Key:** `DISCORD_TOKEN`
    *   **Value:** (Paste your actual Discord Bot Token here, from your `.env` file)
    *   *Note: If you have other variables like `TRIGGER_ROLE_NAME`, add them here too.*

5.  **Deploy**
    *   Click **"Create Web Service"**.
    *   Render will start building and deploying your bot.
    *   Once it says "Live", your bot is online 24/7!

## Important Note on "Sleeping"
Free hosting plans sometimes "sleep" if they don't receive web traffic.
- Since we added `keep_alive.py`, your bot runs a small web server.
- To prevent sleeping, you can use a free service like **UptimeRobot** to ping your bot's website URL (which Render provides, e.g., `https://my-discord-bot.onrender.com`) every 5 minutes.
