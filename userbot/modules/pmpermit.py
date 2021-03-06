# Copyright (C) 2019-2021 The Authors
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for keeping control on who can PM you. """

import asyncio
import time
import random

from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import ReportSpamRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User

from userbot import (
    MONGO,
    BOTLOG,
    BOTLOG_CHATID,
    CMD_HELP,
    COUNT_PM,
    COUNT_PM_LOG,
    LASTMSG,
    LOGS,
    PM_AUTO_BAN,
    MAX_FLOOD_IN_PM,
    PM_PERMIT_MSG,
    PM_PASSWORD,
    is_mongo_alive,
    is_redis_alive,
    
)
from userbot.events import register, grp_exclude
from userbot.modules.dbhelper import (
    autoapproval,
    autoapprove,
    approval,
    approve,
    disapprove,
    this_pic,
    notif_off,
    notif_on,
    notif_state,
)

# ========================= CONSTANTS ============================
UNAPPROVED_MSG_ON = PM_PERMIT_MSG or (
    "Bleep blop! I am a bot.\n"
    "Hmm...I don't remember seeing you around here.\n\n"
    "So I will wait for my owner to look in and approve you. They mostly approve PMs.\n\n"
    "**Till then, don't try to spam! Follow my warnings or I will block you!!**"
)
    
UNAPPROVED_MSG_OFF = PM_PERMIT_MSG or (
    "Bleep blop! I am a bot.\n"
    "Hmm...I don't remember seeing you around here.\n\n"
    "So I will wait for my owner to look in and approve you. It may take a long time.\n\n"
    "My owner has turned off notifications, so I will read your messages and won't notify them.\n\n"
    "**Till then, don't try to spam! Follow my warnings or I will block you!!**"
)
        
MAX_MSG = MAX_FLOOD_IN_PM or 5
# =================================================================

async def delete_in(text, seconds):
    await asyncio.sleep(seconds)
    return await text.delete()

async def iterate_delete(event, event_id, user, text):
    async for message in event.client.iter_messages(
        event_id, from_user=user, limit=300
    ):
        clean_msg = message.text
        if clean_msg == text:
            await message.delete()
            
            
@register(incoming=True, disable_edited=True, disable_errors=True)
@grp_exclude()
async def permitpm(event):
    """ Permits people from PMing you without approval.
           Will block retards automatically. """
    if PM_AUTO_BAN:
        if event.is_private and not (await event.get_sender()).bot:
            if not is_mongo_alive() or not is_redis_alive():
                return
            await pm_password(event)
            if await approval(event.chat_id) is False:
                if event.chat_id not in LASTMSG:
                    #----------------------------------------------------
                    PM_PERMIT_IMAGE = await this_pic("PM_PERMIT_IMAGE")
                    #----------------------------------------------------
                    if PM_PERMIT_IMAGE:
                        if await notif_state() is True:
                            await event.respond(UNAPPROVED_MSG_ON, file=PM_PERMIT_IMAGE)
                            LASTMSG.update({event.chat_id: event.text})
                        if await notif_state() is False:
                            await event.respond(UNAPPROVED_MSG_OFF, file=PM_PERMIT_IMAGE)
                            LASTMSG.update({event.chat_id: event.text})
                    elif not PM_PERMIT_IMAGE:
                        if await notif_state() is True:
                            await event.respond(UNAPPROVED_MSG_ON)
                            LASTMSG.update({event.chat_id: event.text})
                        if await notif_state() is False:
                            await event.respond(UNAPPROVED_MSG_OFF)
                            LASTMSG.update({event.chat_id: event.text})
                        
                if await notif_state() is False:
                    await event.client.send_read_acknowledge(event.chat_id)
                if event.chat_id not in COUNT_PM:
                    COUNT_PM.update({event.chat_id: 1})
                else:
                    COUNT_PM[event.chat_id] += 1
                    
                #=======================================   
                WARN = MAX_MSG - COUNT_PM[event.chat_id] #
                #=======================================
                
#==============#                                      
                async def pm_notifier():        
                    if BOTLOG:
                        name = await event.client.get_entity(event.chat_id)
                        name0 = str(name.first_name)
                        
                        log_message = (
                            "#INCOMING\n"
                            + f"[{name0}](tg://user?id={event.chat_id})"                            
                            + " is waiting in your PM.\n" 
                            + f"[{name0}](tg://user?id={event.chat_id})" 
                            + " has sent {} message(s)."
                        )
                        
                        if event.chat_id in COUNT_PM_LOG:
                            await COUNT_PM_LOG[event.chat_id].delete()
                            
                        if WARN < 0:
                            return
                        else:
                            COUNT_PM_LOG[event.chat_id] = await event.client.send_message(
                                    BOTLOG_CHATID, 
                                    log_message.format(COUNT_PM[event.chat_id]))
#==============#                                      
                                                        
    
                if WARN > 1:
                    message = await event.reply(f"You have {WARN} warns left.")
                    await delete_in(message, 5)
                    await pm_notifier()
                elif WARN == 1:
                    message = await event.reply("You have 1 warn left.")
                    await delete_in(message, 5)
                    await pm_notifier()
                elif WARN == 0:
                    message = await event.reply("**This is the last warning. Please stop spamming!!**")
                    await delete_in(message, 10)
                    await pm_notifier()
                elif WARN == -1:
                    await event.respond("You were spamming the PM, inspite of my warnings.\n"
                                    "So now you are BLOCKED and REPORTED spam!!")
                    await iterate_delete(event, event.chat_id, "me", UNAPPROVED_MSG_ON)
                    await iterate_delete(event, event.chat_id, "me", UNAPPROVED_MSG_OFF)
                
                if WARN <= -1:
                    await event.client(BlockRequest(event.chat_id))
                    await event.client(ReportSpamRequest(peer=event.chat_id))
                    
                    try:
                        del COUNT_PM[event.chat_id]
                        del LASTMSG[event.chat_id]
                    except KeyError:
                        if BOTLOG:
                            for i in range(1):
                                await event.client.send_message(
                                    BOTLOG_CHATID,
                                    "PMPermit broke, please restart Paperplane.",
                                )
                        LOGS.info("PMPermit broke, please restart Paperplane.")
                        return
                
                    if BOTLOG:
                        name = await event.client.get_entity(event.chat_id)
                        name0 = str(name.first_name)
                        await event.client.send_message(
                            BOTLOG_CHATID,
                            "["
                            + name0
                            + "](tg://user?id="
                            + str(event.chat_id)
                            + ")"
                            + " was spamming your PM and has been blocked.",
                        )
                    


# Some fun func:
async def pm_password(event):
    """Will approve someone who enters the correct PM password"""
    if event.is_private and PM_PASSWORD:
        if await approval(event.chat_id) is False:
            async for password in event.client.iter_messages(
                event.chat_id,
                from_user=event.chat_id,
                limit=300
            ):
                password = password.text
                
                if password == PM_PASSWORD:
                    await approve(event.chat_id)
                    await iterate_delete(event, event.chat_id, "me", UNAPPROVED_MSG_ON)
                    await iterate_delete(event, event.chat_id, "me", UNAPPROVED_MSG_OFF)
                    await iterate_delete(event, event.chat_id, event.chat_id, PM_PASSWORD)
                    
                    wlcm_msg = (
                        await event.reply("Welcome, I am a bot!!\n" 
                                      "Very nice to meet you😊 "
                                      "I will ping my owner about you now."
                                     )
                    )
                    
                    async with event.client.conversation(event.chat_id) as conv:
                        rmd_msg = await conv.send_message(
                            "Just say a \"Hi\"."
                        )
                        response = (await conv.get_response()).message
                        
                        if response == ("Hi" or "\"Hi\""):
                            message = await event.reply(
                                "Great! Now you can be comfortable, I won't intuerrupt😉"
                            )
                        else:
                            message = await event.reply(
                                "Ok it wasn't a \"Hi\"," 
                                " but I won't interrupt anymore. Take care☺️"
                            )
                            
                        if await conv.wait_read(message):
                            await delete_in(wlcm_msg, 0)
                            await delete_in(rmd_msg, 0)
                            await delete_in(message, 3)
                    
                    try:
                        del COUNT_PM[event.chat_id]
                        del LASTMSG[event.chat_id]
                    except KeyError:
                        pass
                    
                    if BOTLOG:
                        name = await event.client.get_entity(event.chat_id)
                        name0 = str(name.first_name)
                        await event.client.send_message(BOTLOG_CHATID,
                                                        "#PM_UNLOCKED\n"
                                                       f"[{name0}](tg://user?id={event.chat_id}) "
                                                        "entered PM password and has been approved."
                                                       )
                    return
                    
#
 
    
@register(outgoing=True, pattern="(autoapprove|autoa)$")
@grp_exclude()
async def auto_approve_switch(event):
    """Will switch auto approve on or off"""
    if not is_mongo_alive() or not is_redis_alive():
        await apprvpm.edit("Database connections failing!")
        return
    else:
        await autoapprove()
        
    if await autoapproval() is True:
        x = await event.edit("`Auto-Approve` ON! I will approve an user after you PM them.")
        await delete_in(x, 5)
    else:
        y = await event.edit("`Auto-Approve` OFF! You will have to manually approve users now.")
        await delete_in(y, 5)
    
    
@register(disable_edited=True, outgoing=True, disable_errors=True)
@grp_exclude()
async def auto_accept(event):
    """Will approve automatically if you text them."""
    if await autoapproval() is True:
        chat = await event.get_chat()
        if not is_mongo_alive() or not is_redis_alive():
            return
        if event.text.startswith((".block", ".autoa", ".a", ".da", ".autoapprove", 
                                  ".approve", ".disapprove", ".notifon", ".notifoff")):
            return
        if event.is_private: 
            if not await approval(chat.id) and not chat.bot:
                await approve(chat.id)
                await iterate_delete(event, chat.id, "me", UNAPPROVED_MSG_ON)
                await iterate_delete(event, chat.id, "me", UNAPPROVED_MSG_OFF)

                if BOTLOG:
                    await event.client.send_message(
                    BOTLOG_CHATID,
                    "#AUTO_APPROVED\n"
                    + "User: "
                    + f"[{chat.first_name}](tg://user?id={chat.id})",
              )              

@register(outgoing=True, pattern="notifoff$")
@grp_exclude()
async def notifoff(noff_event):
    """For .notifoff command, stop getting
    notifications from unapproved PMs."""
    if await notif_off() is False:
        x = await noff_event.edit("Notifications are already silenced.")
        return await delete_in(x, 5)
    else:
        y = await noff_event.edit("Notifications silenced!")
        return await delete_in(y, 5)  
 

@register(outgoing=True, pattern="notifon$")
@grp_exclude()
async def notifon(non_event):
    """For .notifoff command, get notifications from unapproved PMs."""
    if await notif_on() is False:
        x = await non_event.edit("Notifications aren't muted.")
        return await delete_in(x, 5)
    else:
        y = await non_event.edit("Notifications unmuted!")
        return await delete_in(y, 5)
    
    
#=============================================== 
# Now here's the approve, disapprove, block and unblock command helper.
#===================================

"""User Getter"""
async def user_getter(event):
    if event.pattern_match.group(1):
        try:
            user = await event.client.get_entity(event.pattern_match.group(1))
            name = str(user.first_name)
            user_id = user.id
        except ValueError:
            return await exception_handler(event, 'username')
    elif event.is_private:
            user = await event.client.get_entity(event.chat_id)
            name = str(user.first_name)
            user_id = user.id
    elif event.reply_to_msg_id:
        try:
            reply = await event.get_reply_message()
            name = str((await event.client.get_entity(reply.sender.id)).first_name)
            user_id = reply.sender.id
        except TypeError:
            return await exception_handler(event, 'reply')
    else:
         return await error_handler(event)
    return name, user_id

"""Error Handler"""
async def error_handler(event):
    if f"{event}" == "apprvpm":
        message = "I can't see the user you want to approve😳"
    if f"{event}" == "dapprvpm":
        message = "I can't see the user you want to approve😳"
    if f"{event}" == "block":
        message = "Gimme the user to **block**!!"
    if f"{event}" == "unblock":
        message = "Well, I can't unblock __nobody__"
    await event.edit(message)
    return await delete_in(message, 5)
        
"""Exeption Handler"""
async def exception_handler(event, type):
    if type == 'username':
        message = await event.edit(
            "I am sorry. I can't find that user😥. "
             "Have you entered the correct username?"
        )
        return await delete_in(message, 5)
    else:
        message = await event.edit(
            "Excuse me...Is that an anonymous admin?"
        )
        return await delete_in(message, 5)
#===================================
# Here it ends.
#=============================================== 

    
@register(outgoing=True, pattern="(?:approve|a)(?: |$)(.*)$")
@grp_exclude()
async def approvepm(apprvpm):
    """For .approve command, give someone the permissions to PM you."""
    if not is_mongo_alive() or not is_redis_alive():
        await apprvpm.edit("Database connections failing!")
        return
    
    try:
        aname, uid = await user_getter(apprvpm)
    except:
        return
    
    if await approval(uid) is True:
        x = await apprvpm.edit("I already know this user! You can chat!")
        return await delete_in(x, 5)
    
    await approve(uid)
    await apprvpm.edit(f"I will remember [{aname}](tg://user?id={uid}) as your __mutual__ contact😉")
    await asyncio.sleep(3)
    await iterate_delete(apprvpm, uid, "me", UNAPPROVED_MSG_ON)
    await iterate_delete(apprvpm, uid, "me", UNAPPROVED_MSG_OFF)
    
    if apprvpm.pattern_match.group(1):
        await apprvpm.edit(f"[{aname}](tg://user?id={uid}) can PM you now.")
    elif apprvpm.reply_to_msg_id:
        await apprvpm.edit(f"[{aname}](tg://user?id={uid}), you can PM without an issue😊")
    elif apprvpm.is_private:
        await apprvpm.edit("Hey there! Nice to meet you😊 I am an obidient bot of my owner!")
        
    if uid in LASTMSG:
        del LASTMSG[uid]
    if uid in COUNT_PM:
        del COUNT_PM[uid]

    if BOTLOG:
        await apprvpm.client.send_message(
            BOTLOG_CHATID, "#APPROVED\n" + "User: " + f"[{aname}](tg://user?id={uid})"
        )
        
        
        
@register(outgoing=True, pattern="(?:disapprove|da)(?: |$)(.*)$")
@grp_exclude()
async def dapprovepm(dapprvpm):
    """For .disapprove command, revokes someone's permission to PM you."""
    if not is_mongo_alive() or not is_redis_alive():
        await dapprvpm.edit("Database connections failing!")
        return
    
    try:
        dname, uid = await user_getter(dapprvpm)
    except:
        return
    
    if await approval(uid) is False:
        x = await dapprvpm.edit("The user is already a stranger for me.")
        return await delete_in(x, 5)
    
    await disapprove(uid)
    await dapprvpm.edit(f"Forgetting [{dname}](tg://user?id={uid}) .")
    await asyncio.sleep(1)
    await dapprvpm.edit(f"Forgetting [{dname}](tg://user?id={uid}) ..")
    await asyncio.sleep(1)
    await dapprvpm.edit(f"Forgetting [{dname}](tg://user?id={uid}) ...")
    await asyncio.sleep(1)
    await dapprvpm.edit(f"Forgetting [{dname}](tg://user?id={uid}) ... Done!")
    await asyncio.sleep(1)
    
    if PM_PASSWORD:
        await iterate_delete(dapprvpm, uid, uid, PM_PASSWORD)
    
    if dapprvpm.pattern_match.group(1):
        await dapprvpm.edit(f"I will guard your PM from [{dname}](tg://user?id={uid}).")
    elif dapprvpm.is_private:
        await dapprvpm.edit("I don't like strangers in the PM!! Get lost!")
    elif dapprvpm.reply_to_msg_id:
        await dapprvpm.edit(f"[{dname}](tg://user?id={uid}), don't you dare PM!!")

    if BOTLOG:
        await dapprvpm.client.send_message(
            BOTLOG_CHATID, "#DISAPPROVED\n" + "User: " + f"[{dname}](tg://user?id={uid})"
        )

        
@register(outgoing=True, pattern="block(?: |$)(.*)$")
@grp_exclude()
async def blockpm(block):
    """You can block some unwanted people."""
    
    try:
        uname, uid = await user_getter(block)
    except:
        return
    
    if block.pattern_match.group(1):
        await block.edit(f"{uname} will be blocked right away!")
    elif block.is_private:
        await block.edit("I am blocking you now.")
    elif block.reply_to_msg_id:
        await block.edit("You won't look good in PM.")
        
    await block.client(BlockRequest(uid))
    await block.edit("***Blocked***")
    
    if BOTLOG:
        await block.client.send_message(
            BOTLOG_CHATID, "#BLOCKED\n" + "User: " + f"[{name0}](tg://user?id={uid})"
        )

        

@register(outgoing=True, pattern="unblock(?: |$)(.*)$")
@grp_exclude()
async def unblockpm(unblock):
    """You can unblock the people 
            so that they can PM again."""
    
    try:
        uname, uid = await user_getter(unblock)
    except:
        return
    
    if unblock.pattern_match.group(1):
        await unblock.edit(f"I will unblock {uname} in three swconds but are you sure?")
    elif unblock.is_private:
        x = await unblock.edit("You are kidding, right?")
        return await delete_in(x, 5)
    elif unblock.reply_to_msg_id:
        await unblock.edit("You are gonna get unblocked, aren't you happy?")
    
    time.sleep(2)
    await unblock.client(UnblocRequest(uid))
    time.sleep(1)
    await unblock.edit("Let's make peace.")
    
    if BOTLOG:
        await unblock.client.send_message(
            BOTLOG_CHATID,
            f"#UNBLOCKED\n[{uname}](tg://user?id={uid}) was unblocked!.",
        )

        
        

CMD_HELP.update(
    {
        "pmpermit": [
            "PMPermit",
            " - `.autoapprove`||`.autoa`: Switches Auto-Approve module on/off.\n"
            " - `.approve`||`.a`: Approve the mentioned/replied person to PM.\n"
            " - `.disapprove`||`.da`: Disapprove the mentioned/replied person to PM.\n"
            " - `.block`: Block the person from PMing you.\n"
            " - `.unblock`: Unblock the person, so they can PM you again.\n"
            " - `.notifoff`: Stop any notifications coming from unapproved PMs.\n"
            " - `.notifon`: Allow notifications coming from unapproved PMs.\n"
            " - `.setpmpic <links>`: Set picture for your alive message.\n"
            " - `.getpmpic`: List all the pictures you have set.\n"
            " - `.delpmpic`: Delete all the pictures you have set.\n"
        ]
    }
)
