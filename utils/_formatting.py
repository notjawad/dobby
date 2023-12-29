import constants

from datetime import datetime, timezone


def iso_to_discord_timestamp(date_input) -> str:
    # Determine if the input is an ISO string or a Unix timestamp
    if isinstance(date_input, str):  # If it's a string, handle it as an ISO date
        try:
            date_obj = datetime.fromisoformat(date_input.rstrip("Z")).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return "Invalid ISO date format."
    elif isinstance(date_input, int):  # If it's an int, handle it as a Unix timestamp
        date_obj = datetime.fromtimestamp(date_input, tz=timezone.utc)
    else:
        return "Invalid date input."

    timestamp = int(date_obj.timestamp())
    return f"<t:{timestamp}:R>"


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
    body = pr["body"] or "No description provided."
    description = f"{body[:400]}{'...' if len(body) > 400 else ''}"
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
