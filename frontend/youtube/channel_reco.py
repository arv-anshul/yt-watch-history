import httpx
import polars as pl

from configs import API_HOST_URL


def check_if_subscribed_column_exists(ingested_data: pl.DataFrame) -> None:
    """Check if "subscribed" column exists in data."""
    if "subscribed" not in ingested_data.columns:
        raise ValueError("Ingested data does not contain 'subscribed' column.")


def add_subscribed_column(
    ingested_data: pl.DataFrame,
    subscribed_channels: pl.DataFrame,
) -> pl.DataFrame:
    """Add `"subscribed"` column to ingested data."""
    return ingested_data.with_columns(
        pl.col("channelId").is_in(subscribed_channels["Channel Id"]).alias("subscribed")
    )


class RecommendChannels:
    """Class for making recommendations for a channel."""

    def __init__(
        self, ingested_data: pl.DataFrame, video_details_data: pl.DataFrame
    ) -> None:
        check_if_subscribed_column_exists(ingested_data)
        self.data = video_details_data.join(
            ingested_data.filter(pl.col("subscribed").eq(True)),
            left_on="id",
            right_on="videoId",
        ).select("title", "tags", "channelId", "channelTitle")

    def get_recommendations(self, channel_title: str) -> pl.DataFrame:
        """Get recommendations for a channel."""
        query_channel = self.data.filter(pl.col("channelTitle").eq(channel_title))
        res = httpx.post(
            f"{API_HOST_URL}/ml/channel_reco/predict?channels=true",
            json=query_channel.to_dicts(),
        )
        if res.status_code == 200:
            return pl.DataFrame._from_dicts(res.json())
        raise httpx.HTTPStatusError(
            f"Error while making request: {res.text}",
            request=res.request,
            response=res,
        )
