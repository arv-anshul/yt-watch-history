from datetime import datetime
from typing import Optional, Self

from pydantic import BaseModel


class YtVideoDetails(BaseModel):
    categoryId: Optional[str]
    channelId: Optional[str]
    channelTitle: Optional[str]
    description: Optional[str]
    duration: Optional[str]
    id: str
    publishedAt: Optional[datetime]
    tags: Optional[list[str]]
    title: Optional[str]

    @classmethod
    def null(cls, id: Optional[str] = None) -> Self:
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
