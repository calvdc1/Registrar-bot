# Auto-Nickname & Attendance Bot

A Discord bot that automatically adds a stylized suffix `[𝙼𝚂𝚄𝚊𝚗]` to users' nicknames and manages staff attendance.

## Features

### Auto-Nickname
- **Manual Control**: Users can set their own nickname with the suffix using commands.
- **Suffix Removal**: Users can remove the suffix if desired.
- **Commands**:
  - `!nick <Name>`: Users can set their own nickname (suffix added automatically).
  - `!nick remove`: Users can remove the suffix.
  - `!setnick @User <Name>`: (Admin) Manually set a user's nickname with suffix.

### Attendance System
- **Mark Present**: Users type `present` or use `!present` to mark themselves present.
- **Access Control**: Restrict who can mark attendance using `!setpermitrole`.
- **Mark Absent/Excused**: Admins can mark users as absent or excused.
- **Role Management**: Automatically assigns roles for Present, Absent, and Excused statuses.
- **12-Hour Expiry**: Attendance roles and records are automatically cleared after 12 hours.
- **View Lists**: View a report of who is Present, Absent, and Excused.

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

3. **Run the Bot**:
   ```bash
   python bot.py
   ```

## Attendance Configuration

First, set up the roles you want to use:
1. **Present Role**: `!assignrole @PresentRole`
2. **Absent Role**: `!absentrole @AbsentRole`
3. **Excused Role**: `!excuserole @ExcusedRole`
4. **(Optional) Restrict Access**: `!setpermitrole @Role` (Only allow this role to mark present)

## Interactive Configuration (New!)
Use the `!settings` command to open an interactive dashboard where you can configure:
- **System**: Debug mode, etc.
- **Auto-Nickname**: Suffix format, auto-add behavior, enforcement.
- **Attendance**: Expiry time (12h/24h/48h), self-marking permission, admin-only excuse.
- **Presence**: Set the bot's "Playing" or "Watching" status.

## Persistent Attendance UI
You can create a permanent "Check-In" message with buttons using:
- `!setup_attendance`: Posts a message with "Mark Present" and "Excused" buttons.

## Logging
The bot automatically logs important events and errors to both the console and a file named `bot.log`. 
- **Console**: Useful for real-time monitoring.
- **bot.log**: Keeps a persistent history of events (ignored by git).

## Commands Reference

| Command | Permission | Description |
| :--- | :--- | :--- |
| `!settings` | Administrator | Open the configuration dashboard. |
| `!setup_attendance` | Administrator | Create a message with attendance buttons. |
| `!nick <Name>` | Everyone | Change your own nickname. |
| `!nick remove` | Everyone | Remove the suffix from your name. |
| `!setnick @User <Name>` | Manage Nicknames | Change another user's nickname. |
| `!present` | Everyone (or Restricted) | Mark yourself as present. |
| `!assignrole @Role` | Manage Roles | Set the role for "Present" status. |
| `!absentrole @Role` | Manage Roles | Set the role for "Absent" status. |
| `!excuserole @Role` | Manage Roles | Set the role for "Excused" status. |
| `!setpermitrole @Role` | Manage Roles | Restrict `!present` to a specific role. |
| `!absent @User` | Manage Roles | Mark a user as Absent. |
| `!excuse @User` | Manage Roles | Mark a user as Excused. |
| `!removepresent @User` | Manage Roles | Reset a user's status so they can mark again. |
| `!attendance` | Everyone | View the current attendance list. |
