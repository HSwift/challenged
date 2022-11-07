import httpx


async def verify_token(token) -> tuple[bool, str]:
    async with httpx.AsyncClient() as client:
        # TODO: write your own code here
        return True, "username"
