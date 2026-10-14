"""Run separately from Uvicorn: python -m scripts.sync_policies --interval 3600"""
import argparse
import asyncio
import json
from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.services.policy_sync_service import sync_source


async def main(args):
    init_db()
    while True:
        results = []
        for source, region in [('central', None)] + [('local', region) for region in args.regions]:
            with SessionLocal() as db:
                results.append(await sync_source(db, source, region))
        print(json.dumps(results, ensure_ascii=False), flush=True)
        if not args.interval:
            return
        await asyncio.sleep(args.interval)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--regions', nargs='+', default=['서울특별시'])
    parser.add_argument('--interval', type=int, default=0)
    args = parser.parse_args()
    if args.interval < 0:
        parser.error('--interval must be nonnegative')
    asyncio.run(main(args))
