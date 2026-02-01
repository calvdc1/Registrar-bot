# Auto-Nickname & Attendance Bot

A Discord bot that automatically adds a stylized suffix `[𝙼𝚂𝚄𝚊𝚗]` to users' nicknames and manages staff attendance with advanced tracking, time windows, and persistent reporting.

## Features

### 📝 Auto-Nickname
- **Manual Control**: Users can set their own nickname with the suffix using commands.
- **Suffix Removal**: Users can remove the suffix if desired.
- **Enforcement**: Option to enforce suffix on all users or specific roles.

### 📅 Attendance System
- **Flexible Modes**: 
  - **Duration Mode**: Attendance expires after 12/24/48 hours.
  - **Window Mode**: Attendance is only allowed during specific hours (e.g., 8am - 5pm).
- **Mark Present**: Users type `present` or use `!present` to mark themselves present.
- **Access Control**: Restrict who can mark attendance using `!setpermitrole`.
- **Mark Absent/Excused**: Admins can mark users as absent or excused with reasons.
- **Role Management**: Automatically assigns roles for Present, Absent, and Excused statuses.
- **Persistent Reports**: Live-updating attendance report in a designated channel.
- **Auto-Absence**: Automatically marks users as absent if they miss the time window (Window Mode).
- **Persistent Storage**: All data is saved to a database, preventing data loss on restarts.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file with your token:
   ```
   DISCORD_TOKEN=your_token_here
   ```
   *(Optional)* Set `DB_FILE` to specify database location (default: `attendance.db`).

3. **Run the Bot**:
   ```bash
   python bot.py
   ```

## Quick Start Configuration

1. **Set up Roles**:
   ```
   !assignrole @PresentRole
   !absentrole @AbsentRole
   !excuserole @ExcusedRole
   ```
2. **Set Attendance Channel**:
   ```
   !assignchannel #attendance-reports
   ```
3. **Configure Time Window (Optional)**:
   ```
   !settime 8:00am - 5:00pm
   ```

## Interactive Dashboard
Use `!settings` to open the interactive configuration panel. You can toggle:
- Debug Mode
- Auto-Nickname Rules (Auto-add, Enforce)
- Attendance Settings (Self-marking, Admin-only excuse)
- Bot Presence (Status text)

## Commands Reference

### 👤 User Commands
| Command | Description |
| :--- | :--- |
| `!present` | Mark yourself as present. |
| `!nick <Name>` | Change your nickname (suffix added automatically). |
| `!nick remove` | Remove the suffix from your name. |
| `!attendance` | View the current attendance list/report. |
| `!ping` | Check if the bot is responsive. |

### 🛠️ Management Commands (Staff/Admin)
| Command | Permission | Description |
| :--- | :--- | :--- |
| `!present @User` | Manage Roles | Manually mark another user as present. |
| `!absent @User` | Manage Roles | Mark a user as Absent. |
| `!excuse @User <Reason>` | Manage Roles | Mark a user as Excused with a reason. |
| `!removepresent @User` | Manage Roles | Remove a user's status so they can mark again. |
| `!setnick @User <Name>` | Manage Nicknames | Change another user's nickname. |

### ⚙️ Configuration Commands (Admin)
| Command | Description |
| :--- | :--- |
| `!settings` | Open the interactive settings dashboard. |
| `!settime <Start> - <End>` | Set attendance window (e.g., `!settime 8am - 5pm`). **Note:** Uses Philippines Time (UTC+8). |
| `!assignchannel #channel` | Set the channel for live attendance reports. |
| `!setup_attendance` | Create a persistent "Check-In" message with buttons. |

### 🛡️ Role Setup Commands (Admin)
| Command | Description |
| :--- | :--- |
| `!assignrole @Role` | Set the role given for "Present" status. |
| `!absentrole @Role` | Set the role given for "Absent" status. |
| `!excuserole @Role` | Set the role given for "Excused" status. |
| `!setpermitrole @Role` | Restrict `!present` command to a specific role. |
| `!resetpermitrole` | Remove the permitted role from all users who have it. |
| `!reset @Role` | Remove a specific role from all users who have it. |

### ⚠️ System Commands (Admin)
| Command | Description |
| :--- | :--- |
| `!restartattendance` | **Full Reset**: Clears all records, removes roles, and resets settings. (Alias: `!resetattendance`) |

## Deployment (Render)

This bot is configured for deployment on Render.
See [DEPLOY.md](DEPLOY.md) for detailed instructions.

**Key Requirements:**
- Use a **Persistent Disk** mounted at `/data` to save the database (`attendance.db`).
- Set `DB_FILE` environment variable to `/data/attendance.db`.
