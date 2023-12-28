# Migrate Frontend

### Make prediction with CttModel

- Use `/ml/ctt/` to make prediction using video **title and videoId**.
- Make sure that the CttModel must present at the specified path `ml_models/ctt_model.dill`.

### Migration requirements of Frontend

- Remove unnecessary files or codes like `models/`, `frontend/youtube/content_type_tagging.py`, constants from `frontend/constants.py`, `frontend/_io.py` etc.
- Make prediction using API in [Basic Analysis Page](../pages/🐻‍❄️_YT_History_Basic.py)
