import json
import os

from .entrypoints import create_family_session

PROFILE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "tmp",
    "user_sessions",
    "fc864893-aee4-47d9-94e2-9941ad52bd35",
    "user_profile.json",
)

if os.path.exists(PROFILE_PATH):
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        profile_data = json.load(f)
else:
    profile_data = {}

root_agent = create_family_session({"profile": profile_data})
