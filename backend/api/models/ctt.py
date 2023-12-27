from enum import Enum

from pydantic import BaseModel, field_validator


class ContentTypeEnum(Enum):
    Education = "Education"
    Entertainment = "Entertainment"
    MoviesAndReviews = "Movies & Reviews"
    Music = "Music"
    News = "News"
    Programming = "Programming"
    PseudoEducation = "Pseudo Education"
    Reaction = "Reaction"
    Shorts = "Shorts"
    Tech = "Tech"
    Vlogs = "Vlogs"


class CttChannelData(BaseModel):
    channelId: str
    channelTitle: str
    contentType: ContentTypeEnum

    @field_validator("contentType")
    @classmethod
    def validate_contentType(cls, v: ContentTypeEnum) -> str:
        return v.value
