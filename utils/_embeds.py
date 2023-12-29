import discord
import constants

from utils._formatting import (
    iso_to_discord_timestamp,
    get_file_emoji,
    _get_assignees,
    _get_comments,
    _get_description,
    _get_color,
)


def construct_repo_files_embed(repo: str, files: list) -> discord.Embed:
    embed = discord.Embed(
        title=f"`{repo}`",
        color=constants.COLORS["green"],
        url=f"https://github.com/{repo}",
    )

    description_lines = []
    for item in files:
        if item["type"] == "dir":
            icon = constants.FILE_EMOJIS["dir"]
        else:
            icon = get_file_emoji(item["name"])
        description_lines.append(f"{icon} [`{item['name']}`]({item['html_url']})")
    embed.description = "\n".join(description_lines)

    return embed


def construct_loc_embed(repo: str, data: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"Lines of Code in `{repo}`",
        color=constants.COLORS["green"],
        url=f"https://github.com/{repo}",
    )

    total_lines = sum(item["lines"] for item in data)
    total_files = sum(item["files"] for item in data)
    code_breakdown = "\n".join(
        f"{language}: {linesOfCode}"
        for language, linesOfCode in (
            (item["language"], item["linesOfCode"]) for item in data
        )
        if language != "Total"
    )

    embed.description = (
        f"A total of **{total_lines}** lines of code in **{total_files}** files."
    )
    embed.add_field(
        name="Language Breakdown:",
        value=f"```{code_breakdown}```",
        inline=False,
    )

    return embed


def construct_commits_embed(
    repo: str,
    commits: list,
) -> discord.Embed:
    description = []

    for commit in commits:
        sha = commit["sha"][:7]
        message = commit["commit"]["message"].split("\n")[0]

        if len(message) > 50:
            message = f"{message[:50]}..."
        description.append(
            f"{constants.EMOJIS['check']} [`{sha}`]({commit['html_url']}) {message.replace('`', '')}"
        )

    return discord.Embed(
        title=f"{constants.EMOJIS['github']} Latest commits in `{repo}`",
        description="\n".join(description),
        color=constants.COLORS["green"],
        url=f"https://github.com/{repo}",
    )


def construct_issue_embed(
    issue: dict,
) -> discord.Embed:
    embed = discord.Embed(
        title=f"{issue['title']}",
        url=issue["html_url"],
        color=constants.COLORS["green"],
    )

    body_text = f"{issue['body'][:400]}{'...' if len(issue['body']) > 400 else ''}"
    assignee_text = (
        ", ".join(
            f"[{assignee['login']}]({assignee['html_url']})"
            for assignee in issue["assignees"]
        )
        or "No assignees"
    )

    embed.description = (
        f"{body_text}\n\nThis issue has a total of 💬 **{issue['comments']}** comments."
    )
    embed.add_field(
        name="Author",
        value=f"[{issue['user']['login']}]({issue['user']['html_url']})",
    )
    embed.add_field(name="Assignees", value=assignee_text)
    embed.add_field(
        name="Created",
        value=f"{iso_to_discord_timestamp(issue['created_at'])}",
    )

    for field_name, key in [("Closed", "closed_at")]:
        if date := issue.get(key):
            embed.add_field(name=field_name, value=f"{iso_to_discord_timestamp(date)}")

    embed.set_author(
        name=issue["repository_url"].split("/")[-1],
        url=issue["repository_url"],
        icon_url=issue["user"]["avatar_url"],
    )

    return embed


def construct_pr_embed(pr, show_comments, comments=None) -> discord.Embed:
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


def construct_repo_embed(repo: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"📁 {repo['name']}",
        url=repo["html_url"],
        color=constants.COLORS["green"],
    )

    embed.description = f"{repo['description']}\n\nThis repository has a total of 🌟 **{repo['stargazers_count']}** stars, 🍴 **{repo['forks_count']}** forks, and 📂 **{repo['size']}** KB."
    embed.add_field(
        name="Owner",
        value=f"[{repo['owner']['login']}]({repo['owner']['html_url']})",
    )
    embed.add_field(
        name="Created",
        value=f"{iso_to_discord_timestamp(repo['created_at'])}",
    )
    embed.add_field(
        name="Updated",
        value=f"{iso_to_discord_timestamp(repo['updated_at'])}",
    )

    return embed


def construct_profile_embed(profile: dict, repos: list) -> discord.Embed:
    embed = discord.Embed(
        title=f"👤 {profile['login']}",
        url=profile["html_url"],
        color=constants.COLORS["green"],
    )

    bio = profile["bio"] or "No bio."

    if repos:
        bio += f"\n\n**Repositories**:"
        for repo in repos[:5]:
            bio += f"\n{constants.EMOJIS['repo']} [`{repo['full_name']}`]({repo['html_url']})"

    embed.description = f"{bio}\n\nThis user has a total of 🌟 **{profile['public_repos']}** public repositories, 🍴 **{profile['public_gists']}** public gists, and 💬 **{profile['followers']}** followers."
    embed.add_field(
        name="Created",
        value=f"{iso_to_discord_timestamp(profile['created_at'])}",
    )

    if profile["avatar_url"]:
        embed.set_thumbnail(url=profile["avatar_url"])

    return embed


def invalid_language(language: str, closest_languages: list[str]) -> discord.Embed:
    embed = discord.Embed(title="Invalid Language", color=constants.COLORS["red"])

    if not closest_languages:
        embed.description = f"```{language} is not a valid language.```"
        return embed

    matches = "\n".join(f"{i+1}. {lang}" for i, lang in enumerate(closest_languages))

    embed.add_field(name="Did you mean one of these? 🤔", value=f"```{matches}```")

    return embed


def create_eval_embed(
    lang,
    message: discord.Message,
    code_output: str,
    metrics: dict,
) -> discord.Embed:
    emoji = constants.LANG_EMOJIS.get(lang, "")
    embed = discord.Embed(
        title=f"`Result - {message.id}`",
        description=f"{emoji} Exited with code **{metrics['exit_code']}**",
        color=constants.COLORS["green"],
        url=message.jump_url,
    )

    embed.description += f"```{code_output.split('Real time:')[0].rstrip()}```"

    for key, value in metrics.items():
        if key != "exit_code":
            embed.add_field(name=key.replace("_", " ").title(), value=value)

    return embed
