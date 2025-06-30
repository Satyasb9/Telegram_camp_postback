# Telegram Campaign Bot v8.0 – Termux + Admin + Campaign + UPI Tracking        #This is testing bot v8.3 superstable
import telebot
from telebot import types
import json
import os
import re
import threading
import requests
#these are extra for render 
from flask import Flask, request
from threading import Thread

#API_TOKEN = '7781016918:AAHwhocdQReqIacADnNDwZl9A6dwZ1Tu4OA'

API_TOKEN = os.getenv("BOT_TOKEN")
#this is for render variable fetch...


ADMIN_ID = 1185120975  # Replace with your Telegram ID
BITLY_TOKEN = 'YOUR_BITLY_TOKEN_HERE'
USE_BITLY = False

DATA_FILE = 'data.json'
CAMPAIGN_FILE = 'campaigns.json'
TRACKED_FILE = 'tracked.json'


bot = telebot.TeleBot(API_TOKEN)
user_data = {}
send_target_upi = None

app = Flask(__name__)
#this is extra line for render 

# Load data
def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, 'r') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)


users = load_json(DATA_FILE)
campaigns = load_json(CAMPAIGN_FILE)
tracked_upis = load_json(TRACKED_FILE)

#-------Part-2-------#

# Shorten link
def shorten_link(url):
    if USE_BITLY:
        try:
            headers = {"Authorization": f"Bearer {BITLY_TOKEN}"}
            data = {"long_url": url}
            r = requests.post("https://api-ssl.bitly.com/v4/shorten", headers=headers, json=data)
            return r.json().get("link")
        except:
            return url
    else:
        try:
            r = requests.get(f"https://tinyurl.com/api-create.php?url={url}")
            return r.text
        except:
            return url

# UPI Validation
VALID_SUFFIXES = [
    "@sbi", "@icici", "@hdfcbank", "@axisbank", "@kotak", "@indus", "@oneyes",
    "@amazonpay", "@yapl", "@apl", "@ikwik", "@mbk", "@superyes", "@yescred",
    "@upi", "@postbank", "@jupiteraxis", "@oksbi", "@okaxis", "@okicici",
    "@okhdfcbank", "@freecharge", "@ptsbi", "@ptaxis", "@ptyes", "@pthdfc",
    "@ybl", "@axl", "@ibl"
]

def is_valid_upi(upi):
    return re.match(r"^[\w._-]+@[\w]+$", upi) and any(upi.endswith(sfx) for sfx in VALID_SUFFIXES)


# /start
@bot.message_handler(commands=['start'])
def start(message):
    cid = message.chat.id
    if cid == ADMIN_ID:
        text = (
            "👋 Welcome Admin!\n\n"
            "🗂 *Campaign Management*\n"
            "➤ /start  - Start The BOT \n"
            "➤ /addcampaign – Add new campaign\n"
            "➤ /editcampaign – Edit campaign name, URL or description\n"
            "➤ /previewcamp – Preview All campaigns\n"
            "➤ /deletecampaign – Delete a campaign\n\n"

            "👤 *User Management*\n"
            "➤ /viewall – View all users\n"
            "➤ /viewcamp – View users by campaign\n"
            "➤ /deletecamp – Delete user data of a selected campaign\n"
            "➤ /view upi@bank – View a user\n"
            "➤ /delete upi@bank – Delete a user\n"
            "➤ /deleteall – Delete all users\n"
            "➤ /export – Export user list to file(all clicks)\n\n"

            "📊 *Tracked Leads*\n"
            "➤ /tracked upi@bank – Mark UPI as tracked\n"
            "➤ /exporttracked – Export tracked users\n"
            "➤ /viewtracked – View tracked users\n"
            "➤ /deletetracked upi@bank – Remove a tracked user\n"
            "➤ /cleartracked – Clear all tracked leads\n\n"

            "📩 *Messaging*\n"
            "➤ /send upi@bank – Send custom message to user"
        )
        bot.send_message(cid, text)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for camp in campaigns:
            markup.add(camp)
        bot.send_message(cid, "👋 Hey there!\n\n"
    "🎯 Please choose a campaign from the list below:\n\n"
    "⚠️ If you accidentally pick the wrong one,\n\n"
    "🔁 just type /start to restart the bot.\n\n"
    "🚀 Let's begin!", reply_markup=markup)
        user_data[cid] = {}

# Campaign selected
@bot.message_handler(func=lambda m: m.text in campaigns)
def select_campaign(message):
    user_data[message.chat.id] = {'campaign': message.text}
    bot.send_message(message.chat.id, f"{campaigns[message.text]['desc']}\n\nSend your UPI ID:")

# UPI submitted
@bot.message_handler(func=lambda m: '@' in m.text and not m.text.startswith('/'))
def upi_input(message):
    upi = message.text.strip().lower()
    cid = message.chat.id
    username = f"@{message.from_user.username}" if message.from_user.username else f"User ID: {cid}"
    campaign = user_data[cid].get('campaign')

    if not is_valid_upi(upi):
        return bot.send_message(cid, "❌ Invalid UPI. Please enter a valid one like xxx@ybl, xxx@upi")

    # Save user data
    users[upi] = {
        "username": username,
        "campaign": campaign,
        "chat_id": cid
    }
    save_json(DATA_FILE, users)

    # Create referral link
    link = campaigns[campaign]['url'].replace('{aff_id}', upi)
    short_link = shorten_link(link)

    # Inline buttons
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(" 🔁 Restart Bot", callback_data="restart"),
        types.InlineKeyboardButton(" 📞 Contact Admin", url="https://t.me/Contact4TECbot")
    )

    # Send link
    bot.send_message(
    cid,
    f"✅ *Your unique offer link is:*\n\n 🔗 {short_link}\n\n ⏳ _This link is valid for 2 minutes only._\n\n  ❌ After that, it will be deleted automatically.\n\n🔁 To generate a new link, /start the bot again.",
    parse_mode='Markdown',
    reply_markup=markup
)

    # Auto-delete link message after 2 minutes
    threading.Timer(120, lambda: bot.delete_message(cid, message.message_id + 1)).start()

    # Notify admin
   # bot.send_message(ADMIN_ID, f"    📩 Campaign: {campaign}\n👤 {username}\n💳 UPI: {upi}")

    bot.send_message(
    ADMIN_ID,
    f"📩 *Campaign:* {campaign}\n👤 {username}\n💳 *UPI:* `{upi}`",
    parse_mode="Markdown"
)

#-------------Part 3----------#

# /tracked
@bot.message_handler(commands=['tracked'])
def tracked(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        upi = message.text.split()[1].lower()
        if upi in users:
            chat_id = users[upi]["chat_id"]
            campaign = users[upi]["campaign"]
            bot.send_message(chat_id, f"🎉 Your registration on *{campaign}* has been tracked. Please move to the next step.", parse_mode="Markdown")
            bot.send_message(ADMIN_ID, f" ✅ Notified: {upi}")
            tracked_upis[upi] = True
            save_json(TRACKED_FILE, tracked_upis)
        else:
            bot.send_message(ADMIN_ID, "❌ UPI not found")
    except:
        bot.send_message(ADMIN_ID, "Usage: /tracked upi@bank")


# /send
@bot.message_handler(commands=['send'])
def send_prompt(message):
    global send_target_upi
    if message.chat.id != ADMIN_ID:
        return
    try:
        send_target_upi = message.text.split()[1].strip().lower()
        if send_target_upi not in users:
            return bot.send_message(ADMIN_ID, " ❌ UPI not found.")
        bot.send_message(ADMIN_ID, "✉️ Now send the message to deliver:")
    except:
        bot.send_message(ADMIN_ID, "Usage: /send upi@bank")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and not m.text.startswith('/'))
def send_message_to_user(message):
    global send_target_upi
    if send_target_upi:
        user_chat_id = users[send_target_upi]["chat_id"]
        bot.send_message(user_chat_id, f" 📨 Admin Message:\n\n{message.text}")
        bot.send_message(ADMIN_ID, f"✅ Message sent to: {send_target_upi}")
        send_target_upi = None



# /delete upi
@bot.message_handler(commands=['delete'])
def delete_user(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        upi = message.text.split()[1].lower()
        if upi in users:
            del users[upi]
            save_json(DATA_FILE, users)
            bot.send_message(ADMIN_ID, f" ✅ Deleted {upi}")
        else:
            bot.send_message(ADMIN_ID, "❌ UPI not found")
    except:
        bot.send_message(ADMIN_ID, "Usage: /delete upi@bank")

# /delete-all
@bot.message_handler(commands=['deleteall'])
def delete_all(message):
    if message.chat.id == ADMIN_ID:
        user_data["confirm_deleteall"] = True
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Yes", callback_data="confirm_deleteall"),
            types.InlineKeyboardButton("❌ No", callback_data="cancel_deleteall")
        )
        bot.send_message(ADMIN_ID, "⚠️ Are you sure you want to delete ALL users?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_deleteall")
def confirmed_delete_all(call):
    users.clear()
    save_json(DATA_FILE, users)
    bot.send_message(ADMIN_ID, "     ✅ All user data has been deleted.")
    user_data["confirm_deleteall"] = None

@bot.callback_query_handler(func=lambda call: call.data == "cancel_deleteall")
def cancel_delete_all(call):
    bot.send_message(ADMIN_ID, "     ❌ Deletion cancelled.")
    user_data["confirm_deleteall"] = None


# /export
@bot.message_handler(commands=['export'])
def export(message):
    if message.chat.id == ADMIN_ID:
        with open("export.txt", "w") as f:
            for upi, info in users.items():
                f.write(f"UPI: {upi}, Username: {info['username']}, Campaign: {info['campaign']}\n")
        with open("export.txt", "rb") as doc:
            bot.send_document(ADMIN_ID, doc)

# /view upi
@bot.message_handler(commands=['view'])
def view_user(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        upi = message.text.split()[1].lower()
        if upi in users:
            data = users[upi]
            bot.send_message(ADMIN_ID, f" 👤 {data['username']}\n 💳 {upi}\n📋 {data['campaign']}")
        else:
            bot.send_message(ADMIN_ID, "❌ UPI not found")
    except:
        bot.send_message(ADMIN_ID, "Usage: /view upi@bank")

# /view-all
#@bot.message_handler(commands=['viewall'])
#def view_all(message):
    #if message.chat.id == ADMIN_ID:
        #for upi, data in users.items():
            #bot.send_message(ADMIN_ID, f"{data['username']} - {upi} ({data['campaign']})")
#another verson of viewall (use only one comment out the other )
@bot.message_handler(commands=['viewall'])
def view_all(message):
    if message.chat.id == ADMIN_ID:
        for upi, data in users.items():
            safe_upi = upi.replace("_", "\\_")  # Escape underscore if present
            bot.send_message(
                ADMIN_ID,
                f"📋 *Campaign:* {data['campaign']}\n👤 {data['username']}\n💳 *UPI:* `{safe_upi}`",
                parse_mode="Markdown"
            )


# /view-camp
@bot.message_handler(commands=['viewcamp'])
def view_camp(message):
    if message.chat.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup()
    for camp in campaigns:
        markup.add(types.InlineKeyboardButton(camp, callback_data=f"viewcamp_{camp}"))
    user_data[message.chat.id] = {'mode': 'viewcamp'}
    bot.send_message(ADMIN_ID, "     📋 Select a campaign to view users:", reply_markup=markup)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("viewcamp_"))
def handle_viewcamp(call):
    campaign = call.data.replace("viewcamp_", "")
    count = 0
    for upi, data in users.items():
        if data.get("campaign") == campaign:
            safe_upi = upi.replace("_", "\\_")  # Escape _ for Markdown
            bot.send_message(
                ADMIN_ID,
                f"📋 *Campaign:* {campaign}\n👤 {data['username']}\n💳 *UPI:* `{safe_upi}`",
                parse_mode="Markdown"
            )
            count += 1
    if count == 0:
        bot.send_message(ADMIN_ID, "ℹ️ No users found for this campaign.")
    user_data[call.message.chat.id]['mode'] = None



#deleteCamp  Delete user data of a selected Campaign

@bot.message_handler(commands=['deletecamp'])
def delete_camp_data(message):
    if message.chat.id != ADMIN_ID:
        return
    if not users:
        return bot.send_message(ADMIN_ID, "ℹ️ No user data available.")
    
    camps = set(data['campaign'] for data in users.values() if 'campaign' in data)
    if not camps:
        return bot.send_message(ADMIN_ID, "ℹ️ No campaigns found in user data.")

    markup = types.InlineKeyboardMarkup()
    for camp in sorted(camps):
        markup.add(types.InlineKeyboardButton(camp, callback_data=f"deletecamp_select:{camp}"))
    bot.send_message(ADMIN_ID, "*🗑 Select a campaign to delete its users:*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deletecamp_select:"))
def confirm_delete_camp_users(call):
    camp = call.data.split(":")[1]
    user_data['delete_camp_target'] = camp
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Yes", callback_data="deletecamp_confirm"),
        types.InlineKeyboardButton("❌ No", callback_data="deletecamp_cancel")
    )
    bot.send_message(ADMIN_ID, f"⚠️ Are you sure you want to delete all users from:\n*{camp}*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["deletecamp_confirm", "deletecamp_cancel"])
def handle_deletecamp_confirm(call):
    if call.data == "deletecamp_cancel":
        user_data.pop('delete_camp_target', None)
        return bot.send_message(ADMIN_ID, "❌ Deletion cancelled.")

    camp = user_data.get('delete_camp_target')
    if not camp:
        return bot.send_message(ADMIN_ID, "⚠️ No campaign selected.")

    removed = 0
    to_delete = [upi for upi, data in users.items() if data.get("campaign") == camp]
    for upi in to_delete:
        del users[upi]
        removed += 1

    save_json(DATA_FILE, users)
    user_data.pop('delete_camp_target', None)
    bot.send_message(ADMIN_ID, f"✅ Deleted *{removed}* users from campaign: *{camp}*", parse_mode="Markdown")


#/exporttracked

@bot.message_handler(commands=['exporttracked'])
def export_tracked(message):
    if message.chat.id != ADMIN_ID:
        return
    if not tracked_upis:
        return bot.send_message(ADMIN_ID, "ℹ️ No tracked UPIs yet.")

    with open("tracked_upis.txt", "w") as f:
        for upi in tracked_upis:
            data = users.get(upi, {})
            f.write(f"UPI: {upi}, Username: {data.get('username','-')}, Campaign: {data.get('campaign','-')}\n")
    with open("tracked_upis.txt", "rb") as doc:
        bot.send_document(ADMIN_ID, doc)

#/viewtracked
@bot.message_handler(commands=['viewtracked'])
def view_tracked(message):
    if message.chat.id != ADMIN_ID:
        return
    if not tracked_upis:
        return bot.send_message(ADMIN_ID, "ℹ️ No tracked UPIs yet.")
    for upi in tracked_upis:
        data = users.get(upi, {})
        safe_upi = upi.replace("_", "\\_")  # escape underscore for Markdown
        username = data.get('username', '-')
        campaign = data.get('campaign', '-')
        bot.send_message(
            ADMIN_ID,
            f"*──────── Tracked ─────────*\n"
            f"📋 *Campaign:* {campaign}\n"
            f"👤 {username}\n"
            f"💳 *UPI:* `{safe_upi}`",
            parse_mode="Markdown"
        )



#/deletetracked
@bot.message_handler(commands=['deletetracked'])
def delete_tracked(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        upi = message.text.split()[1].lower()
        if upi in tracked_upis:
            del tracked_upis[upi]
            save_json(TRACKED_FILE, tracked_upis)
            bot.send_message(ADMIN_ID, f"🗑 Removed tracked UPI: {upi}")
        else:
            bot.send_message(ADMIN_ID, "❌ UPI not found in tracked list.")
    except:
        bot.send_message(ADMIN_ID, "⚠️ Usage: /deletetracked upi@bank")

#cleartracked

@bot.message_handler(commands=['cleartracked'])
def clear_tracked(message):
    if message.chat.id != ADMIN_ID:
        return
    user_data["confirm_cleartracked"] = True
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(" ✅ Yes", callback_data="confirm_cleartracked"),
        types.InlineKeyboardButton(" ❌ No", callback_data="cancel_cleartracked")
    )
    bot.send_message(ADMIN_ID, "⚠️ Are you sure you want to clear all tracked UPIs?", reply_markup=markup)
@bot.callback_query_handler(func=lambda call: call.data == "confirm_cleartracked")
def confirmed_clear_tracked(call):
    tracked_upis.clear()
    save_json(TRACKED_FILE, tracked_upis)
    bot.send_message(ADMIN_ID, "     ✅ All tracked UPIs have been cleared.")
    user_data["confirm_cleartracked"] = None

@bot.callback_query_handler(func=lambda call: call.data == "cancel_cleartracked")
def cancel_clear_tracked(call):
    bot.send_message(ADMIN_ID, "     ❌ Tracked UPI clearing cancelled.")
    user_data["confirm_cleartracked"] = None

#--------------Part 4-----------#

# === Campaign Management ===

#add Campaign

@bot.message_handler(commands=['addcampaign'])
def add_campaign(message):
    if message.chat.id != ADMIN_ID:
        return
    bot.send_message(ADMIN_ID, "Send new campaign name:")
    bot.register_next_step_handler(message, ask_campaign_url)

def ask_campaign_url(message):
    name = message.text.strip()
    user_data['new_camp'] = name
    bot.send_message(ADMIN_ID, "Now send the campaign URL with {aff_id}")
    bot.register_next_step_handler(message, ask_campaign_desc)

def ask_campaign_desc(message):
    url = message.text.strip()
    user_data['new_url'] = url
    bot.send_message(ADMIN_ID, "Send description:")
    bot.register_next_step_handler(message, save_campaign)

def save_campaign(message):
    desc = message.text.strip()
    name = user_data.get('new_camp')
    url = user_data.get('new_url')
    campaigns[name] = {'url': url, 'desc': desc}
    save_json(CAMPAIGN_FILE, campaigns)
    bot.send_message(ADMIN_ID, f"    ✅ Campaign '{name}' added.")

#deletecampaign
@bot.message_handler(commands=['deletecampaign'])
def delete_campaign(message):
    if message.chat.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup()
    for name in campaigns:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"delcamp_{name}"))
    bot.send_message(ADMIN_ID, "🗑 Select campaign to delete:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delcamp_"))
def confirm_delete_campaign(call):
    name = call.data.replace("delcamp_", "")
    user_data["del_camp_name"] = name

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(" ✅ Yes", callback_data="confirm_delete"),
        types.InlineKeyboardButton(" ❌ No", callback_data="cancel_delete")
    )
    bot.send_message(ADMIN_ID, f"⚠️ Are you sure you want to delete '{name}'?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "confirm_delete")
def delete_confirmed(call):
    name = user_data.get("del_camp_name")
    if name in campaigns:
        del campaigns[name]
        save_json(CAMPAIGN_FILE, campaigns)
        bot.send_message(ADMIN_ID, f"✅ Campaign '{name}' has been deleted.")
    else:
        bot.send_message(ADMIN_ID, " ❌ Campaign not found.")
    user_data["del_camp_name"] = None

@bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
def delete_cancelled(call):
    bot.send_message(ADMIN_ID, "     ❌ Campaign deletion cancelled.")
    user_data["del_camp_name"] = None


#----Edit Campaign---#
@bot.message_handler(commands=['editcampaign'])
def edit_campaign(message):
    if message.chat.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup()
    for name in campaigns:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"edit_{name}"))
    bot.send_message(ADMIN_ID, "     📋 Choose a campaign to edit:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_") and not call.data.startswith("edit_name") and not call.data.startswith("edit_url") and not call.data.startswith("edit_desc"))
def show_edit_options(call):
    name = call.data.replace("edit_", "")
    user_data["edit_camp"] = name


    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✏️ Edit Name", callback_data="edit_name"),
        types.InlineKeyboardButton(" 🔗 Edit URL", callback_data="edit_url"),
        types.InlineKeyboardButton(" 📝 Edit Description", callback_data="edit_desc")
    )
    bot.send_message(ADMIN_ID, f"Editing '{name}'. Choose what to change:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["edit_name", "edit_url", "edit_desc"])
def ask_new_value(call):
    field = call.data.replace("edit_", "")
    user_data["edit_field"] = field
    bot.send_message(ADMIN_ID, f"Send new value for {field}:")
    bot.register_next_step_handler_by_chat_id(ADMIN_ID, update_campaign)
    
#this code is for previewcamp 
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_name_") or call.data.startswith("edit_url_") or call.data.startswith("edit_desc_"))
def ask_preview_edit(call):
    if call.data.startswith("edit_name_"):
        field = "name"
        target = call.data.replace("edit_name_", "")
    elif call.data.startswith("edit_url_"):
        field = "url"
        target = call.data.replace("edit_url_", "")
    else:
        field = "desc"
        target = call.data.replace("edit_desc_", "")

    user_data["edit_camp"] = target
    user_data["edit_field"] = field
    bot.send_message(ADMIN_ID, f"✏️ Send new {field} for campaign *{target}*:", parse_mode="Markdown")
    bot.register_next_step_handler_by_chat_id(ADMIN_ID, update_campaign)


  #preview camp end 
  
def update_campaign(message):
    name = user_data.get("edit_camp")
    field = user_data.get("edit_field")
    new_value = message.text.strip()


    if field == "name":
        # Rename key
        campaigns[new_value] = campaigns.pop(name)
        user_data["edit_camp"] = new_value
        bot.send_message(ADMIN_ID, f"✅ Campaign renamed to '{new_value}'")
    else:
        if field == "url":
            campaigns[name]["url"] = new_value
        elif field == "desc":
            campaigns[name]["desc"] = new_value
        bot.send_message(ADMIN_ID, f"✅ Updated {field} of '{name}'")

    save_json(CAMPAIGN_FILE, campaigns)

#preview camp 

@bot.message_handler(commands=['previewcamp'])
def preview_campaign_select(message):
    if message.chat.id != ADMIN_ID:
        return
    if not campaigns:
        return bot.send_message(ADMIN_ID, "ℹ️ No campaigns available.")

    markup = types.InlineKeyboardMarkup()
    for name in campaigns:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"previewcamp:{name}"))
    bot.send_message(ADMIN_ID, "*📋 Select a campaign to preview:*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("previewcamp:"))
def preview_campaign_details(call):
    name = call.data.split(":")[1]
    data = campaigns.get(name)
    if not data:
        return bot.send_message(ADMIN_ID, "❌ Campaign not found.")

    url = data.get("url", "-")
    desc = data.get("desc", "-")

    # Campaign name with edit
    name_markup = types.InlineKeyboardMarkup()
    name_markup.add(types.InlineKeyboardButton("✏️ Edit Name", callback_data=f"edit_name_{name}"))
    bot.send_message(ADMIN_ID, f"*📢 Campaign Name:*\n{name}", parse_mode="Markdown", reply_markup=name_markup)

    # Campaign URL with edit
    url_markup = types.InlineKeyboardMarkup()
    url_markup.add(types.InlineKeyboardButton("🔗 Edit URL", callback_data=f"edit_url_{name}"))
    bot.send_message(ADMIN_ID, f"*🔗 URL:*\n`{url}`", parse_mode="Markdown", reply_markup=url_markup)

    # Description with edit
    desc_markup = types.InlineKeyboardMarkup()
    desc_markup.add(types.InlineKeyboardButton("📝 Edit Desc", callback_data=f"edit_desc_{name}"))
    bot.send_message(ADMIN_ID, f"*📝 Description:*\n{desc}", parse_mode="Markdown", reply_markup=desc_markup)

#postback auto tracking set up in telegram bot and run it on render.com 

@app.route('/postback', methods=['GET'])
def handle_postback():
    clickid = request.args.get('clickid') or request.args.get('p1')
    camp_id = request.args.get('camp_id') or 'Unknown'

    if not clickid or clickid not in users:
        return "Invalid clickid", 400

    user = users[clickid]
    chat_id = user['chat_id']
    username = user['username']
    campaign = user['campaign']

    # Notify user
    bot.send_message(
        chat_id,
        f"🎉 Your registration on *{campaign}* has been tracked. Please move to the next step.",
        parse_mode="Markdown"
    )

    # Notify admin
    bot.send_message(
        ADMIN_ID,
        f"*--------📡 Tracked via Postback --------*\n"
        f"📢 *Campaign:* {campaign}\n"
        f"👤 {username}\n"
        f"💳 *UPI:* `{clickid}`",
        parse_mode="Markdown"
    )

    # Save to tracked
    tracked_upis[clickid] = True
    save_json(TRACKED_FILE, tracked_upis)

    return "OK", 200


# === Bot Startup ===


@bot.callback_query_handler(func=lambda call: call.data == "restart")
def restart_callback(call):
    start(call.message)


#if __name__ == '__main__':
    #print("🤖 Bot is running...")
   # bot.infinity_polling()

#this is extra for render

def start_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    Thread(target=start_bot).start()
    app.run(host="0.0.0.0", port=10000)
