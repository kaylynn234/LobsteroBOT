"""A bunch of text. Be glad it's here and not elsewhere."""
# fuck pep8

moderation_mapping = {
    "warn": "Warnings",
    "mute": "Mutes",
    "deafen": "Deafens",
    "kick": "Kicks",
    "ban": "Bans",
    "softban": "Softbans"
}

memelist = [
    "10 Guy", "https://memegen.link/api/templates/tenguy",
    "Afraid to Ask Andy", "https://memegen.link/api/templates/afraid",
    "Almost Politically Correct Redneck", "https://memegen.link/api/templates/apcr",
    "An Older Code Sir, But It Checks Out", "https://memegen.link/api/templates/older",
    "Ancient Aliens Guy", "https://memegen.link/api/templates/aag",
    "And Then I Said", "https://memegen.link/api/templates/atis",
    "At Least You Tried", "https://memegen.link/api/templates/tried",
    "Baby Insanity Wolf", "https://memegen.link/api/templates/biw",
    "Baby, You've Got a Stew Going", "https://memegen.link/api/templates/stew",
    "Bad Luck Brian", "https://memegen.link/api/templates/blb",
    "But That's None of My Business", "https://memegen.link/api/templates/kermit",
    "Butthurt Dweller", "https://memegen.link/api/templates/bd",
    "Captain Hindsight", "https://memegen.link/api/templates/ch",
    "Comic Book Guy", "https://memegen.link/api/templates/cbg",
    "Condescending Wonka", "https://memegen.link/api/templates/wonka",
    "Confession Bear", "https://memegen.link/api/templates/cb",
    "Confused Gandalf", "https://memegen.link/api/templates/gandalf",
    "Conspiracy Keanu", "https://memegen.link/api/templates/keanu",
    "Crying on Floor", "https://memegen.link/api/templates/cryingfloor",
    "Dating Site Murderer", "https://memegen.link/api/templates/dsm",
    "Disaster Girl", "https://memegen.link/api/templates/disastergirl",
    "Do It Live!", "https://memegen.link/api/templates/live",
    "Do You Want Ants?", "https://memegen.link/api/templates/ants",
    "Doge", "https://memegen.link/api/templates/doge",
    "Donald Trump", "https://memegen.link/api/templates/trump",
    "Drakeposting", "https://memegen.link/api/templates/drake",
    "Ermahgerd", "https://memegen.link/api/templates/ermg",
    "Facepalm", "https://memegen.link/api/templates/facepalm",
    "First Try!", "https://memegen.link/api/templates/firsttry",
    "First World Problems", "https://memegen.link/api/templates/fwp",
    "Forever Alone", "https://memegen.link/api/templates/fa",
    "Foul Bachelor Frog", "https://memegen.link/api/templates/fbf",
    "Futurama Fry", "https://memegen.link/api/templates/fry",
    "Good Guy Greg", "https://memegen.link/api/templates/ggg",
    "Grumpy Cat", "https://memegen.link/api/templates/grumpycat",
    "Hide the Pain Harold", "https://memegen.link/api/templates/harold",
    "Hipster Barista", "https://memegen.link/api/templates/hipster",
    "I Can Has Cheezburger?", "https://memegen.link/api/templates/icanhas",
    "I Feel Like I'm Taking Crazy Pills", "https://memegen.link/api/templates/crazypills",
    "I Guarantee It", "https://memegen.link/api/templates/mw",
    "I Have No Idea What I'm Doing", "https://memegen.link/api/templates/noidea",
    "I Immediately Regret This Decision!", "https://memegen.link/api/templates/regret",
    "I Should Buy a Boat Cat", "https://memegen.link/api/templates/boat",
    "I Should Not Have Said That", "https://memegen.link/api/templates/hagrid",
    "I Would Be So Happy", "https://memegen.link/api/templates/sohappy",
    "I am the Captain Now", "https://memegen.link/api/templates/captain",
    "I'm Going to Build My Own Theme Park", "https://memegen.link/api/templates/bender",
    "Inigo Montoya", "https://memegen.link/api/templates/inigo",
    "Insanity Wolf", "https://memegen.link/api/templates/iw",
    "It's A Trap!", "https://memegen.link/api/templates/ackbar",
    "It's Happening", "https://memegen.link/api/templates/happening",
    "It's Simple, Kill the Batman", "https://memegen.link/api/templates/joker",
    "Laughing Lizard", "https://memegen.link/api/templates/ll",
    "Laundry Room Viking", "https://memegen.link/api/templates/lrv",
    "Leo Strutting", "https://memegen.link/api/templates/leo",
    "Life... Finds a Way", "https://memegen.link/api/templates/away",
    "Matrix Morpheus", "https://memegen.link/api/templates/morpheus",
    "Member Berries", "https://memegen.link/api/templates/mb",
    "Milk Was a Bad Choice", "https://memegen.link/api/templates/badchoice",
    "Minor Mistake Marvin", "https://memegen.link/api/templates/mmm",
    "Mocking Spongebob", "https://memegen.link/api/templates/spongebob",
    "No Soup for You / Soup Nazi", "https://memegen.link/api/templates/soup-nazi",
    "Nothing To Do Here", "https://memegen.link/api/templates/jetpack",
    "Oh, I'm Sorry, I Thought This Was America", "https://memegen.link/api/templates/imsorry",
    "Oh, Is That What We're Going to Do Today?", "https://memegen.link/api/templates/red",
    "One Does Not Simply Walk into Mordor", "https://memegen.link/api/templates/mordor",
    "Oprah You Get a Car", "https://memegen.link/api/templates/oprah",
    "Overly Attached Girlfriend", "https://memegen.link/api/templates/oag",
    "Pepperidge Farm Remembers", "https://memegen.link/api/templates/remembers",
    "Persian Cat Room Guardian", "https://memegen.link/api/templates/persian",
    "Philosoraptor", "https://memegen.link/api/templates/philosoraptor",
    "Probably Not a Good Idea", "https://memegen.link/api/templates/jw",
    "Push it somewhere else Patrick", "https://memegen.link/api/templates/patrick",
    "Roll Safe", "https://memegen.link/api/templates/rollsafe",
    "Sad Barack Obama", "https://memegen.link/api/templates/sad-obama",
    "Sad Bill Clinton", "https://memegen.link/api/templates/sad-clinton",
    "Sad Frog / Feels Bad Man", "https://memegen.link/api/templates/sadfrog",
    "Sad George Bush", "https://memegen.link/api/templates/sad-bush",
    "Sad Joe Biden", "https://memegen.link/api/templates/sad-biden",
    "Sad John Boehner", "https://memegen.link/api/templates/sad-boehner",
    "Salt Bae", "https://memegen.link/api/templates/saltbae",
    "Sarcastic Bear", "https://memegen.link/api/templates/sarcasticbear",
    "Schrute Facts", "https://memegen.link/api/templates/dwight",
    "Scumbag Brain", "https://memegen.link/api/templates/sb",
    "Scumbag Steve", "https://memegen.link/api/templates/ss",
    "Seal of Approval", "https://memegen.link/api/templates/soa",
    "Sealed Fate", "https://memegen.link/api/templates/sf",
    "See? Nobody Cares", "https://memegen.link/api/templates/dodgson",
    "Shut Up and Take My Money!", "https://memegen.link/api/templates/money",
    "Skeptical Snake", "https://memegen.link/api/templates/snek",
    "Skeptical Third World Kid", "https://memegen.link/api/templates/sk",
    "So Hot Right Now", "https://memegen.link/api/templates/sohot",
    "So I Got That Goin' For Me, Which is Nice", "https://memegen.link/api/templates/nice",
    "Socially Awesome Awkward Penguin", "https://memegen.link/api/templates/awesome-awkward",
    "Socially Awesome Penguin", "https://memegen.link/api/templates/awesome",
    "Socially Awkward Awesome Penguin", "https://memegen.link/api/templates/awkward-awesome",
    "Socially Awkward Penguin", "https://memegen.link/api/templates/awkward",
    "Stop It, Get Some Help", "https://memegen.link/api/templates/stop-it",
    "Stop Trying to Make Fetch Happen", "https://memegen.link/api/templates/fetch",
    "Success Kid", "https://memegen.link/api/templates/success",
    "Sudden Clarity Clarence", "https://memegen.link/api/templates/scc",
    "Super Cool Ski Instructor", "https://memegen.link/api/templates/ski",
    "Sweet Brown / Ain't Nobody Got Time For That", "https://memegen.link/api/templates/aint-got-time",
    "That Would Be Great", "https://memegen.link/api/templates/officespace",
    "The Most Interesting Man in the World", "https://memegen.link/api/templates/interesting",
    "The Rent Is Too Damn High", "https://memegen.link/api/templates/toohigh",
    "This is Bull, Shark", "https://memegen.link/api/templates/bs",
    "This is Fine", "https://memegen.link/api/templates/fine",
    "This is Sparta!", "https://memegen.link/api/templates/sparta",
    "Ugandan Knuckles", "https://memegen.link/api/templates/ugandanknuck",
    "Unpopular opinion puffin", "https://memegen.link/api/templates/puffin",
    "What Year Is It?", "https://memegen.link/api/templates/whatyear",
    "What is this, a Center for Ants?!", "https://memegen.link/api/templates/center",
    "Why Not Both?", "https://memegen.link/api/templates/both",
    "Winter is coming", "https://memegen.link/api/templates/winter",
    "X all the Y", "https://memegen.link/api/templates/xy",
    "X, X Everywhere", "https://memegen.link/api/templates/buzz",
    "Xzibit Yo Dawg", "https://memegen.link/api/templates/yodawg",
    "Y U NO Guy", "https://memegen.link/api/templates/yuno",
    "Y'all Got Any More of Them", "https://memegen.link/api/templates/yallgot",
    "You Should Feel Bad", "https://memegen.link/api/templates/bad",
    "You Sit on a Throne of Lies", "https://memegen.link/api/templates/elf",
    "You Were the Chosen One!", "https://memegen.link/api/templates/chosen"]

quotelist = [
    "your actions have consequences.",
    "there is no salvation for your crimes.",
    "there is no place to hide.",
    "I know your every move.",
    "you can't run from your past.",
    "did you really think there would be no repercussions?",
    "there is no hope for you.",
    "your fate has been sealed."]

estr = """☺☻😃😄😅😆😊😎😇😈😋😏😌😁😀😂🤣🤠🤡🤑🤩🤪😳😉😗😚😘😙😍🤤
🤗😛😜😝😶🙃😐😑🤔🙄😮😔😖😕🤨🤯🤭🧐🤫😯🤐😩😫😪😴😵😦😢😭🤢
🤮😷🤒🤕😒😠😡😤😣😧🤬😬😓😰😨😱😲😞😥😟🤥🤓🤖😸😹😺😻😼😽😾
😿🙀🙈🙉🙊🐰🤦🤷🙅🙆🙋🙌🙍🙎🙇🙏🤳💃🕺💆💇💈🧖🧘👰🤰🤱👯👶🧒
👦👩👨👧🧔🧑🧓👴👵👤👥👪👫👬👭👲👳🧕👱🤴👸🤵🎅🤶👮👷💁💂🕴🕵
👼👻🧙🧚🧛🧜🧝🧞🧟👿💀☠🕱🕲👽👾🛸👹👺🧠👁👀👂👃👄🗢👅💬💭🗨
🗩🗪🗫🗬🗭🗮🗯🗰🗱🗣🗤🗥🗦🗧💢💦💧💫💤💥💨💪🗲🔥💡💩💯🔟🔰🕃🕄🕅🕉"""

emotes = [x for x in estr]

fishdict = {
    "fish1": "<:fish1:614648232978677792>", "fish2": "<:fish2:614648235100733450>",
    "fish3": "<:fish3:614648235084087296>", "fish4": "<:fish4:614648232894529543>",
    "fish5": "<:fish5:614648234517987338>", "fish6": "<:fish6:614648235587534893>",
    "fish7": "<:fish7:614648238343192595>", "shoe": "👢", "glasses": "👓"}

fish_names = {
    "shoe": "Well-worn leather boot",
    "glasses": "Ancient pair of glasses",
    "fish1": "Red trout",
    "fish2": "Exemplary tuna",
    "fish3": "Agile cod",
    "fish4": "Odd-looking salmon",
    "fish5": "Peculiar barramundi",
    "fish6": "Weird carp",
    "fish7": "Ultimate Catch"
}

bedtime_url = (
    "https://cdn.discordapp.com/attachments/506665745229545472"
    "/616174546780946432/549161.png")

mod_id_invalid = "Make sure to provide a valid infraction ID when using this command."
mod_not_number = "That's not a number! Make sure to provide a valid infraction ID when using this command."
mod_none_matching = "Couldn't find an infraction with a matching ID. Make sure to provide a valid infraction ID when using this command."
mod_on_other_guild = "An infraction with this ID exists, but belongs to another server and cannot be viewed."
mod_member_invalid = "Couldn't find a matching member. Make sure to provide a valid member name, mention, nickname or ID when using this command."
mod_none_assoc = "Couldn't find any infractions associated to this member."

action_softban = """
Please ensure that you have made the right decision - softbanning a user ejects them from this server and deletes all messages they have sent in the past 7 days. 
Note that softbans cannot be set to "expire," nor can they be timed in any way. 
However, softbans can be "striked" if need-be, or completely wiped by the server owner."""
action_ban = """
Please ensure that you have made the right decision - banning a user ejects them from this server and prevents them from rejoining. 
Deafens can be set to expire and "striked" if need-be, or comepletely wiped by the server owner."""
action_kick = """
Please ensure that you have made the right decision - kicking a user ejects them from this server. 
Note that kicks cannot be set to "expire," nor can they be timed in any way. 
However, kicks can be "striked" if need-be, or completely wiped by the server owner."""
action_deafen = """
Please ensure that you have made the right decision - deafening a user prevents them from seeing any channels.
Deafens can be set to expire and "striked" if need-be, or completely wiped by the server owner."""
action_mute = """
Please ensure that you have made the right decision - muting a user prevents them from speaking in any channels. 
Mutes can be set to expire and "striked" if need-be, or completely wiped by the server owner."""
action_warn = """
Please ensure that you have made the right decision. 
Note that warnings cannot be set to "expire," nor can they be timed in any way. 
However, warnings can be "striked" if need-be, or completely wiped by the server owner."""

mod_can_expire = """This punishment can \"expire\" - meaning the effects of it can automatically be undone in a certain period of time. 
Enter a period of time now if you'd wish to set an expiry - this can be something like \'in an hour\" or \"January 2020\". 
Alternatively, respond with gibberish or wait, and the punishment will not expire. This will time out in 10 seconds. """

mod_how_to = """Moderation is performed via subcommands - see ``<help m`` for more information.
Setting up channels for logging is done using ``<channels``. See ``<help channels set`` for more information."""

guess_what = """How do you want to guess? Respond with one of the numbers below to choose. 
Each method of guessing yields different risks and rewards, so be careful!

You can do the following:
**1**: Guess the suit of the card.
**2**: Guess the type of the card.
**3**: Guess the number on the card.
**4**: Guess the exact card (if you're in that kind of mood.)
**5**: I don't want to play. Let me out!"""

cardurls_1 = {
    "hearts": "https://cdn.discordapp.com/attachments/506665745229545472/589037648077783041/collection_hearts.png",
    "diamonds": "https://cdn.discordapp.com/attachments/506665745229545472/589037589709848596/collection_diamonds.png",
    "spades": "https://cdn.discordapp.com/attachments/506665745229545472/589037756957720576/collection_spades.png",
    "clubs" : "https://cdn.discordapp.com/attachments/506665745229545472/589037707695751169/collection_clubs.png"}

cardurls_2 = {
    "king": "https://cdn.discordapp.com/attachments/506665745229545472/589037648077783041/collection_hearts.png",
    "queen": "https://cdn.discordapp.com/attachments/506665745229545472/589037589709848596/collection_diamonds.png",
    "jack" : "https://cdn.discordapp.com/attachments/506665745229545472/589037756957720576/collection_spades.png",
    "ace": "https://cdn.discordapp.com/attachments/506665745229545472/589037707695751169/collection_clubs.png",
    "number": "https://cdn.discordapp.com/attachments/506665745229545472/589216141604290560/back_cards-07.png"}

cardurls_3 = "https://cdn.discordapp.com/attachments/506665745229545472/589216141604290560/back_cards-07.png"

cardurls_4 = "https://cdn.discordapp.com/attachments/506665745229545472/v589216141604290560/back_cards-07.png"

bp_id_invalid = "Make sure to provide a valid blueprint ID when using this command."
bp_not_number = "That's not a number! Make sure to provide a valid blueprint ID when using this command."
bp_none_matching = "Couldn't find an blueprint with a matching ID. Make sure to provide a valid blueprint ID when using this command."
bp_on_other_guild = "A blueprint with this ID exists, but belongs to another server and cannot be viewed."
bp_member_invalid = "Couldn't find a matching member. Make sure to provide a valid member name, mention, nickname or ID when using this command."
bp_none_assoc = "Couldn't find any blueprints associated to this command."
bp_what_type = """What criteria should this blueprint have?
1\N{combining enclosing keycap}: The author has/ does not have any role.
2\N{combining enclosing keycap}: The author has/ does not have a specific role.
3\N{combining enclosing keycap}: The author does/ does not have certain permissions in the channel the command is used in.
4\N{combining enclosing keycap}: The author does/ does not have certain permissions in the server the command is used in.
5\N{combining enclosing keycap}: The author is/is not a specific user.
6\N{combining enclosing keycap}: The author is/is not the server owner.

Use the reactions below to answer. You can configure the criteria further in the next step."""

bp_has_any_role = """How should the chosen criteria trigger?
✅: If the author has any role
🚫: If the author does not have any role

Use the reactions below to answer. """

bp_has_role = """How should the chosen criteria trigger?
✅: If the author has the role I specify
🚫: If the author does not have the role I specify

Use the reactions below to answer. The role can be chosen in the next step."""

bp_has_permissions = """How should the chosen criteria trigger?
✅: If the author has the permission I specify (in the channel the command is used in)
🚫: If the author does not have the permission I specify (in the channel the command is used in)

Use the reactions below to answer. The permission can be chosen in the next step."""

bp_has_strict_permissions = """How should the chosen criteria trigger?
✅: If the author has the permission I specify in this server
🚫: If the author does not have the permission I specify in this server

Use the reactions below to answer. The permission can be chosen in the next step."""

bp_is_specific_user = """How should the chosen criteria trigger?
✅: If the author is the member I specify
🚫: If the author is not the member I specify

Use the reactions below to answer. The member can be chosen in the next step."""

bp_is_guild_owner = """How should the chosen criteria trigger?
✅: If the author owns this server
🚫: If the author does not own this server

Use the reactions below to answer."""

bp_member_prompt = """Choose which member this criteria should apply to.
Respond to this message with either somebody's @mention, user ID, username or nickname.

Make sure your capitalization and spelling are both correct!"""

bp_role_prompt = """Choose which role this criteria should apply to.
Respond to this message with either a role's @mention, role ID or role name.

Make sure your capitalization and spelling are both correct!"""

bp_perm_prompt = """Choose which permission this criteria should apply to.
Respond to this message with any of the following:
%s

Make sure your capitalization and spelling are both correct!"""

really_awful_meme_subs = [
    "fffffffuuuuuuuuuuuu",
    "dogfort",
    "catfort",
    "memes",
    "dankmemes",
    "surrealmemes",
    "meirl",
    "2meirl4meirl",
    "adviceanimals",
    "inglip",
    "cursedimages",
    "blursedimages",
    "wholesomememes",
    "terriblefacebookmemes",
    "animemes",
    "fellowkids",
    "okbuddyretard",
    "deepfriedmemes",
    "shittyadviceanimals",
    "politicalcompassmemes",
    "funny",
    "im14andthisisdeep"
]