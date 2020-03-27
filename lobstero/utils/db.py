"""Provides an entire suite of abstracted database functions.
Entirely useless for anything else."""

import sys
import json
import calendar
from unittest import mock
from collections import OrderedDict
from typing import Optional, Type, Mapping, Sequence

import pendulum
import dataset
from aioify import aioify
from dataset.util import ResultIter
from lobstero.utils import misc

root_directory = sys.path[0] + "/"

db = dataset.connect('sqlite:///' + root_directory + 'data.db')


def economy_manipulate(user_id, amount) -> None:
    """Changes how rich someone is or isn't"""
    table = db['ecodata']
    user_id = str(user_id)
    amount = int(amount)
    data = dict(userid=user_id, balance=economy_check(user_id) + amount)
    table.upsert(data, ['userid'])


def economy_set(user_id, amount) -> None:
    """Forced redistribution of wealth."""
    table = db['ecodata']
    user_id = str(user_id)
    amount = int(amount)
    data = dict(userid=user_id, balance=amount)
    table.upsert(data, ['userid'])


def economy_check(user_id) -> int:
    """Knock knock, it's the IRS."""
    table = db['ecodata']
    user_id = str(user_id)
    result = list(table.find(userid=user_id))
    if not result:
        return 0
    else:
        return result[0]["balance"]


def return_all_balances() -> list:
    """It's a big deal for the bank."""
    balancelist = []
    results = list(db['ecodata'].all())
    for x in results:
        balancelist.append([x["balance"], x["userid"]])
    for _ in range(5):
        balancelist.append([0, 486309010447007756])
    return sorted(balancelist, key=lambda x: x[0], reverse=True)


def set_tag(serverid, tagname, tagvalue) -> None:
    """Sets the value of a tag."""
    table = db["tagdata"]
    data = dict(tag=tagname.lower(), value=tagvalue, guildid=serverid)
    table.upsert(data, ['tag'])


def return_tag(serverid, tagname) -> Optional[str]:
    """Returns the value of a tag."""
    table = db["tagdata"]
    result = list(table.find(tag=tagname.lower(), guildid=serverid))
    if not result:
        return None
    else:
        return result[0]["value"]


def delete_tag(serverid, tagname) -> None:
    """Deletes a tag."""
    table = db["tagdata"]
    table.delete(tag=tagname.lower(), guildid=serverid)


def return_all_tags(serverid) -> list:
    """I really wouldn't be giving these docstrings if my linter didn't annoy me about it."""
    table = db["tagdata"]
    taglist = []
    results = list(table.find(guildid=serverid))
    for x in results:
        taglist.append([x["tag"], x["value"]])
    return taglist


def add_gnome(user_id, amount) -> int:
    """Adds a gnome to a user's gnome count."""
    gnometable = db['gnomedata']
    user_id = str(user_id)
    amount = int(amount)
    data = dict(userid=user_id, gnomeamount=gnome_check(user_id) + amount)
    gnometable.upsert(data, ['userid'])
    return gnome_check(user_id)


def gnome_check(user_id) -> int:
    """Returns a user's gnome count."""
    gnometable = db['gnomedata']
    user_id = str(user_id)
    result = list(gnometable.find(userid=user_id))
    if not result:
        return 0
    else:
        return result[0]["gnomeamount"]


def return_all_gnomes() -> list:
    """Returns all gnomes to the local gardenware shop. They were faulty."""
    gnometable = db['gnomedata']
    balancelist = []
    results = list(gnometable.all())
    for x in results:
        balancelist.append([x["gnomeamount"], x["userid"]])
    for i in range(5):
        balancelist.append([0, 486309010447007756])
    return sorted(balancelist, key=lambda x: x[0], reverse=True)


def afk_message_set(user_id, text) -> None:
    """Sets a custom AFK-removal message for a user"""
    afktable = db['afkmessagelist']
    data = dict(userid=user_id, message=text)
    afktable.upsert(data, ['userid'])


def return_afk_message(user_id) -> Optional[str]:
    """Returns a user's custom AFk-removal message"""
    afktable = db['afkmessagelist']
    result = list(afktable.find(userid=user_id))
    if not result:
        return None
    else:
        return result[0]["message"]


def return_fishing_bal(userid: int) -> Type[OrderedDict]:
    """I'm gonna get rid of this soon. Returns how many fish you have."""
    table = db['fishdata']
    for x in table.all():
        if str(x['userid']) == str(userid):
            return x

    return None


def fishedit(userid: int, fishtype, amount=1) -> None:
    """Edits how many fish a user has. They're bionic!"""
    table = db['fishdata']

    result = None

    for x in table.all():
        if str(x['userid']) == str(userid):
            result = x

    try:
        oldval = result[fishtype]
    except KeyError:
        oldval = 0

    if oldval is None:
        oldval = 0

    data = {"userid": userid, fishtype: oldval + amount}

    table.upsert(data, ["userid"])


def settings_values() -> Type[ResultIter]:
    """Returns settings values for everyone."""
    table = db['serversettings']
    return table.all()


def settings_value_for_guild(serverid) -> Type[ResultIter]:
    """Returns settings values for just one server."""
    table = db['serversettings']
    return table.find_one(serverid=serverid)


def edit_settings_value(serverid: int, val: str, new) -> None:
    """Edits a settings value."""
    table = db['serversettings']
    data = {"serverid": serverid, val: new}
    table.upsert(data, ["serverid"])


def give_table() -> Mapping[str, OrderedDict]:
    """Chucks a table at you out of sheer rage."""
    return {x["serverid"]: x for x in settings_values()}


def assignables_add(serverid: int, mid: str) -> None:
    """Adds an assignable role to a server. I'm going to change how these are stored in a while."""
    table = db['serversettings']
    mlist = assignables_check(serverid)
    if mid not in mlist:
        mlist.append(mid)
        data = dict(serverid=serverid, assignables=json.dumps([str(x) for x in mlist]))
        table.upsert(data, ['serverid'])


def assignables_remove(serverid: int, mid: str) -> None:
    """Removes an assignable role from a server. See above docstring."""
    table = db['serversettings']
    if mid in assignables_check(serverid):
        mlist = assignables_check(serverid)
        for index, x in enumerate(mlist):
            if str(x) == str(mid):
                del mlist[index]
        data = dict(serverid=serverid, assignables=json.dumps([str(x) for x in mlist]))
        table.upsert(data, ['serverid'])


def assignables_clear(serverid: int) -> None:
    """Assignables? Never heard of 'er."""
    table = db['serversettings']
    data = dict(serverid=serverid, assignables="")
    table.upsert(data, ['serverid'])


def assignables_check(serverid: int) -> Optional[list]:
    """Gives you all the assignables."""
    table = db['serversettings']
    result = list(table.find(serverid=serverid))
    if not result:
        return []
    else:
        try:
            v = json.loads(result[0]["assignables"])
            for index, x in enumerate(v):
                if x == "":
                    del v[index]
            return v
        except KeyError:
            return []


def return_server_reacts_list(serverid: str) -> Sequence[OrderedDict]:
    """Reactions mapped by server."""
    return [x for x in db["customreacts"].find(guildid=serverid)]


def find_matching_response(serverid: str, trigger) -> list:
    """Finds a response."""
    table = db["customreacts"]
    result = list(table.find(trigger=trigger, guildid=serverid))
    if len(result) < 1:
        return []
    else:
        return json.loads(result[0]["response"])


def raw_find_matching_response(serverid: str, trigger):
    """The same as above, but raw-er."""
    table = db["customreacts"]
    result = list(table.find(trigger=trigger, guildid=serverid))
    if len(result) < 1:
        return []
    else:
        return result[0]


def add_reaction(serverid, trigger, value, mtype=None) -> None:
    """Adds a custom reaction."""
    table = db["customreacts"]
    val = find_matching_response(str(serverid), trigger)
    val.append(value)
    newdata = {"trigger": trigger, "response": json.dumps(val), "guildid": serverid}
    if mtype is not None:
        newdata["type"] = mtype

    table.upsert(newdata, ["trigger"])


def remove_response(serverid, trigger, index: int, mtype) -> None:
    """Removes a response from a custom reaction."""
    table = db["customreacts"]
    val = find_matching_response(serverid, trigger)
    del val[index]
    newdata = {
        "trigger": trigger,
        "response": json.dumps(val),
        "type": mtype,
        "guildid": serverid}

    table.upsert(newdata, ["trigger"])


def remove_reaction(serverid, trigger) -> None:
    """Removes a custom reaction entirely."""
    table = db["customreacts"]
    table.delete(trigger=trigger, guildid=serverid)


def deny_list_all() -> Mapping[str, OrderedDict]:
    """Returns denied channels."""
    return {str(x["serverid"]): x for x in db["deniedchannels"].all()}


def is_denied(serverid, channelid) -> bool:
    """Can we do the thing there?"""
    denied = deny_list_all()
    if str(serverid) in denied:
        unpacked = [str(x) for x in json.loads(denied[str(serverid)]["channels"])]
        return str(channelid) in unpacked
    else:
        return False


def add_new_deny_channel(serverid: str, channelid) -> None:
    """Denies a channel."""
    denied = deny_list_all()
    table = db["deniedchannels"]

    if str(serverid) in denied:
        unpacked = json.loads(denied[str(serverid)]["channels"])
    else:
        unpacked = []

    unpacked.append(str(channelid))
    newdata = {"serverid": str(serverid), "channels": json.dumps(unpacked)}
    table.upsert(newdata, ["serverid"])


def remove_deny_channel(serverid: str, channelid) -> None:
    """I'm denying my denial,"""
    denied = deny_list_all()
    table = db["deniedchannels"]

    if str(serverid) in denied:
        unpacked = json.loads(denied[str(serverid)]["channels"])
        if str(channelid) in unpacked:
            for index, x in enumerate(unpacked):
                if str(channelid) == x:
                    del unpacked[index]
                    newdata = {"serverid": serverid, "channels": json.dumps(unpacked)}
                    table.upsert(newdata, ["serverid"])
                    return


def prefix_list() -> Mapping[str, OrderedDict]:
    """List of prefixes."""
    return {str(x["serverid"]): x for x in db["prefixes"].all()}


def add_prefix(serverid: int, prefix: str) -> None:
    """Adds a prefix."""
    table = db["prefixes"]
    table.upsert({"serverid": serverid, "prefix": prefix}, ["serverid"])


def find_inventory(userid: str) -> Optional:
    """Because you lost it."""
    table = db["inventory"]
    result = list(table.find(userid=str(userid)))
    if len(result) < 1:
        return []
    else:
        return json.loads(result[0]["item"])


def grant_item(userid: str, item: str, count: int) -> None:
    """Gives you something."""
    table = db["inventory"]
    current = find_inventory(userid)
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
    table.upsert(newdata, ["userid"])


def remove_item(userid: str, item: str, count: int) -> bool:
    """What can be given can also be taken away."""
    table = db["inventory"]
    current = find_inventory(userid)
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
    table.upsert(newdata, ["userid"])

    return removed


def retrieve_location(userid: str) -> str:
    """Ok google, where am I?"""
    table = db["inventory"]
    result = list(table.find(userid=userid))
    if result:
        return "undergrowth"
    else:
        return result[0]["location"]


def set_location(userid: str, place: str) -> None:
    """Teleportation or something."""
    table = db["inventory"]
    newdata = {"userid": userid, "location": place}
    table.upsert(newdata, "userid")


def log_infraction(operation, guildid: int, userid: int, staffid: int, reason, expires="False", redacted="False"):
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
    table.insert(data)


def find_infraction(operation, guildid, userid, id_):
    """Finds a very specific infraction."""
    table = db['moderation']
    res = table.find_one(operation=operation, guild=guildid, user=userid, id=id_)
    if res:
        return dict(res)
    else:
        return None


def find_specific_infraction(id_):
    """Finds a slightly specific infraction"""
    table = db['moderation']
    res = table.find_one(id=id_)
    if res:
        return dict(res)
    else:
        return None


def find_all_infractions(guildid, operation=None):
    """All the wrongdoings."""
    table = db['moderation']
    res = list(table.find(guild=guildid))
    if operation:
        return [item for item in res if item["operation"] == operation]
    else:
        return res


def find_all_member_infractions(guildid, memberid, operation=None):
    """Finds wrongdoings for a specific guy."""
    table = db['moderation']
    res = list(table.find(guild=guildid, user=memberid))
    if operation:
        return [item for item in res if item["operation"] == operation]
    else:
        return res


def strike_infraction(operation, guildid, userid, id_, new: bool = True):
    """Proverbially crosses out an infraction."""
    table = db['moderation']
    r = find_infraction(operation, guildid, userid, id_)
    r["redacted"] = str(new)
    table.upsert(r, ["id"])


async def return_all_expiring_infractions():
    """What will go wrong, when?"""
    statement = "SELECT * FROM moderation WHERE NOT (expiry = 'False')"
    return list(db.query(statement))


def close_infraction(_id):
    """Closes a case."""
    data = {"id": int(_id), "expiry": "False"}
    table = db['moderation']
    table.update(data, ["id"])


def is_logging_enabled(guildid):
    """Is it?"""
    res = settings_value_for_guild(guildid)
    if res:
        if "moderationlogs" in res:
            if res["moderationlogs"] is not None:
                return (True, json.loads(res["moderationlogs"]))

    return (False, False)


def find_reminder(id_):
    """Finds a reminder by id."""
    table = db['reminders']
    res = table.find_one(id=id_)
    if res:
        return dict(res)
    else:
        return None


def find_reminders_for_user(id_):
    """Finds all reminders for a user."""
    table = db['reminders']
    res = table.find(user=id_)
    if res:
        return [dict(i) for i in res]
    else:
        return None


def negate_reminder(_id):
    """Deletes a reminder by id."""
    table = db['reminders']
    table.delete(id=_id)


async def return_all_expiring_reminders():
    """Returns all expiring reminders."""
    statement = "SELECT * FROM reminders WHERE NOT (expiry = 'False')"
    return list(db.query(statement))


def add_reminder(authorid, reason, date, issued):
    """Adds a reminder."""
    data = {"user": str(authorid), "expiry": str(date), "reason": reason, "issued": str(issued)}
    table = db['reminders']
    table.insert(data)


def blacklist_add(id_, type_) -> None:
    """Adds an ID to the blacklist."""
    data = {"bannedid": str(id_), "type": type_}
    table = db['blacklists']
    table.insert(data)


def is_not_blacklisted(id_, type_) -> bool:
    """Returns whether an ID has permission to use a command."""
    data = {"bannedid": str(id_), "type": type_}
    table = db['blacklists']
    res = table.find(**data)
    if list(res):
        return False
    else:
        return True


def blacklist_remove(id_, type_) -> None:
    """Nukes an ID from the blacklist."""
    data = {"bannedid": str(id_), "type": type_}
    table = db['blacklists']
    table.delete(**data)


def find_welcome_message(guilidid: str, message: str):
    data = {"guild": str(guilidid), "message": message}
    table = db['welcomemessages']
    res = table.find(**data)
    if not res:
        return None
    else:
        return res


def add_welcome_message(guilidid: str, message: str) -> None:
    data = {"guild": str(guilidid), "message": message}
    table = db['welcomemessages']
    table.insert(data)


def remove_welcome_message(guilidid: str, message: str):
    data = {"guild": str(guilidid), "message": message}
    table = db['welcomemessages']
    res = find_welcome_message(guilidid, message)
    if res:
        table.delete(**data)
        return True
    else:
        return False


def all_welcome_messages_for_guild(guilidid: str):
    table = db['welcomemessages']
    res = table.find(guild=guilidid)
    if res:
        return res
    else:
        return None


def query_db(expr: str):
    return db.query(expr)


def add_vault_note(ownerid: str, title: str, content: str):
    rn = pendulum.now("Atlantic/Reykjavik")  # utc+0 baybee
    data = {"userid": ownerid, "title": title, "content": content, "added": str(rn)}
    table = db['vault']
    table.upsert(data, ["userid", "title"])


def add_blueprint(guildid: str, command: str, key: str, value: str, requires: bool):
    """Adds a blueprint to a command."""
    table = db['blueprints']
    data = {
        "guildid": guildid, "command": command, "criteria_type": key,
        "criteria_value": value, "criteria_requires": requires}

    table.insert(data)


def blueprints_for(guildid: str, command: str):
    """Returns blueprints needed for a command to run"""
    table = db['blueprints']
    data = {"guildid": guildid, "command": command}
    res = table.find(**data)
    if res:
        return list(res)
    else:
        return None


def blueprints_for_guild(guildid: str):
    """Returns all blueprints for a guild."""
    table = db['blueprints']
    data = {"guildid": guildid}
    res = table.find(**data)
    if res:
        return list(res)
    else:
        return None


def blueprint_by_id(_id: str):
    """Returns a blueprint by ID."""
    table = db['blueprints']
    data = {"id": _id}
    res = table.find(**data)
    if res:
        return list(res)[0]
    else:
        return None


def clear_blueprints_for(guildid: str, command: str):
    """Removes blueprints for a command."""
    table = db['blueprints']
    res = blueprints_for(guildid, command)
    if res:
        data = {"guildid": guildid, "command": command}
        table.delete(**data)


def clear_blueprint(guildid: str, _id: str):
    """Removes a blueprint by id."""
    table = db['blueprints']
    data = {"guildid": guildid, "id": _id}
    table.delete(**data)


def retrieve_ooeric():
    """More."""
    table = db['ooer']
    data = {"ooer": "ooer"}
    res = table.find(**data)
    if res:
        return int(list(res)[0]["amount"])
    else:
        return 0


def ooeric():
    """More."""
    table = db['ooer']
    data = {"ooer": "ooer"}
    current = retrieve_ooeric()
    data["amount"] = current + 1
    table.upsert(data, ["ooer"])
    return current + 1


def add_investment_subreddit(userid, sub):
    table = db["favourite_subreddits"]
    data = {"user": userid, "subreddit": sub}
    table.upsert(data, ["user", "subreddit"])


def remove_investment_subreddit(userid, sub):
    table = db["favourite_subreddits"]
    data = {"user": userid, "subreddit": sub}
    table.delete(**data)


def all_investment_subreddits(userid):
    table = db["favourite_subreddits"]
    res = table.find(user=userid)
    if res:
        return [item["subreddit"] for item in res]
    else:
        return None


def find_settings_channels(guildid, channeltype=None):
    table = db["settings_channels"]
    data = {"guild": guildid}
    if channeltype:
        data["type"] = channeltype

    res = table.find(**data)
    if res:
        return list(res)
    else:
        return []


def add_settings_channel(guildid, channelid, channeltype):
    table = db["settings_channels"]
    data = {"guild": guildid, "channel": channelid, "type": channeltype}
    existing = find_settings_channels(guildid, channeltype)

    if channeltype != "archives" and len(existing) <= 4 or channeltype == "archives" and len(existing) == 0:
        table.upsert(data)
        return True
    else:
        return False


def remove_settings_channel(guildid, channelid, channeltype):
    table = db["settings_channels"]
    data = {"guild": guildid, "channel": channelid, "type": channeltype}
    table.delete(data)


def wipe_settings_channel(guildid, channeltype):
    table = db["settings_channels"]
    data = {"guild": guildid, "type": channeltype}
    table.delete(data)


def add_investment(userid, submissionid):
    pass


aio = mock.Mock()
this_module = sys.modules[__name__]
for name in dir():
    this_item = getattr(this_module, name, None)
    m = getattr(this_item, "__module__", None)
    if m == "lobstero.utils.db":  # could probably replace this with __name__, lazy
        setattr(aio, name, aioify(obj=this_item, name=name))
