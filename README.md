# Auto-Nickname & Attendance Bot

A Discord bot that automatically adds a stylized suffix `[𝙼𝚂𝚄𝚊𝚗]` to users' nicknames and manages staff attendance.

## Features

### Auto-Nickname
- **Auto-Suffix**: Adds `[𝙼𝚂𝚄𝚊𝚗]` to new members or when they receive a role.
- **Suffix Removal**: Removes the suffix when a user loses their roles.
- **Commands**:
  - `!nick <Name>`: Users can set their own nickname (suffix added automatically).
  - `!nick remove`: Users can remove the suffix.
  - `!setnick @User <Name>`: (Admin) Manually set a user's nickname with suffix.

### Attendance System
- **Mark Present**: Users type `present` in any channel to mark themselves present.
- **Mark Absent/Excused**: Admins can mark users as absent or excused.
- **Role Management**: Automatically assigns roles for Present, Absent, and Excused statuses (and removes conflicting roles).
- **24-Hour Expiry**: Attendance roles and records are automatically cleared after 24 hours.
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

## Commands Reference

| Command | Permission | Description |
| :--- | :--- | :--- |
| `!nick <Name>` | Everyone | Change your own nickname. |
| `!nick remove` | Everyone | Remove the suffix from your name. |
| `!setnick @User <Name>` | Manage Nicknames | Change another user's nickname. |
| `!assignrole @Role` | Manage Roles | Set the role for "Present" status. |
| `!absentrole @Role` | Manage Roles | Set the role for "Absent" status. |
| `!excuserole @Role` | Manage Roles | Set the role for "Excused" status. |
| `!absent @User` | Manage Roles | Mark a user as Absent. |
| `!excuse @User` | Manage Roles | Mark a user as Excused. |
| `!attendance` | Everyone | View the current attendance list. |
