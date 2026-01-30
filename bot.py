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
    settings = load_settings()
    suffix = settings.get("suffix_format", SUFFIX)
    
    try:
        current_name = member.display_name
        
        # Avoid double tagging if they already have the suffix
        if current_name.endswith(suffix):
            return

        # Truncate original name if necessary to fit the suffix within 32 chars (Discord limit)
        max_name_length = 32 - len(suffix)
        
        if len(current_name) > max_name_length:
            new_nick = current_name[:max_name_length] + suffix
        else:
            new_nick = current_name + suffix
            
        logger.info(f'Attempting to change nickname for {member.name} to {new_nick}')
        await member.edit(nick=new_nick)
        logger.info(f'Successfully changed nickname for {member.name} to {new_nick}')
        
    except discord.Forbidden:
        logger.warning(f"Failed to change nickname for {member.name}: Missing Permissions (Check role hierarchy)")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

async def remove_nickname(member):
    """Helper function to remove the nickname suffix."""
    settings = load_settings()
    suffix = settings.get("suffix_format", SUFFIX)
    
    try:
        current_name = member.display_name
        
        # Only attempt removal if the suffix exists
        if current_name.endswith(suffix):
            new_nick = current_name[:-len(suffix)]
            
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
    settings = load_settings()
    if settings.get("auto_nick_on_join", False):
        await apply_nickname(member)

@bot.event
async def on_member_update(before, after):
    settings = load_settings()
    
    # Enforce Suffix
    if settings.get("enforce_suffix", False):
        # Check if nickname changed and suffix was removed
        if before.display_name != after.display_name:
             suffix = settings.get("suffix_format", SUFFIX)
             if not after.display_name.endswith(suffix):
                 await apply_nickname(after)

    # Remove on Role Loss (placeholder logic)
    pass
    # Auto-nickname disabled by request
    # pass
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
            settings = load_settings()
            suffix = settings.get("suffix_format", SUFFIX)
            if not name.endswith(suffix):
                 # Truncate if necessary
                max_name_length = 32 - len(suffix)
                if len(name) > max_name_length:
                    new_nick = name[:max_name_length] + suffix
                else:
                    new_nick = name + suffix
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
        return {"attendance_role_id": None, "absent_role_id": None, "excused_role_id": None, "welcome_channel_id": None, "records": {}, "settings": {}}

def load_settings():
    """Helper to get settings with defaults"""
    data = load_attendance_data()
    defaults = {
        "debug_mode": False,
        "auto_nick_on_join": False,
        "enforce_suffix": False,
        "remove_suffix_on_role_loss": False,
        "attendance_expiry_hours": 24,
        "allow_self_marking": True,
        "require_admin_excuse": True,
        "suffix_format": " [𝙼𝚂𝚄𝚊𝚗]"
    }
    settings = data.get("settings", {})
    # Merge defaults
    for k, v in defaults.items():
        if k not in settings:
            settings[k] = v
    return settings

def save_settings(settings):
    data = load_attendance_data()
    data["settings"] = settings
    save_attendance_data(data)

def save_attendance_data(data):
    with open(ATTENDANCE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Configuration Views ---

class SettingsSelect(discord.ui.Select):
    def __init__(self, bot_instance):
        options = [
            discord.SelectOption(label="System Settings", description="Debug Mode, Sync Commands", emoji="⚙️"),
            discord.SelectOption(label="Auto-Nickname", description="Suffix, Auto-Add, Enforce", emoji="📝"),
            discord.SelectOption(label="Attendance Settings", description="Expiry, Self-Marking, Admin Only", emoji="📅"),
            discord.SelectOption(label="Presence", description="Set Bot Status", emoji="🤖")
        ]
        super().__init__(placeholder="Select a category to configure...", min_values=1, max_values=1, options=options)
        self.bot_instance = bot_instance

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        settings = load_settings()
        
        if category == "System Settings":
            view = SystemSettingsView(settings)
            embed = discord.Embed(title="System Settings", color=discord.Color.blue())
            embed.add_field(name="Debug Mode", value="Enabled" if settings['debug_mode'] else "Disabled")
            await interaction.response.edit_message(embed=embed, view=view)
            
        elif category == "Auto-Nickname":
            view = AutoNickSettingsView(settings)
            embed = discord.Embed(title="Auto-Nickname Configuration", color=discord.Color.green())
            embed.add_field(name="Suffix Format", value=f"`{settings['suffix_format']}`", inline=False)
            embed.add_field(name="Auto-Add on Join", value=str(settings['auto_nick_on_join']))
            embed.add_field(name="Enforce Suffix", value=str(settings['enforce_suffix']))
            embed.add_field(name="Remove on Role Loss", value=str(settings['remove_suffix_on_role_loss']))
            await interaction.response.edit_message(embed=embed, view=view)
            
        elif category == "Attendance Settings":
            view = AttendanceSettingsView(settings)
            embed = discord.Embed(title="Attendance Settings", color=discord.Color.orange())
            embed.add_field(name="Auto-Expiry (Hours)", value=str(settings['attendance_expiry_hours']))
            embed.add_field(name="Allow Self-Marking", value=str(settings['allow_self_marking']))
            embed.add_field(name="Require Admin for Excuse", value=str(settings['require_admin_excuse']))
            await interaction.response.edit_message(embed=embed, view=view)
            
        elif category == "Presence":
            await interaction.response.send_modal(PresenceModal(self.bot_instance))

class PresenceModal(discord.ui.Modal, title="Set Bot Presence"):
    status_type = discord.ui.TextInput(label="Type (playing, watching, listening)", placeholder="playing")
    status_text = discord.ui.TextInput(label="Status Text", placeholder="Managing Attendance")

    def __init__(self, bot_instance):
        super().__init__()
        self.bot_instance = bot_instance

    async def on_submit(self, interaction: discord.Interaction):
        activity_type = discord.ActivityType.playing
        if self.status_type.value.lower() == 'watching':
            activity_type = discord.ActivityType.watching
        elif self.status_type.value.lower() == 'listening':
            activity_type = discord.ActivityType.listening
            
        await self.bot_instance.change_presence(activity=discord.Activity(type=activity_type, name=self.status_text.value))
        await interaction.response.send_message(f"Presence updated to: {self.status_type.value} {self.status_text.value}", ephemeral=True)

class BaseSettingsView(discord.ui.View):
    def __init__(self, settings):
        super().__init__(timeout=180)
        self.settings = settings

    async def update_message(self, interaction, embed):
        save_settings(self.settings)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Back to Main Menu", style=discord.ButtonStyle.secondary, row=4)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=discord.Embed(title="Settings Dashboard", description="Select a category below."), view=MainSettingsView(interaction.client))

class SystemSettingsView(BaseSettingsView):
    @discord.ui.button(label="Toggle Debug Mode", style=discord.ButtonStyle.primary)
    async def toggle_debug(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings['debug_mode'] = not self.settings['debug_mode']
        
        # Apply logging change immediately
        if self.settings['debug_mode']:
            logger.setLevel(logging.DEBUG)
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            logging.getLogger().setLevel(logging.INFO)
            
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="Debug Mode", value="Enabled" if self.settings['debug_mode'] else "Disabled")
        await self.update_message(interaction, embed)

class AutoNickSettingsView(BaseSettingsView):
    @discord.ui.button(label="Toggle Auto-Add on Join", style=discord.ButtonStyle.primary)
    async def toggle_auto_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings['auto_nick_on_join'] = not self.settings['auto_nick_on_join']
        self.update_embed(interaction.message.embeds[0])
        await self.update_message(interaction, interaction.message.embeds[0])

    @discord.ui.button(label="Toggle Enforce Suffix", style=discord.ButtonStyle.primary)
    async def toggle_enforce(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings['enforce_suffix'] = not self.settings['enforce_suffix']
        self.update_embed(interaction.message.embeds[0])
        await self.update_message(interaction, interaction.message.embeds[0])

    @discord.ui.button(label="Toggle Remove on Role Loss", style=discord.ButtonStyle.primary)
    async def toggle_remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings['remove_suffix_on_role_loss'] = not self.settings['remove_suffix_on_role_loss']
        self.update_embed(interaction.message.embeds[0])
        await self.update_message(interaction, interaction.message.embeds[0])

    def update_embed(self, embed):
        embed.set_field_at(1, name="Auto-Add on Join", value=str(self.settings['auto_nick_on_join']))
        embed.set_field_at(2, name="Enforce Suffix", value=str(self.settings['enforce_suffix']))
        embed.set_field_at(3, name="Remove on Role Loss", value=str(self.settings['remove_suffix_on_role_loss']))

class AttendanceSettingsView(BaseSettingsView):
    @discord.ui.button(label="Toggle Self-Marking", style=discord.ButtonStyle.primary)
    async def toggle_self_mark(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings['allow_self_marking'] = not self.settings['allow_self_marking']
        self.update_embed(interaction.message.embeds[0])
        await self.update_message(interaction, interaction.message.embeds[0])

    @discord.ui.button(label="Toggle Admin Only Excuse", style=discord.ButtonStyle.primary)
    async def toggle_admin_excuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.settings['require_admin_excuse'] = not self.settings['require_admin_excuse']
        self.update_embed(interaction.message.embeds[0])
        await self.update_message(interaction, interaction.message.embeds[0])

    @discord.ui.select(placeholder="Select Expiry Time", options=[
        discord.SelectOption(label="12 Hours", value="12"),
        discord.SelectOption(label="24 Hours", value="24"),
        discord.SelectOption(label="48 Hours", value="48")
    ])
    async def select_expiry(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.settings['attendance_expiry_hours'] = int(select.values[0])
        self.update_embed(interaction.message.embeds[0])
        await self.update_message(interaction, interaction.message.embeds[0])

    def update_embed(self, embed):
        embed.set_field_at(0, name="Auto-Expiry (Hours)", value=str(self.settings['attendance_expiry_hours']))
        embed.set_field_at(1, name="Allow Self-Marking", value=str(self.settings['allow_self_marking']))
        embed.set_field_at(2, name="Require Admin for Excuse", value=str(self.settings['require_admin_excuse']))

class MainSettingsView(discord.ui.View):
    def __init__(self, bot_instance):
        super().__init__()
        self.add_item(SettingsSelect(bot_instance))

@bot.command(name='settings', aliases=['panel', 'config'])
@commands.has_permissions(administrator=True)
async def settings_panel(ctx):
    """Opens the interactive settings dashboard."""
    embed = discord.Embed(title="Settings Dashboard", description="Select a category below to configure the bot.", color=discord.Color.blurple())
    await ctx.send(embed=embed, view=MainSettingsView(bot))

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


async def update_user_status(ctx, member, status, reason=None):
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
                msg = f"Marked {member.mention} as **{status.upper()}** and gave them the {role.name} role."
                if reason:
                    msg += f"\nReason: {reason}"
                await ctx.send(msg)
            except discord.Forbidden:
                await ctx.send(f"Failed to give {status} role to {member.display_name} (Missing Permissions)")
        else:
             msg = f"Marked {member.mention} as **{status.upper()}**, but the role for this status is not configured or deleted."
             if reason:
                 msg += f"\nReason: {reason}"
             await ctx.send(msg)
    else:
        msg = f"Marked {member.mention} as **{status.upper()}**. (No role configured for this status)"
        if reason:
            msg += f"\nReason: {reason}"
        await ctx.send(msg)

    # Update JSON
    user_id = str(member.id)
    if 'records' not in data:
        data['records'] = {}
    
    record = {
        "status": status,
        "timestamp": datetime.datetime.now().isoformat(),
        "channel_id": ctx.channel.id
    }
    if reason:
        record["reason"] = reason
        
    data['records'][user_id] = record
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
        settings = load_settings()
        if not settings.get('allow_self_marking', True):
            await ctx.send("Self-marking is currently disabled.")
            return

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
async def mark_excuse(ctx, member: discord.Member, *, reason: str):
    """
    Marks a user as excused with a reason.
    Usage: !excuse @User I was sick
    """
    settings = load_settings()
    if settings.get('require_admin_excuse', True):
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("You do not have permission to excuse users.")
            return

    await update_user_status(ctx, member, 'excused', reason=reason)

@mark_excuse.error
async def mark_excuse_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!excuse @User <reason>` (e.g., `!excuse @John I was sick`)")

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
    settings = data.get("settings", {})
    expiry_hours = settings.get("attendance_expiry_hours", 24) # Default to 24 hours now
    
    records = data.get('records', {})
    
    # Get all role IDs
    role_map = {
        'present': data.get('attendance_role_id'),
        'absent': data.get('absent_role_id'),
        'excused': data.get('excused_role_id')
    }
    ping_role_id = data.get('ping_role_id')

    now = datetime.datetime.now()
    users_to_remove = []
    
    # Iterate over guilds
    for guild in bot.guilds:
        for user_id_str, info in records.items():
            # Handle migration/fallback
            if isinstance(info, str):
                info = {"status": "present", "timestamp": info, "channel_id": None}
            
            timestamp_str = info.get('timestamp')
            status = info.get('status', 'present')
            channel_id = info.get('channel_id')
            role_id = role_map.get(status)

            if not timestamp_str:
                users_to_remove.append(user_id_str)
                continue

            try:
                # Handle ISO format
                # Be robust to non-string timestamps by coercing to string
                timestamp = datetime.datetime.fromisoformat(str(timestamp_str))
                
                # Check if X hours have passed
                if now - timestamp > datetime.timedelta(hours=expiry_hours):
                    user_id = int(user_id_str)
                    member = guild.get_member(user_id)
                    
                    if member and role_id:
                        role = guild.get_role(role_id)
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(role)
                                logger.info(f"Removed {status} role from {member.name} (expired)")
                                
                                # Notification Logic
                                channel = None
                                if channel_id:
                                    channel = guild.get_channel(channel_id)
                                
                                # Fallback channel if specific channel is gone or not recorded
                                if not channel and data.get('welcome_channel_id'):
                                    channel = guild.get_channel(data.get('welcome_channel_id'))
                                    
                                if channel:
                                    msg_content = f"{member.mention}, your attendance session has expired (12 hours)."
                                    
                                    # Ping Notification Role if set
                                    if ping_role_id:
                                        ping_role = guild.get_role(ping_role_id)
                                        if ping_role:
                                            msg_content = f"{ping_role.mention} " + msg_content
                                            
                                    msg_content += f"\nYou are now allowed to say **present** again."
                                    
                                    await channel.send(msg_content)
                                    
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
    
    # Register persistent views
    bot.add_view(AttendanceView(bot))

# --- Persistent Views for Attendance ---

class ExcuseModal(discord.ui.Modal, title="Excuse Reason"):
    reason = discord.ui.TextInput(
        label="Reason for being excused",
        style=discord.TextStyle.paragraph,
        placeholder="e.g., I was sick...",
        required=True,
        max_length=200
    )

    def __init__(self, view_instance):
        super().__init__()
        self.view_instance = view_instance

    async def on_submit(self, interaction: discord.Interaction):
        await self.view_instance.handle_attendance(interaction, "excused", self.reason.value)
        # handle_attendance handles the response

class AttendanceView(discord.ui.View):
    def __init__(self, bot_instance):
        super().__init__(timeout=None) # Persistent view
        self.bot_instance = bot_instance

    @discord.ui.button(label="Mark Present", style=discord.ButtonStyle.success, custom_id="attendance_btn_present", emoji="✅")
    async def btn_present(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_attendance(interaction, "present")

    @discord.ui.button(label="Excused", style=discord.ButtonStyle.secondary, custom_id="attendance_btn_excused", emoji="⚠️")
    async def btn_excused(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check permission for admin only excuse is handled inside handle_attendance or here?
        # The modal should open first, then we check? Or check first?
        # Checking first is better UX.
        
        settings = load_settings()
        if settings.get('require_admin_excuse', True) and not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("Only admins can mark users as excused.", ephemeral=True)
            return
            
        # Open Modal to get reason
        await interaction.response.send_modal(ExcuseModal(self))

    async def handle_attendance(self, interaction, status, reason=None):
        user = interaction.user
        
        # Check self-marking setting (only for present)
        settings = load_settings()
        if status == 'present' and not settings.get('allow_self_marking', True):
             await interaction.response.send_message("Self-marking is currently disabled.", ephemeral=True)
             return

        # Check permitted role
        data = load_attendance_data()
        allowed_role_id = data.get('allowed_role_id')
        if allowed_role_id:
            allowed_role = interaction.guild.get_role(allowed_role_id)
            if allowed_role and allowed_role not in user.roles:
                await interaction.response.send_message(f"You need the {allowed_role.mention} role to use this.", ephemeral=True)
                return

        # If it's a modal submission (interaction.type == modal_submit), we don't need to defer usually if we reply quickly.
        # But process_status_update might take a moment.
        if not interaction.response.is_done():
             await interaction.response.defer(ephemeral=True)
        
        await self.process_status_update(interaction, user, status, reason)
        
        msg = f"Successfully marked as **{status.upper()}**!"
        if reason:
            msg += f"\nReason: {reason}"
        
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    async def process_status_update(self, interaction, member, status, reason=None):
        # Logic duplicated/adapted from update_user_status to avoid ctx dependency
        data = load_attendance_data()
        present_role_id = data.get('attendance_role_id')
        absent_role_id = data.get('absent_role_id')
        excused_role_id = data.get('excused_role_id')
        
        target_role_id = None
        roles_to_remove = []
        
        if status == 'present':
            target_role_id = present_role_id
            if absent_role_id: roles_to_remove.append(absent_role_id)
            if excused_role_id: roles_to_remove.append(excused_role_id)
        elif status == 'excused':
            target_role_id = excused_role_id
            if present_role_id: roles_to_remove.append(present_role_id)
            if absent_role_id: roles_to_remove.append(absent_role_id)
            
        guild = interaction.guild
        
        # Remove roles
        for rid in roles_to_remove:
            role = guild.get_role(rid)
            if role and role in member.roles:
                try:
                    await member.remove_roles(role)
                except: pass

        # Add role
        if target_role_id:
            role = guild.get_role(target_role_id)
            if role:
                try:
                    await member.add_roles(role)
                except: pass
        
        # Save record
        user_id = str(member.id)
        if 'records' not in data:
            data['records'] = {}
        
        record = {
            "status": status,
            "timestamp": datetime.datetime.now().isoformat()
        }
        if reason:
            record["reason"] = reason
            
        data['records'][user_id] = record
        save_attendance_data(data)

@bot.command(name='setup_attendance')
@commands.has_permissions(administrator=True)
async def setup_attendance_ui(ctx):
    """Posts the persistent attendance buttons."""
    embed = discord.Embed(
        title="Attendance Check-In", 
        description="Click the button below to mark your attendance.", 
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=AttendanceView(bot))


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
