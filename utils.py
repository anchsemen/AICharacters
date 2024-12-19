import re


async def crop_message(text: str) -> str:
    match = re.search(r"[.!?*](?!.*[.!?*])", text)
    if match:
        return text[:match.end()]
    return text
