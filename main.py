"""
MIT License

Copyright (c) 2025 PAMHoYA Team (https://pamhoya.ac.uk)
Project: PAMHoYA - Platform for Advancing Mental Health in Youth and Adolescence
Lead Developer: Augustine Khumalo

This software extends and builds upon the Harmony framework 
(Copyright (c) 2023 Ulster University - https://harmonydata.ac.uk)
for item harmonisation functionality.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys

sys.path.append("./harmony/src")

import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from harmony_api.core.settings import settings
from harmony_api.routers.health_check_router import router as health_check_router
from harmony_api.routers.info_router import router as info_router
from harmony_api.routers.text_router import router as text_router
from harmony_api.routers.data_discovery_router import router as data_discovery_router
from harmony_api.routers.data_harmonisation_router import router as data_harmonisation_router
from harmony_api.routers.summarisation_router import router as summarisation_router
from harmony_api.routers.analytics_router import router as analytics_router
from harmony_api.routers.metadata_router import router as metadata_router
from harmony_api.services.instruments_cache import InstrumentsCache
from harmony_api.scheduler import scheduler
from harmony_api.services.vectors_cache import VectorsCache

description = """
PAMHoYA API - Platform for Advancing Mental Health in Youth and Adolescence

PAMHoYA is a comprehensive platform for mental health research discovery, harmonisation, 
and analytics across South African languages and beyond. 

The platform enables researchers, policymakers, and community stakeholders to:
- Discover mental health research datasets
- Harmonise questionnaires and data across instruments
- Generate plain-language summaries of research
- Access role-based analytics and insights

**Item Harmonisation**: Built on the Harmony framework (https://harmonydata.ac.uk)
**Multilingual Support**: 11 South African languages + 109 global languages via LaBSE
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.start()

    yield

app_fastapi = FastAPI(
    title=settings.APP_TITLE or "PAMHoYA API",
    description=description,
    version=settings.VERSION or "1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    contact={
        "name": "PAMHoYA Team",
        "url": "https://pamhoya.ac.uk",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/license/mit/",
    },
)

app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS["origins"],
    allow_credentials=settings.CORS["allow_credentials"],
    allow_methods=settings.CORS["allow_methods"],
    allow_headers=settings.CORS["allow_headers"],
)

# Add gzip middleware
app_fastapi.add_middleware(GZipMiddleware)

# Include routers
app_fastapi.include_router(health_check_router, tags=["Health Check"])
app_fastapi.include_router(text_router, tags=["Text"])
app_fastapi.include_router(info_router, tags=["Info"])
app_fastapi.include_router(data_discovery_router, tags=["Data Discovery"])
app_fastapi.include_router(metadata_router, tags=["Metadata Harmonization"])
app_fastapi.include_router(data_harmonisation_router, tags=["Data Harmonisation"])
app_fastapi.include_router(summarisation_router, tags=["Summarisation"])
app_fastapi.include_router(analytics_router, tags=["Analytics"])


async def main():
    # Load cache
    InstrumentsCache()
    VectorsCache()

    # Load metadata
    from harmony_api.services.metadata_harmonizer import get_harmonizer
    from harmony_api.services.metadata_loader import MetadataLoader

    harmonizer = get_harmonizer()
    loader = MetadataLoader(harmonizer)

    # Load SAPRIN metadata
    try:
        load_results = loader.load_saprin_metadata()
        print("INFO:\t  Metadata loaded successfully")
        print(f"INFO:\t  Loaded sources: {loader.get_loaded_sources()}")
    except Exception as e:
        print(f"WARNING:\t Error loading metadata: {str(e)}")

    server = uvicorn.Server(
        config=uvicorn.Config(
            app=app_fastapi,
            host=settings.SERVER_HOST,
            port=settings.PORT,
            reload=settings.RELOAD,
            workers=1,
            loop="asyncio",
        )
    )

    api = asyncio.create_task(server.serve())

    # Start FastAPI
    print("INFO:\t  Starting application...")
    await asyncio.wait([api])


if __name__ == "__main__":
    asyncio.run(main())
