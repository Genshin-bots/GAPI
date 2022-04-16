from typing import Union
from pathlib import Path
from time import time

from config import Config
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from fastapi import APIRouter, HTTPException, logger
from apscheduler.schedulers.background import BackgroundScheduler

conf = Config()
router = APIRouter(prefix='/image')
tmpdir = Path(__file__).parent / 'tmp'
storage_dir = Path(__file__).parent / 'saved'

if not tmpdir.exists():
    tmpdir.mkdir()
if not storage_dir.exists():
    storage_dir.mkdir()


def cleanup_(expired_time: int = conf.tmp.expired_time):
    for fp in tmpdir.iterdir():
        if int(time()) - fp.stat().st_ctime >= expired_time * 60:
            fp.unlink()


@router.get('/tmp/{filename}')
async def provider(filename: str, cleanup: bool = False):
    fp_ = tmpdir / filename
    if not fp_.exists():
        return HTTPException(404, 'File does not exist.')
    if cleanup and conf.tmp.allow_cleanup:
        return FileResponse(fp_, background=BackgroundTask(cleanup_, fp=fp_))
    return FileResponse(fp_)


@router.on_event('startup')
def init_auto_cleanup():
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_, 'interval', minutes=5)
    scheduler.start()
    logger.logger.info(
        f'Temporary folder detection has been started: files that exist for more than {conf.tmp.expired_time} '
        f'minutes will be deleted every {conf.tmp.interval} minute.'
    )
