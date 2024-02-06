# app.py
from titiler.core.factory import TilerFactory
from titiler.extensions import cogViewerExtension, cogValidateExtension
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from .dependencies import ColorMapParams

app = FastAPI(root_path="/tiler")
cog = TilerFactory(
    colormap_dependency=ColorMapParams,
    extensions=[
        cogViewerExtension(),
        cogValidateExtension(),
    ])
app.include_router(cog.router)
add_exception_handlers(app, DEFAULT_STATUS_CODES)
