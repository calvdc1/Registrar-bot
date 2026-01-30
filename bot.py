import os
import json
import datetime
import asyncio
import logging
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ATTENDANCE_FILE = "attendance_data.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure intents
intents = discord.Intents.default()
intents.members = True  # Required to detect member joins and updates
intents.message_content = True # Required for reading commands

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
SUFFIX = " [𝙼𝚂𝚄𝚊𝚗]"
# Set this to the name of the role that triggers the nickname change
# If None, it will trigger on ANY role change (which might be spammy, so be careful)
TRIGGER_ROLE_NAME = None 

def can_manage_nick(ctx, member):
    """Checks if the bot has permission to change the member's nickname."""
    # Bot cannot change the server owner's nickname
    if member.id == ctx.guild.owner_id:
        return False, "I cannot change the Server Owner's nickname due to Discord's security limitations."
    
    # Bot cannot change nickname of someone with higher or equal role
    if member.top_role >= ctx.guild.me.top_role:
        return False, f"I cannot change {member.display_name}'s nickname because their role ({member.top_role.name}) is higher than or equal to my highest role ({ctx.guild.me.top_role.name}). Please move my role higher in the Server Settings."
        
    return True, None

async def apply_nickname(member):
    """Helper function to apply the nickname suffix."""
    try:
        current_name = member.display_name
        
        # Avoid double tagging if they already have the suffix
        if current_name.endswith(SUFFIX):
            return

        # Truncate original name if necessary to fit the suffix within 32 chars (Discord limit)
        max_name_length = 32 - len(SUFFIX)
        
        if len(current_name) > max_name_length:
            new_nick = current_name[:max_name_length] + SUFFIX
        else:
            new_nick = current_name + SUFFIX
            
        logger.info(f'Attempting to change nickname for {member.name} to {new_nick}')
        await member.edit(nick=new_nick)
        logger.info(f'Successfully changed nickname for {member.name} to {new_nick}')
        
    except discord.Forbidden:
        logger.warning(f"Failed to change nickname for {member.name}: Missing Permissions (Check role hierarchy)")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

async def remove_nickname(member):
    """Helper function to remove the nickname suffix."""
    try:
        current_name = member.display_name
        
        # Only attempt removal if the suffix exists
        if current_name.endswith(SUFFIX):
            new_nick = current_name[:-len(SUFFIX)]
            
            # If the name becomes empty (edge case), don't change it or revert to name
            if not new_nick.strip():
                new_nick = member.name
            
            logger.info(f'Attempting to remove nickname suffix for {member.name} to {new_nick}')
            await member.edit(nick=new_nick)
            logger.info(f'Successfully removed nickname suffix for {member.name}')
            
    except discord.Forbidden:
        logger.warning(f"Failed to remove nickname for {member.name}: Missing Permissions (Check role hierarchy)")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


@bot.event
async def on_member_join(member):
    logger.info(f"Member joined: {member.name}")
    # Auto-nickname disabled by request
    # await apply_nickname(member)

@bot.event
async def on_member_update(before, after):
    # Auto-nickname disabled by request
    pass
    # Check if roles have changed
    # if len(before.roles) < len(after.roles):
    #     # A role was added
    #     new_roles = [role for role in after.roles if role not in before.roles]
    #     for role in new_roles:
    #         print(f"User {after.name} received role: {role.name}")
            
    #         if TRIGGER_ROLE_NAME:
    #             if role.name == TRIGGER_ROLE_NAME:
    #                 await apply_nickname(after)
    #         else:
    #             await apply_nickname(after)

    # elif len(before.roles) > len(after.roles):
    #     # A role was removed
    #     removed_roles = [role for role in before.roles if role not in after.roles]
    #     for role in removed_roles:
    #         print(f"User {after.name} lost role: {role.name}")
            
    #         if TRIGGER_ROLE_NAME:
    #             if role.name == TRIGGER_ROLE_NAME:
    #                 await remove_nickname(after)
    #         else:
    #             if len(after.roles) <= 1:
    #                  await remove_nickname(after)

@bot.command(name='setnick')
@commands.has_permissions(manage_nicknames=True)
async def set_nickname(ctx, member: discord.Member, *, new_name: str):
    """
    Manually sets a user's nickname and appends the suffix.
    Usage: !setnick @Member NewName
    """
    # Check hierarchy first
    allowed, message = can_manage_nick(ctx, member)
    if not allowed:
        await ctx.send(f"Failed: {message}")
        return

    try:
        # Check if the suffix is already in the provided name, if not, append it
        if not new_name.endswith(SUFFIX):
             # Truncate if necessary
            max_name_length = 32 - len(SUFFIX)
            if len(new_name) > max_name_length:
                new_nick = new_name[:max_name_length] + SUFFIX
            else:
                new_nick = new_name + SUFFIX
        else:
            new_nick = new_name
            
        await member.edit(nick=new_nick)
        await ctx.send(f"Successfully changed nickname for {member.mention} to `{new_nick}`")
        
    except discord.Forbidden:
        await ctx.send("Failed: I don't have permission to change that user's nickname. (Unexpected Forbidden error)")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@set_nickname.error
async def set_nickname_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!setnick @Member New Name`")

@bot.command(name='nick')
async def nick(ctx, *, name: str = None):
    """
    Sets your own nickname with the suffix.
    Usage: !nick NewName
    Usage: !nick remove (to remove the suffix)
    """
    logger.info(f"Command !nick triggered by {ctx.author}")
    member = ctx.author
    
    if name is None:
        await ctx.send("Usage: Type `!nick YourName` to change your nickname, or `!nick remove` to remove the suffix.")
        return

    if name.lower() == "remove":
        # Check hierarchy first
        allowed, message = can_manage_nick(ctx, member)
        if not allowed:
            await ctx.send(f"Failed: {message}")
            return
            
        await remove_nickname(member)
        await ctx.send(f"Nickname suffix removed for {member.mention}.")
    else:
        try:
            # Check hierarchy first
            allowed, message = can_manage_nick(ctx, member)
            if not allowed:
                await ctx.send(f"Failed: {message}")
                return

            # Check if the suffix is already in the provided name, if not, append it
            if not name.endswith(SUFFIX):
                 # Truncate if necessary
                max_name_length = 32 - len(SUFFIX)
                if len(name) > max_name_length:
                    new_nick = name[:max_name_length] + SUFFIX
                else:
                    new_nick = name + SUFFIX
            else:
                new_nick = name
                
            logger.info(f"Changing nickname for {member} to {new_nick}")
            await member.edit(nick=new_nick)
            await ctx.send(f"Successfully changed nickname for {member.mention} to `{new_nick}`")
            
        except discord.Forbidden:
            logger.warning("Forbidden: Cannot change nickname.")
            await ctx.send("Failed: I don't have permission to change your nickname. Ensure my role is higher than yours in the server settings.")
        except Exception as e:
            logger.error(f"Error in !nick: {e}")
            await ctx.send(f"An error occurred: {e}")

@nick.error
async def nick_error(ctx, error):
    # MissingRequiredArgument is now handled inside the command function
    pass

# --- Attendance Logic ---

def load_attendance_data():
    try:
        with open(ATTENDANCE_FILE, 'r') as f:
            data = json.load(f)
            # Migration check: if 'records' contains strings (old format), convert them
            records = data.get('records', {})
            new_records = {}
            for uid, val in records.items():
                if isinstance(val, str):
                    # Old format: "timestamp" -> New format: {"status": "present", "timestamp": "timestamp"}
                    new_records[uid] = {"status": "present", "timestamp": val}
                else:
                    new_records[uid] = val
            data['records'] = new_records
            return data
            
    except FileNotFoundError:
        return {"attendance_role_id": None, "absent_role_id": None, "excused_role_id": None, "welcome_channel_id": None, "records": {}}
    except json.JSONDecodeError:
        return {"attendance_role_id": None, "absent_role_id": None, "excused_role_id": None, "welcome_channel_id": None, "records": {}}

def save_attendance_data(data):
    with open(ATTENDANCE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@bot.command(name='presentrole', aliases=['assignrole'])
@commands.has_permissions(manage_roles=True)
async def assign_attendance_role(ctx, role: discord.Role):
    """
    Sets the role that users receive when they say 'present'.
    Usage: !presentrole @Role (or !assignrole @Role)
    """
    data = load_attendance_data()
    data['attendance_role_id'] = role.id
    save_attendance_data(data)
    await ctx.send(f"Attendance role has been set to {role.mention}. Users who say 'present' will now receive this role for 12 hours.")

@bot.command(name='absentrole')
@commands.has_permissions(manage_roles=True)
async def assign_absent_role(ctx, role: discord.Role):
    """
    Sets the role that users receive when marked as absent.
    Usage: !absentrole @Role
    """
    data = load_attendance_data()
    data['absent_role_id'] = role.id
    save_attendance_data(data)
    await ctx.send(f"Absent role has been set to {role.mention}.")

@bot.command(name='excuserole')
@commands.has_permissions(manage_roles=True)
async def assign_excused_role(ctx, role: discord.Role):
    """
    Sets the role that users receive when marked as excused.
    Usage: !excuserole @Role
    """
    data = load_attendance_data()
    data['excused_role_id'] = role.id
    save_attendance_data(data)
    await ctx.send(f"Excused role has been set to {role.mention}.")


async def update_user_status(ctx, member, status):
    data = load_attendance_data()
    
    # Get all role IDs
    present_role_id = data.get('attendance_role_id')
    absent_role_id = data.get('absent_role_id')
    excused_role_id = data.get('excused_role_id')
    
    target_role_id = None
    roles_to_remove = []
    
    if status == 'present':
        target_role_id = present_role_id
        if absent_role_id: roles_to_remove.append(absent_role_id)
        if excused_role_id: roles_to_remove.append(excused_role_id)
    elif status == 'absent':
        target_role_id = absent_role_id
        if present_role_id: roles_to_remove.append(present_role_id)
        if excused_role_id: roles_to_remove.append(excused_role_id)
    elif status == 'excused':
        target_role_id = excused_role_id
        if present_role_id: roles_to_remove.append(present_role_id)
        if absent_role_id: roles_to_remove.append(absent_role_id)
        
    # Remove conflicting roles
    for rid in roles_to_remove:
        role = ctx.guild.get_role(rid)
        if role and role in member.roles:
            try:
                await member.remove_roles(role)
            except discord.Forbidden:
                await ctx.send(f"Warning: Could not remove role {role.name} from {member.display_name} (Missing Permissions)")

    # Add new role
    if target_role_id:
        role = ctx.guild.get_role(target_role_id)
        if role:
            try:
                await member.add_roles(role)
                await ctx.send(f"Marked {member.mention} as **{status.upper()}** and gave them the {role.name} role.")
            except discord.Forbidden:
                await ctx.send(f"Failed to give {status} role to {member.display_name} (Missing Permissions)")
        else:
             await ctx.send(f"Marked {member.mention} as **{status.upper()}**, but the role for this status is not configured or deleted.")
    else:
        await ctx.send(f"Marked {member.mention} as **{status.upper()}**. (No role configured for this status)")

    # Update JSON
    user_id = str(member.id)
    if 'records' not in data:
        data['records'] = {}
    
    data['records'][user_id] = {
        "status": status,
        "timestamp": datetime.datetime.now().isoformat()
    }
    save_attendance_data(data)

@bot.command(name='setpermitrole', aliases=['allowrole'])
@commands.has_permissions(manage_roles=True)
async def set_permit_role(ctx, role: discord.Role = None):
    """
    Sets the role required to use the 'present' command.
    Usage: !setpermitrole @Role
    Usage: !setpermitrole (to reset/allow everyone)
    """
    data = load_attendance_data()
    if role:
        data['allowed_role_id'] = role.id
        await ctx.send(f"Permission Updated: Only users with the {role.mention} role can mark attendance.")
    else:
        data['allowed_role_id'] = None
        await ctx.send("Permission Updated: Everyone can now mark attendance.")
    
    save_attendance_data(data)

@bot.command(name='present')
async def mark_present(ctx, member: discord.Member = None):
    """
    Marks a user as present.
    Usage: !present (for yourself)
    Usage: !present @User (requires Manage Roles)
    """
    if member is None:
        member = ctx.author

    # Check for required role if marking self
    if member == ctx.author:
        data = load_attendance_data()
        allowed_role_id = data.get('allowed_role_id')
        if allowed_role_id:
            allowed_role = ctx.guild.get_role(allowed_role_id)
            if allowed_role and allowed_role not in ctx.author.roles:
                await ctx.send(f"You need the {allowed_role.mention} role to mark attendance.")
                return

    if member != ctx.author and not ctx.author.guild_permissions.manage_roles:
        await ctx.send("You do not have permission to mark others as present.")
        return

    await update_user_status(ctx, member, 'present')

@bot.command(name='absent')
@commands.has_permissions(manage_roles=True)
async def mark_absent(ctx, member: discord.Member):
    """
    Marks a user as absent.
    Usage: !absent @User
    """
    await update_user_status(ctx, member, 'absent')

@bot.command(name='excuse')
@commands.has_permissions(manage_roles=True)
async def mark_excuse(ctx, member: discord.Member):
    """
    Marks a user as excused.
    Usage: !excuse @User
    """
    await update_user_status(ctx, member, 'excused')

def create_attendance_embed(guild):
    data = load_attendance_data()
    records = data.get('records', {})
    
    present_list = []
    absent_list = []
    excused_list = []
    
    # Filter for active records
    for uid, info in records.items():
        # Handle migration fallback just in case
        if isinstance(info, str):
            info = {"status": "present", "timestamp": info}
            
        status = info.get('status', 'present')
        member = guild.get_member(int(uid))
        name = member.display_name if member else f"Unknown User ({uid})"
        
        if status == 'present':
            present_list.append(name)
        elif status == 'absent':
            absent_list.append(name)
        elif status == 'excused':
            excused_list.append(name)
            
    # Philippines Time (UTC+8)
    ph_tz = datetime.timezone(datetime.timedelta(hours=8))
    now_ph = datetime.datetime.now(ph_tz)

    embed = discord.Embed(title=f"Attendance Report - {now_ph.strftime('%B %d, %Y')}", color=discord.Color.blue())
    embed.add_field(name=f"✅ Present ({len(present_list)})", value="\n".join(present_list) if present_list else "None", inline=False)
    embed.add_field(name=f"❌ Absent ({len(absent_list)})", value="\n".join(absent_list) if absent_list else "None", inline=False)
    embed.add_field(name=f"⚠️ Excused ({len(excused_list)})", value="\n".join(excused_list) if excused_list else "None", inline=False)
    embed.set_footer(text=f"Generated at {now_ph.strftime('%I:%M %p')} (PHT)")
    
    return embed

@bot.command(name='removepresent')
@commands.has_permissions(manage_roles=True)
async def remove_present(ctx, member: discord.Member):
    """
    Removes a user's present status/role so they can mark attendance again.
    Usage: !removepresent @User
    """
    data = load_attendance_data()
    role_id = data.get('attendance_role_id')
    user_id = str(member.id)
    
    # Remove from records
    if 'records' in data and user_id in data['records']:
        del data['records'][user_id]
        save_attendance_data(data)
    
    # Remove role
    if role_id:
        role = ctx.guild.get_role(role_id)
        if role and role in member.roles:
            try:
                await member.remove_roles(role)
            except discord.Forbidden:
                await ctx.send("Warning: Could not remove role (Missing Permissions).")
                
    await ctx.send(f"Reset attendance for {member.mention}. They can now say 'present' again.")

@bot.command(name='attendance')
async def view_attendance(ctx):
    """
    View the current attendance lists.
    Usage: !attendance
    """
    embed = create_attendance_embed(ctx.guild)
    await ctx.send(embed=embed)

@assign_attendance_role.error
async def assign_role_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!assignrole @Role`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid role. Please ping a valid role.")

@tasks.loop(minutes=1)
async def check_attendance_expiry():
    data = load_attendance_data()
    records = data.get('records', {})
    
    # Get all role IDs
    role_map = {
        'present': data.get('attendance_role_id'),
        'absent': data.get('absent_role_id'),
        'excused': data.get('excused_role_id')
    }

    now = datetime.datetime.now()
    users_to_remove = []
    
    # Iterate over guilds
    for guild in bot.guilds:
        for user_id_str, info in records.items():
            # Handle migration/fallback
            if isinstance(info, str):
                info = {"status": "present", "timestamp": info}
            
            timestamp_str = info.get('timestamp')
            status = info.get('status', 'present')
            role_id = role_map.get(status)

            if not timestamp_str:
                users_to_remove.append(user_id_str)
                continue

            try:
                # Handle ISO format
                # Be robust to non-string timestamps by coercing to string
                timestamp = datetime.datetime.fromisoformat(str(timestamp_str))
                
                # Check if 12 hours have passed
                if now - timestamp > datetime.timedelta(hours=12):
                    user_id = int(user_id_str)
                    member = guild.get_member(user_id)
                    
                    if member and role_id:
                        role = guild.get_role(role_id)
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(role)
                                logger.info(f"Removed {status} role from {member.name} (expired)")
                            except discord.Forbidden:
                                logger.warning(f"Failed to remove role from {member.name}: Missing Permissions")
                    
                    # Mark for removal from records
                    users_to_remove.append(user_id_str)
                    
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing timestamp for user {user_id_str}: {e}")
                users_to_remove.append(user_id_str)

    if users_to_remove:
        # Remove duplicates
        users_to_remove = list(set(users_to_remove))
        for uid in users_to_remove:
            if uid in data['records']:
                del data['records'][uid]
        save_attendance_data(data)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}')
    logger.info('Bot is ready to auto-nickname users!')
    if not check_attendance_expiry.is_running():
        check_attendance_expiry.start()

@bot.event
async def on_message(message):
    # Don't let the bot reply to itself
    if message.author == bot.user:
        return

    # Process commands first (important!)
    await bot.process_commands(message)

    # Attendance check logic
    if message.content.strip().lower() == "present":
        data = load_attendance_data()
        
        # Check permissions
        allowed_role_id = data.get('allowed_role_id')
        if allowed_role_id:
            allowed_role = message.guild.get_role(allowed_role_id)
            if allowed_role and allowed_role not in message.author.roles:
                # Silently ignore or maybe react with ❌? 
                # Better to ignore to prevent spam if they don't have perms.
                return

        attendance_role_id = data.get('attendance_role_id')
        absent_role_id = data.get('absent_role_id')
        excused_role_id = data.get('excused_role_id')

        if attendance_role_id:
            role = message.guild.get_role(attendance_role_id)
            if role:
                user_id = str(message.author.id)
                now = datetime.datetime.now()
                
                # Check if already marked today (prevent spamming present)
                # We check if they HAVE the role already as a proxy for "already present"
                if role in message.author.roles:
                     # Check if it was marked today to give specific feedback, 
                     # but mainly we just don't do anything if they have the role.
                     # Or we can just remind them.
                     await message.channel.send(f"{message.author.mention}, you have already marked your attendance!", delete_after=5)
                else:
                    # Give role
                    try:
                        # Remove conflicting roles first
                        roles_to_remove = []
                        if absent_role_id: roles_to_remove.append(absent_role_id)
                        if excused_role_id: roles_to_remove.append(excused_role_id)
                        
                        for rid in roles_to_remove:
                            r = message.guild.get_role(rid)
                            if r and r in message.author.roles:
                                await message.author.remove_roles(r)

                        await message.author.add_roles(role)
                        await message.add_reaction("✅")
                        
                        # Update record with FULL timestamp for 24h expiry
                        if 'records' not in data:
                            data['records'] = {}
                        data['records'][user_id] = {
                            "status": "present",
                            "timestamp": now.isoformat()
                        }
                        save_attendance_data(data)
                        
                        await message.channel.send(f"Attendance marked for {message.author.mention}! You have been given the {role.name} role.", delete_after=10)
                        
                        # Automatically show the attendance report
                        embed = create_attendance_embed(message.guild)
                        await message.channel.send(embed=embed)
                    except discord.Forbidden:
                        await message.channel.send("I tried to give you the role, but I don't have permission! Please check my role hierarchy.")

    elif message.content.strip().lower() == "excuse":
        data = load_attendance_data()
        attendance_role_id = data.get('attendance_role_id')
        absent_role_id = data.get('absent_role_id')
        excused_role_id = data.get('excused_role_id')

        if excused_role_id:
            role = message.guild.get_role(excused_role_id)
            if role:
                user_id = str(message.author.id)
                now = datetime.datetime.now()
                
                # Check if already marked (prevent spamming)
                if role in message.author.roles:
                     await message.channel.send(f"{message.author.mention}, you have already marked your status as excused!", delete_after=5)
                else:
                    # Give role
                    try:
                        # Remove conflicting roles first
                        roles_to_remove = []
                        if attendance_role_id: roles_to_remove.append(attendance_role_id)
                        if absent_role_id: roles_to_remove.append(absent_role_id)
                        
                        for rid in roles_to_remove:
                            r = message.guild.get_role(rid)
                            if r and r in message.author.roles:
                                await message.author.remove_roles(r)

                        await message.author.add_roles(role)
                        await message.add_reaction("✅")
                        
                        # Update record with FULL timestamp for 24h expiry
                        if 'records' not in data:
                            data['records'] = {}
                        data['records'][user_id] = {
                            "status": "excused",
                            "timestamp": now.isoformat()
                        }
                        save_attendance_data(data)
                        
                        await message.channel.send(f"Excused status marked for {message.author.mention}! You have been given the {role.name} role.", delete_after=10)
                        
                        # Automatically show the attendance report
                        embed = create_attendance_embed(message.guild)
                        await message.channel.send(embed=embed)
                    except discord.Forbidden:
                        await message.channel.send("I tried to give you the role, but I don't have permission! Please check my role hierarchy.")


if __name__ == "__main__":
    if not TOKEN or TOKEN == "your_token_here":
        print("Error: Please set your DISCORD_TOKEN in the .env file.")
    else:
        keep_alive()
        bot.run(TOKEN)
