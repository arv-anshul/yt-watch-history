import os

import dotenv

dotenv.load_dotenv()  # Load environment variables from `.env` file.

YT_API_KEY = os.environ.get("YT_API_KEY")
