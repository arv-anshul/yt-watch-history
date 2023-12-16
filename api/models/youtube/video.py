import asyncio
from datetime import datetime
from typing import Self

from pydantic import BaseModel


class YtVideoDetails(BaseModel):
    categoryId: str | None
    channelId: str | None
    channelTitle: str | None
    description: str | None
    duration: str | None
    id: str
    publishedAt: datetime | None
    tags: list[str] | None
    title: str | None

    @classmethod
    def null(cls, id: str | None = None) -> Self:
        return cls(
            categoryId=None,
            channelId=None,
            channelTitle=None,
            description=None,
            duration=None,
            id="N/A" if id is None else id,
            publishedAt=None,
            tags=[],
            title="N/A",
        )

    @classmethod
    async def from_dict(cls, item: dict, /) -> Self:
        try:
            return cls(
                categoryId=item["snippet"].get("categoryId"),
                channelId=item["snippet"].get("channelId"),
                channelTitle=item["snippet"].get("channelTitle"),
                description=item["snippet"].get("description"),
                duration=item["contentDetails"].get("duration"),
                id=item["id"],
                publishedAt=item["snippet"].get("publishedAt"),
                tags=item["snippet"].get("tags"),
                title=item["snippet"].get("title"),
            )
        except KeyError:
            return cls.null(item.get("id"))

    @classmethod
    async def from_dicts(cls, items: list[dict], /) -> list[Self]:
        return await asyncio.gather(*[cls.from_dict(i) for i in items])
