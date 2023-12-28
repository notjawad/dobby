import discord
import constants

from datetime import datetime, timezone


def iso_to_discord_timestamp(iso_date: str) -> str:
    try:
        date_obj = datetime.fromisoformat(iso_date.rstrip("Z")).replace(
            tzinfo=timezone.utc
        )
        timestamp = int(date_obj.timestamp())
        return f"<t:{timestamp}:R>"
    except ValueError:
        return "Invalid ISO date format."


def get_file_emoji(file_name: str) -> str:
    return next(
        (
            emoji
            for extension, emoji in constants.FILE_EMOJIS.items()
            if file_name.endswith(extension) or file_name == extension
        ),
        constants.FILE_EMOJIS["file"],
    )


def _get_color(pr):
    return (
        constants.COLORS["green"] if pr["state"] == "open" else constants.COLORS["red"]
    )


def _get_description(pr: dict) -> str:
    description = f"{pr['body'][:400]}{'...' if len(pr['body']) > 400 else ''}"
    stats = f"💬 **{pr['comments']} comments**, 📝 **{pr['commits']} commits**, 🟢 **{pr['additions']} additions**, 🔴 **{pr['deletions']} deletions**, 📄 **{pr['changed_files']} changed files**"
    return f"{description}\n\n{stats}"


def _get_assignees(pr: dict) -> str:
    assignees = ", ".join(f"[{a['login']}]({a['html_url']})" for a in pr["assignees"])
    return assignees or "No assignees"


def _get_comments(comments: list) -> str:
    return "\n".join(
        f"[`{c['user']['login']}`]({c['user']['html_url']}) - {c['body'][:200]}{'...' if len(c['body']) > 200 else ''}"
        for c in comments
    )


def build_pr_embed(pr, show_comments, comments=None):
    embed = discord.Embed(
        title=f"{constants.EMOJIS['pr']} {pr['title']}",
        url=pr["html_url"],
        color=_get_color(pr),
    )

    embed.set_author(
        name=pr["head"]["repo"]["full_name"],
        url=pr["head"]["repo"]["html_url"],
        icon_url=pr["head"]["repo"]["owner"]["avatar_url"],
    )

    embed.description = _get_description(pr)

    embed.add_field(
        name="Author", value=f"[`{pr['user']['login']}`]({pr['user']['html_url']})"
    )

    embed.add_field(name="Assignees", value=_get_assignees(pr))

    embed.add_field(name="Created", value=iso_to_discord_timestamp(pr["created_at"]))

    for name, key in [
        ("Merged", "merged_at"),
        ("Closed", "closed_at"),
        ("Updated", "updated_at"),
    ]:
        if date := pr.get(key):
            embed.add_field(name=name, value=iso_to_discord_timestamp(date))

    if show_comments:
        embed.add_field(name="Comments", value=_get_comments(comments), inline=False)

    return embed
