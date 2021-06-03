from logging import error
import os
from typing import Dict, List
import sys
sys.path.append('./src/proto')

from proto.proto.page_scraper_pb2 import TextRequest, TextResponse
from proto.proto.page_scraper_pb2_grpc import PageScraperStub
from delphai_utils.grpc_client import get_grpc_client
import pandas as pd
import asyncio
from delphai_utils.logging import logging
from asyncio import Semaphore
from tqdm import tqdm
from grpc.aio import AioRpcError
import json

page_scraper = get_grpc_client(PageScraperStub, 'page-scraper.grpc.delphai.xyz:80')
semaphore = Semaphore(200)
data_dir = os.path.abspath('./.data')

async def scrape_link(link: str, scraped_path: str, progress_bar: tqdm, errors:Dict[str, str]):
  async with semaphore:
    try:
      text_response = await page_scraper.get_text(TextRequest(url=link, plain=True))
      response = text_response
    except AioRpcError as ex:
      logging.debug(f'[{link}] [{ex.code()}] {ex.details()}')
      errors[link] = f'[{ex.code()}] {ex.details().replace(f"[{link}] ", "")}'
      response = TextResponse(text=f'[{ex.code()}] {ex.details()}', original_url=link, resolved_url=link)
    except Exception as ex:
      logging.debug(f'[{link}] {repr(ex)}')
      errors[link] = repr(ex)
      response = TextResponse(text=repr(ex), original_url=link, resolved_url=link)
    finally:
      try:
        cleaned_link = link.replace('http://', '').replace('https://', '').split('#')[0].split('?')[0].replace('.html', '').rstrip('/')
        cleaned_link = f'{cleaned_link}.txt'
        file_path = os.path.dirname(cleaned_link)
        file_dir = os.path.abspath(f'{scraped_path}/{file_path}')
        if not os.path.exists(file_dir):
          os.makedirs(file_dir)
        with open(f'{scraped_path}/{cleaned_link}', 'w') as file:
          file.write(response.text)
          file.close()
      except Exception as ex:
        errors[link] = repr(ex)
      progress_bar.update(1)

async def main():
  with open('./.data/google_news_for_training.csv', 'rb') as input_file:
    df = pd.read_csv(input_file)
  link_list: List[str] = df.link.to_list()
  logging.info(f'found {len(link_list)} links')
  progress_bar = tqdm(total=len(link_list))
  errors: Dict[str, str] = {}
  tasks = []
  scraped_path = os.path.abspath(f'{data_dir}/scraped')
  if not os.path.exists(scraped_path):
    os.makedirs(scraped_path)
  for link in link_list:
    task = scrape_link(link, scraped_path, progress_bar, errors)
    tasks.append(task)
  await asyncio.gather(*tasks)
  error_path = f'{data_dir}/errors.json'
  if os.path.exists(error_path):
    os.remove(error_path)
  if len(errors.keys()) > 0:
    with open(error_path, 'w') as error_file:
      json.dump(errors, error_file, indent=2)



if __name__ == '__main__':
  asyncio.get_event_loop().run_until_complete(main())