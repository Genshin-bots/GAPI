from fastapi import FastAPI
from Image import provider
from Artifact import scanner

igs = FastAPI(
    title="G3A",
    description="Genshin 3rd-party API"
)

igs.include_router(provider.router)
igs.include_router(scanner.router, prefix='/artifact')

if __name__ == '__main__':
    from uvicorn import run

