import os
import logging
import asyncio
import datetime

import aiofiles
from aiohttp import web


logging.basicConfig(
    format=u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
    level=logging.INFO)

INTERVAL_SECS = 1
BYTES = 512000


async def archive(request):
    archive_hash = request.match_info.get('archive_hash')
    if not os.path.exists(os.path.join('test_photos', archive_hash)):
        raise web.HTTPNotFound(text=f'404 Архив {archive_hash} не существует или был удален')
    response = web.StreamResponse(
        headers={
            'Content-Disposition': f'attachment; filename="{archive_hash}.zip"',
            'Content-Type': 'application/zip'
        }
    )
    await response.prepare(request)

    args = ['zip', '-r', '-', archive_hash]
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd='test_photos')
    try:
        while not process.stdout.at_eof():
            archive_data = await process.stdout.read(BYTES)
            logging.info(f'Sending {archive_hash} archive chunk')
            await response.write(archive_data)
        await response.write_eof()
    finally:
        process.kill()
        await process.communicate()
        logging.error('Download was interrupted')
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
