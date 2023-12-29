import aiohttp


class StackOverflow:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def search(self, query: str, limit: 20) -> dict:
        async with self.session.get(
            "https://api.stackexchange.com/2.2/search/advanced",
            params={
                "order": "desc",
                "sort": "relevance",
                "site": "stackoverflow",
                "q": query,
                "pagesize": limit,
            },
        ) as resp:
            return await resp.json()

    async def get_question_answers(self, question_id: int) -> dict:
        async with self.session.get(
            f"https://api.stackexchange.com/2.2/questions/{question_id}/answers",
            params={
                "order": "desc",
                "sort": "votes",
                "site": "stackoverflow",
                "filter": "!9_bDE(fI5",
            },
        ) as resp:
            return await resp.json()

    async def get_question_body(self, question_id: int) -> dict:
        url = f"https://api.stackexchange.com/2.2/questions/{question_id}"
        params = {
            "order": "desc",
            "sort": "activity",
            "site": "stackoverflow",
            "filter": "!-MBrU_IzpJ5H-AG6Bbzy.X-BYQe(2v-.J",
        }
        async with self.session.get(url, params=params) as resp:
            data = await resp.json()
            if data["items"]:
                # Return the body of the first (and typically only) question
                return data["items"][0].get("body", "No body found.")
            else:
                return "No question found with the provided ID."
