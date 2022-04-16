from pathlib import Path

import toml
from pydantic import BaseModel


class Temporary(BaseModel):
    interval: int
    expired_time: int
    allow_cleanup: bool


class Config(BaseModel):
    tmp: Temporary

    def __init__(self, conf_fp: str = Path(__file__).parent / 'config.toml'):
        conf_ = toml.load(conf_fp)
        super().__init__(**conf_)
