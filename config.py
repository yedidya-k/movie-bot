from dotenv import dotenv_values


class Config:
    def __init__(self, env_path: str = ".env"):
        env = dotenv_values(env_path)

        self.download_path = env.get("DOWNLOAD_PATH", "./downloads/")

        raw_groups = env.get("GROUP_IDS", "")
        self.group_ids = [int(x.strip()) for x in raw_groups.split(",") if x.strip()]

        raw_bridge = env.get("BRIDGE_GROUP_ID", "")
        self.bridge_group_id = int(raw_bridge) if raw_bridge.strip() else None

        raw_bots = env.get("BRIDGE_BOTS", "")
        self.bridge_bots = [x.strip() for x in raw_bots.split(",") if x.strip()]

        self.api_id = int(env.get("API_ID", "0")) if env.get("API_ID") else None
        self.api_hash = env.get("API_HASH", "")
        self.phone_number = env.get("PHONE_NUMBER", "")
