import logging
import os

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

supabase = None

try:
    from supabase import create_client

    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
except Exception:
    logger.warning("Supabase not configured — running with mock data only.")
