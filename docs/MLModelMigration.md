# ML Model Migration

> [!IMPORTANT]
>
> Fixing issue [#9](https://github.com/arv-anshul/yt-watch-history/issues/9) of [arv-anshul/yt-watch-history](https://github.com/arv-anshul/yt-watch-history) repository.

## Plan of Attack

### For ContentType Prediction Model

1. **Fetch Data From Database for Model Training**
   - Fetch video details data from database and store it into local then train on it with different params.
   - Fetch ContentTypeTaggedChannel data from database to create the training data.
