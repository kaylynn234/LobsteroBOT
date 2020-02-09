"""For when things go wrong."""

from discord.ext import commands


class BlueprintFailure(commands.CheckFailure):
    """Raised when a check on a blueprint fails. Yes I know it's ugly."""

    def __init__(self, bot, s, f):
        why = [
            "The administrators of this server have changed what is required to use it.\n"]
        for check in s:
            if check["criteria_type"] == "has_any_role":
                if check["criteria_requires"]:
                    why.append("✅ **|** You have at least one role.")
                else:
                    why.append("✅ **|** You have no roles.")

            elif check["criteria_type"] == "has_role":
                r = bot.get_role(int(check["criteria_value"]))
                if check["criteria_requires"]:
                    why.append(f"✅ **|** You have the required role ``{r.name}``.")
                else:
                    why.append(f"✅ **|** You do not have the forbidden role ``{r.name}``.")

            elif check["criteria_type"] == "has_permissions":
                formatted = check["criteria_value"].replace("-", " ")
                if check["criteria_requires"]:
                    why.append(f"✅ **|** You have the {formatted} permission in this channel.")
                else:
                    why.append((
                        f"✅ **|** You do not have the forbidden {formatted} "
                        "permission in this channel."))

            elif check["criteria_type"] == "has_strict_permissions":
                formatted = check["criteria_value"].replace("-", " ")
                if check["criteria_requires"]:
                    why.append(f"✅ **|** You have the {formatted} permission in this server.")
                else:
                    why.append((
                        f"✅ **|** You do not have the forbidden {formatted} "
                        "permission in this server."))

            elif check["criteria_type"] == "is_specific_user":
                if check["criteria_requires"]:
                    why.append(f"✅ **|** You are the required user.")
                else:
                    why.append(f"✅ **|** You are not a blocked user.")

            elif check["criteria_type"] == "is_guild_owner":
                if check["criteria_requires"]:
                    why.append(f"✅ **|** You are the server owner.")
                else:
                    why.append(f"✅ **|** You are not the server owner.")

        for check in f:
            if check["criteria_type"] == "has_any_role":
                if not check["criteria_requires"]:
                    why.append("🚫 **|** You have at least one role.")
                else:
                    why.append("🚫 **|** You have no roles.")

            elif check["criteria_type"] == "has_role":
                r = bot.get_role(int(check["criteria_value"]))
                if not check["criteria_requires"]:
                    why.append(f"🚫 **|** You have the blocked role ``{r.name}``.")
                else:
                    why.append(f"🚫 **|** You do not have the required role ``{r.name}``.")

            elif check["criteria_type"] == "has_permissions":
                formatted = check["criteria_value"].replace("-", " ")
                if not check["criteria_requires"]:
                    why.append(
                        f"🚫 **|** You have the forbidden {formatted} permission in this channel.")
                else:
                    why.append((
                        f"🚫 **|** You do not have the required {formatted} "
                        "permission in this channel."))

            elif check["criteria_type"] == "has_strict_permissions":
                formatted = check["criteria_value"].replace("-", " ")
                if not check["criteria_requires"]:
                    why.append(
                        f"🚫 **|** You have the forbidden {formatted} permission in this server.")
                else:
                    why.append((
                        f"🚫 **|** You do not have the required {formatted} "
                        "permission in this server."))

            elif check["criteria_type"] == "is_specific_user":
                if not check["criteria_requires"]:
                    why.append(f"🚫 **|** You are not the required user.")
                else:
                    why.append(f"🚫 **|** You are a blocked user.")

            elif check["criteria_type"] == "is_guild_owner":
                if not check["criteria_requires"]:
                    why.append(f"🚫 **|** You are not the server owner.")
                else:
                    why.append(f"🚫 **|** You are the server owner.")

        self.description = "\n".join(why)
