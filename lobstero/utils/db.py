"""Provides an entire suite of abstracted database functions.
Entirely useless for anything else."""

import sys
import json
import calendar
from collections import OrderedDict
from typing import Optional, Mapping, Sequence

import pendulum
import bigbeans
from . import misc
from ..lobstero_config import LobsteroCredentials

lc = LobsteroCredentials()
db = None


async def connect_to_db():
    global db
    db = await bigbeans.connect(
        user=lc.auth.storage_database_username,
        password=lc.auth.storage_database_password,
        host=lc.auth.storage_database_address,
        port=lc.auth.storage_database_port,
        database=lc.auth.storage_database_name
    )

root_directory = sys.path[0] + "/"


# old_db = dataset.connect('sqlite:///' + root_directory + 'data.db')
async def migrate(old, new):
    tables = [
        "afkmessagelist", "customreacts", "deniedchannels",
        "ecodata", "gnomedata", "inventory", "moderation",
        "prefixes", "reminders", "serversettings", "settings_channels",
        "tagdata", "welcomemessages"
    ]

    for table in tables:
        try:
            await new[table].drop()
        except:
            pass

        for item in old[table].all():
            to_insert = dict(item)
            del to_insert["id"]

            # this is disgusting, but what can you do
            if "user" in to_insert:
                to_insert["username"] = to_insert["user"]
                del to_insert["user"]

            if "moderation_confirmation" in to_insert:
                to_insert["moderation_confirmation"] = str(to_insert["moderation_confirmation"])

            print(to_insert)
            await new[table].insert(**to_insert)
        print("finished table " + table)


async def economy_manipulate(user_id, amount) -> None:
    """Changes how rich someone is or isn't"""
    table = db['ecodata']
    user_id = str(user_id)
    amount = int(amount)
    data = {"userid": user_id, "balance": (await economy_check(user_id)) + amount}
    await table.upsert(["userid"], **data)


async def economy_set(user_id, amount) -> None:
    """Forced redistribution of wealth."""
    table = db['ecodata']
    user_id = str(user_id)
    amount = int(amount)
    data = {"userid": user_id, "balance": (await economy_check(user_id)) + amount}
    await table.upsert(["userid"], **data)


async def economy_check(user_id) -> int:
    """Knock knock, it's the IRS."""
    table = db['ecodata']
    user_id = str(user_id)
    result = await table.find(userid=user_id)
    if not result:
        return 0
    else:
        return result[0]["balance"]


async def return_all_balances() -> list:
    """It's a big deal for the bank."""
    balancelist = []
    results = await db["ecodata"].all()
    for x in results:
        balancelist.append([x["balance"], x["userid"]])
    for _ in range(5):
        balancelist.append([0, 486309010447007756])
    return sorted(balancelist, key=lambda x: x[0], reverse=True)


async def set_tag(serverid, tagname, tagvalue) -> None:
    """Sets the value of a tag."""
    table = db["tagdata"]
    data = dict(tag=tagname.lower(), value=tagvalue, guildid=serverid)
    await table.upsert(["tag"], **data)


async def return_tag(serverid, tagname) -> Optional[str]:
    """Returns the value of a tag."""
    table = db["tagdata"]
    result = await table.find(tag=tagname.lower(), guildid=serverid)
    if not result:
        return None
    else:
        return result[0]["value"]


async def delete_tag(serverid, tagname) -> None:
    """Deletes a tag."""
    table = db["tagdata"]
    await table.delete(tag=tagname.lower(), guildid=serverid)


async def return_all_tags(serverid) -> list:
    """I really wouldn't be giving these docstrings if my linter didn't annoy me about it."""
    table = db["tagdata"]
    taglist = []
    results = await table.find(guildid=serverid)
    for x in results:
        taglist.append([x["tag"], x["value"]])

    return taglist


async def add_gnome(user_id, amount) -> int:
    """Adds a gnome to a user's gnome count."""
    gnometable = db['gnomedata']
    user_id = str(user_id)
    amount = int(amount)
    data = dict(userid=user_id, gnomeamount=gnome_check(user_id) + amount)
    await gnometable.upsert(["userid"], **data)

    return await gnome_check(user_id)


async def gnome_check(user_id) -> int:
    """Returns a user's gnome count."""
    gnometable = db['gnomedata']
    user_id = str(user_id)
    result = await gnometable.find(userid=user_id)
    if not result:
        return 0
    else:
        return result[0]["gnomeamount"]


async def return_all_gnomes() -> list:
    """Returns all gnomes to the local gardenware shop. They were faulty."""
    gnometable = db['gnomedata']
    balancelist = []
    results = await gnometable.all()
    for x in results:
        balancelist.append([x["gnomeamount"], x["userid"]])
    for i in range(5):
        balancelist.append([0, 486309010447007756])

    return sorted(balancelist, key=lambda x: x[0], reverse=True)


async def afk_message_set(user_id, text) -> None:
    """Sets a custom AFK-removal message for a user"""
    afktable = db['afkmessagelist']
    data = dict(userid=user_id, message=text)
    await afktable.upsert(["userid"], **data)


async def return_afk_message(user_id) -> Optional[str]:
    """Returns a user's custom AFk-removal message"""
    afktable = db['afkmessagelist']
    result = await afktable.find(userid=user_id)
    if not result:
        return None
    else:
        return result[0]["message"]


async def settings_values() -> list:
    """Returns settings values for everyone."""
    table = db['serversettings']
    return await table.all()


async def settings_value_for_guild(serverid) -> list:
    """Returns settings values for just one server."""
    table = db['serversettings']
    return await table.find_one(serverid=serverid)


async def edit_settings_value(serverid: int, val: str, new) -> None:
    """Edits a settings value."""
    table = db['serversettings']
    data = {"serverid": serverid, val: new}
    await table.upsert(["serverid"], **data)


async def give_table() -> Mapping[str, OrderedDict]:
    """Chucks a table at you out of sheer rage."""
    return {x["serverid"]: x for x in await settings_values()}


async def return_server_reacts_list(serverid: str) -> Sequence[OrderedDict]:
    """Reactions mapped by server."""
    return [x for x in await db["customreacts"].find(guildid=serverid)]


async def find_matching_response(serverid: str, trigger) -> list:
    """Finds a response."""
    table = db["customreacts"]
    result = await table.find(trigger=trigger, guildid=serverid)

    return json.loads(result[0]["response"]) if result else []


async def raw_find_matching_response(serverid: str, trigger):
    """The same as above, but raw-er."""
    table = db["customreacts"]
    result = await table.find(trigger=trigger, guildid=serverid)

    return result


async def add_reaction(serverid, trigger, value, mtype=None) -> None:
    """Adds a custom reaction."""
    table = db["customreacts"]
    val = await find_matching_response(str(serverid), trigger)
    val.append(value)
    newdata = {"trigger": trigger, "response": json.dumps(val), "guildid": serverid}
    if mtype is not None:
        newdata["type"] = mtype

    await table.upsert(["trigger"], **newdata)


async def remove_response(serverid, trigger, index: int, mtype) -> None:
    """Removes a response from a custom reaction."""
    table = db["customreacts"]
    val = await find_matching_response(serverid, trigger)
    del val[index]
    newdata = {
        "trigger": trigger,
        "response": json.dumps(val),
        "type": mtype,
        "guildid": serverid}

    await table.upsert(["trigger"], **newdata)


async def remove_reaction(serverid, trigger) -> None:
    """Removes a custom reaction entirely."""
    table = db["customreacts"]
    await table.delete(trigger=trigger, guildid=serverid)


async def deny_list_all() -> Mapping[str, OrderedDict]:
    """Returns denied channels."""
    return {str(x["serverid"]): x for x in await db["deniedchannels"].all()}


async def is_denied(serverid, channelid) -> bool:
    """Can we do the thing there?"""
    denied = await deny_list_all()
    if str(serverid) in denied:
        unpacked = [str(x) for x in json.loads(denied[str(serverid)]["channels"])]
        return str(channelid) in unpacked
    else:
        return False


async def add_new_deny_channel(serverid: str, channelid) -> None:
    """Denies a channel."""
    denied = await deny_list_all()
    table = db["deniedchannels"]

    if str(serverid) in denied:
        unpacked = json.loads(denied[str(serverid)]["channels"])
    else:
        unpacked = []

    unpacked.append(str(channelid))
    newdata = {"serverid": str(serverid), "channels": json.dumps(unpacked)}
    await table.upsert(["serverid"], **newdata)


async def remove_deny_channel(serverid: str, channelid) -> None:
    """I'm denying my denial,"""
    denied = await deny_list_all()
    table = db["deniedchannels"]

    if str(serverid) in denied:
        unpacked = json.loads(denied[str(serverid)]["channels"])
        if str(channelid) in unpacked:
            for index, x in enumerate(unpacked):
                if str(channelid) == x:
                    del unpacked[index]
                    newdata = {"serverid": serverid, "channels": json.dumps(unpacked)}
                    await table.upsert(["serverid"], **newdata)


async def prefix_list() -> Mapping[str, OrderedDict]:
    """List of prefixes."""
    return {str(x["serverid"]): x for x in await db["prefixes"].all()}


async def add_prefix(serverid: int, prefix: str) -> None:
    """Adds a prefix."""
    table = db["prefixes"]
    await table.upsert(["serverid"], **{"serverid": serverid, "prefix": prefix})


async def find_inventory(userid: str) -> Optional:
    """Because you lost it."""
    table = db["inventory"]
    result = list(await table.find(userid=str(userid)))

    return json.loads(result[0]["item"]) if result else []


async def grant_item(userid: str, item: str, count: int) -> None:
    """Gives you something."""
    table = db["inventory"]
    current = await find_inventory(userid)
    reconstructed, appended = [], False
    for pair in current:
        inv_item, amount = list(pair.items())[0]
        if inv_item.lower() == item.lower():
            reconstructed.append({item: int(amount) + abs(count)})
            appended = True
        else:
            reconstructed.append(pair)

    if not appended:
        reconstructed.append({item: count})

    newdata = {"userid": userid, "item": json.dumps(reconstructed)}
    await table.upsert(["userid"], **newdata)


async def remove_item(userid: str, item: str, count: int) -> bool:
    """What can be given can also be taken away."""
    table = db["inventory"]
    current = await find_inventory(userid)
    reconstructed, removed = [], False
    for pair in current:
        inv_item, amount = list(pair.items())[0]
        if inv_item.lower() == item.lower():
            if amount > count:
                reconstructed.append({item: int(amount) - abs(count)})
                removed = True
            elif int(amount) == count:
                removed = True
            else:
                reconstructed.append(pair)
        else:
            reconstructed.append(pair)

    newdata = {"userid": userid, "item": json.dumps(reconstructed)}
    await table.upsert(["userid"], **newdata)

    return removed


async def log_infraction(operation, guildid: int, userid: int, staffid: int, reason, expires="False", redacted="False"):
    """Drama recorder 9000"""
    if expires != "False":
        expiry = expires
    else:
        expiry = "False"

    rn = pendulum.now("Atlantic/Reykjavik")

    readable = rn.strftime((
        f"{calendar.day_name[rn.weekday()]} "
        f"{misc.ordinal(rn.day)} "
        f"{calendar.month_name[rn.month]} "
        f"%Y, %H:%M UTC"))
    encodeable = str(pendulum.now("Atlantic/Reykjavik"))

    data = {
        "operation": operation, "guild": guildid,
        "user": userid, "staff": staffid,
        "reason": reason, "expiry": expiry,
        "redacted": redacted, "date": readable,
        "date_raw": encodeable}

    table = db['moderation']
    await table.insert(**data)


async def find_infraction(operation, guildid, userid, id_):
    """Finds a very specific infraction."""
    table = db['moderation']
    res = await table.find_one(operation=operation, guild=guildid, user=userid, id=id_)

    return dict(res) if res else None


async def find_specific_infraction(id_):
    """Finds a slightly specific infraction"""
    table = db['moderation']
    res = await table.find_one(_id=id_)
    return dict(res) if res else None


async def find_all_infractions(guildid, operation=None):
    """All the wrongdoings."""
    table = db['moderation']
    res = await table.find(guild=guildid)
    if operation:
        return [item for item in res if item["operation"] == operation]
    else:
        return res


async def find_all_member_infractions(guildid, memberid, operation=None):
    """Finds wrongdoings for a specific guy."""
    table = db['moderation']
    res = await table.find(guild=guildid, user=memberid)
    if operation:
        return [item for item in res if item["operation"] == operation]
    else:
        return res


async def strike_infraction(operation, guildid, userid, id_, new: bool = True):
    """Proverbially crosses out an infraction."""
    table = db['moderation']
    r = await find_infraction(operation, guildid, userid, id_)
    r["redacted"] = str(new)
    await table.upsert(["_id"], **r)


async def return_all_expiring_infractions():
    """What will go wrong, when?"""
    statement = "SELECT * FROM moderation WHERE NOT (expiry = 'False')"
    return await db.fetch_query(statement)


async def close_infraction(_id):
    """Closes a case."""
    data = {"_id": int(_id), "expiry": "False"}
    table = db["moderation"]
    await table.update(["_id"], **data)


async def is_logging_enabled(guildid):
    """Is it?"""
    return bool(await find_settings_channels(guildid, "moderation"))


async def find_reminder(id_):
    """Finds a reminder by id."""
    table = db['reminders']
    res = await table.find_one(_id=id_)
    if res:
        return dict(res)
    else:
        return None


async def find_reminders_for_user(id_):
    """Finds all reminders for a user."""
    table = db['reminders']
    res = await table.find(user=id_)
    if res:
        return [dict(i) for i in res]
    else:
        return None


async def negate_reminder(_id):
    """Deletes a reminder by id."""
    table = db['reminders']
    await table.delete(_id=_id)


async def return_all_expiring_reminders():
    """Returns all expiring reminders."""
    statement = "SELECT * FROM reminders WHERE NOT (expiry = 'False')"
    return await db.fetch_query(statement)


async def add_reminder(authorid, reason, date, issued):
    """Adds a reminder."""
    data = {"user": str(authorid), "expiry": str(date), "reason": reason, "issued": str(issued)}
    table = db['reminders']
    await table.insert(**data)


async def blacklist_add(id_, type_) -> None:
    """Adds an ID to the blacklist."""
    data = {"bannedid": str(id_), "type": type_}
    table = db['blacklists']
    await table.insert(**data)


async def is_not_blacklisted(id_, type_) -> bool:
    """Returns whether an ID has permission to use a command."""
    data = {"bannedid": str(id_), "type": type_}
    table = db['blacklists']
    res = await table.find(**data)
    if list(res):
        return False
    else:
        return True


async def blacklist_remove(id_, type_) -> None:
    """Nukes an ID from the blacklist."""
    data = {"bannedid": str(id_), "type": type_}
    table = db['blacklists']
    await table.delete(**data)


async def find_welcome_message(guilidid: str, message: str):
    data = {"guild": str(guilidid), "message": message}
    table = db['welcomemessages']
    res = await table.find(**data)
    if not res:
        return None
    else:
        return res


async def add_welcome_message(guilidid: str, message: str) -> None:
    data = {"guild": str(guilidid), "message": message}
    table = db['welcomemessages']
    await table.insert(**data)


async def remove_welcome_message(guilidid: str, message: str):
    data = {"guild": str(guilidid), "message": message}
    table = db['welcomemessages']
    res = await find_welcome_message(guilidid, message)
    if res:
        await table.delete(**data)
        return True
    else:
        return False


async def all_welcome_messages_for_guild(guilidid: str):
    table = db['welcomemessages']
    res = await table.find(guild=guilidid)
    return res or None


async def query_db(expr: str):
    return db.query(expr)


async def add_blueprint(guildid: str, command: str, key: str, value: str, requires: bool):
    """Adds a blueprint to a command."""
    table = db['blueprints']
    data = {
        "guildid": guildid, "command": command, "criteria_type": key,
        "criteria_value": value, "criteria_requires": requires}

    await table.insert(**data)


async def blueprints_for(guildid: str, command: str):
    """Returns blueprints needed for a command to run"""
    table = db['blueprints']
    data = {"guildid": guildid, "command": command}
    res = await table.find(**data)
    return res or None


async def blueprints_for_guild(guildid: str):
    """Returns all blueprints for a guild."""
    table = db['blueprints']
    data = {"guildid": guildid}
    res = await table.find(**data)
    return res or None


async def blueprint_by_id(_id: str):
    """Returns a blueprint by ID."""
    table = db['blueprints']
    data = {"_id": _id}
    res = table.find(**data)
    return res[0] if res else None


async def clear_blueprints_for(guildid: str, command: str):
    """Removes blueprints for a command."""
    table = db['blueprints']
    res = await blueprints_for(guildid, command)
    if res:
        data = {"guildid": guildid, "command": command}
        await table.delete(**data)


async def clear_blueprint(guildid: str, _id: str):
    """Removes a blueprint by id."""
    table = db['blueprints']
    data = {"guildid": guildid, "_id": _id}
    await table.delete(**data)


async def retrieve_ooeric():
    """More."""
    table = db['ooer']
    data = {"ooer": "ooer"}
    res = await table.find(**data)
    return int(res[0])["amount"] if res else 0


async def ooeric():
    """More."""
    table = db['ooer']
    data = {"ooer": "ooer"}
    current = await retrieve_ooeric()
    data["amount"] = current + 1
    await table.upsert(["ooer"], **data)
    return current + 1


async def add_investment_subreddit(userid, sub):
    table = db["favourite_subreddits"]
    data = {"user": userid, "subreddit": sub}
    await table.upsert(["user", "subreddit"], **data)


async def remove_investment_subreddit(userid, sub):
    table = db["favourite_subreddits"]
    data = {"user": userid, "subreddit": sub}
    await table.delete(**data)


async def all_investment_subreddits(userid):
    table = db["favourite_subreddits"]
    res = await table.find(user=userid)
    return [item["subreddit"] for item in res] if res else None


async def find_settings_channels(guildid, channeltype=None):
    table = db["settings_channels"]
    data = {"guild": guildid}
    if channeltype:
        data["type"] = channeltype

    return await table.find(**data)


async def add_settings_channel(guildid, channelid, channeltype):
    table = db["settings_channels"]
    data = {"guild": guildid, "channel": channelid, "type": channeltype}
    existing = await find_settings_channels(guildid, channeltype)

    if (channeltype != "archives" and len(existing) <= 4) or (channeltype == "archives" and len(existing) == 0):
        await table.upsert(["channel", "type"], **data)
        return True
    else:
        return False


async def remove_settings_channel(guildid, channelid, channeltype):
    table = db["settings_channels"]
    data = {"guild": guildid, "channel": channelid, "type": channeltype}
    await table.delete(**data)


async def wipe_settings_channel(guildid, channeltype):
    table = db["settings_channels"]
    data = {"guild": guildid, "type": channeltype}
    await table.delete(**data)
