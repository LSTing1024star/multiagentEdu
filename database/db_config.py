import os
from dataclasses import dataclass

@dataclass
class DBConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", 3306))
    user: str = os.getenv("DB_USER", "root")
    password: str = os.getenv("DB_PASSWORD", "123456")
    db_name: str = os.getenv("DB_NAME", "edu_agent")
    charset: str = "utf8mb4"

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "edu_agent.db")
