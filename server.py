import os.path

from aiohttp import web
import aiofiles

import asyncio
import datetime


INTERVAL_SECS = 1
BYTES = 102400


async def uptime_handler(request):
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/html'
    await response.prepare(request)

    while True:
        formatted_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f'{formatted_date}<br>'
        await response.write(message.encode('utf-8'))

        await asyncio.sleep(INTERVAL_SECS)


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
    while not process.stdout.at_eof():
        archive_data = await process.stdout.read(BYTES)
        await response.write(archive_data)

    await response.write_eof()
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
