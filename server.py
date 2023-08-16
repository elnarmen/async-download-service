import os
import logging
import asyncio
import argparse
from pathlib import Path
from functools import partial

import aiofiles
from aiohttp import web


logger = logging.getLogger(__file__)

BYTES = 512000


async def archive(request, sleep_duration, photos_dir):
    archive_hash = request.match_info.get('archive_hash')
    if not os.path.exists(os.path.join(photos_dir, archive_hash)):
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
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=photos_dir)
    try:
        while not process.stdout.at_eof():
            archive_data = await process.stdout.read(BYTES)
            logger.info(f'Sending {archive_hash} archive chunk')
            if sleep_duration:
                await asyncio.sleep(sleep_duration)
            await response.write(archive_data)

        await response.write_eof()
        logger.info(f'{archive_hash} archive was successfully downloaded')
        await process.wait()  # ждать пока zip завершит процесс
    finally:
        if process.returncode is None:
            process.kill()
            await process.communicate()
            logger.error('Download was interrupted')
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--logs', action='store_true', help='Включить логирование')
    parser.add_argument(
        '-s',
        '--sleep',
        type=int,
        default=0,
        help='Длительность задержки ответа (сек)',
    )
    parser.add_argument(
        '-p', '--path', type=Path, default='test_photos', help='Путь к директории с фото')
    args = parser.parse_args()

    logging.basicConfig(level=logging.ERROR)
    if args.logs:
        logger.setLevel(logging.INFO)

    archive_handler = partial(archive, sleep_duration=args.sleep, photos_dir=args.path)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive_handler),
    ])
    web.run_app(app)


if __name__ == '__main__':
    main()
