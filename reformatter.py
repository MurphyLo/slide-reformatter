import json
import os
import re
import sys
import time
import requests
from urllib.parse import unquote
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# 设置日志
log_file = os.path.expanduser('~/slide_reformatter.log')
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

proxies = {"https": "http://127.0.0.1:7897"}

def log_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"{func.__name__} 执行时间: {end_time - start_time:.2f} 秒")
        return result
    return wrapper

@log_time
def set_cookie():
    url = 'https://online2pdf.com/multiple-pages-per-sheet'
    resp = requests.get(url, proxies=proxies)
    keys = ['C', 'SESSID', 'SETTINGS_ID', 'U', 'A']  # 240912
    return {key: resp.cookies.get(key) for key in keys}


@log_time
def check(cookie_init):
    url = 'https://online2pdf.com/check'
    params = {
        'v': '3',  # 240912
        'ab': '11',
        'ra': None,  # 240912
    }
    cookies = {'language': 'en',}
    cookies.update(cookie_init)
    resp = requests.post(url, data=params, cookies=cookies, proxies=proxies)
    server_cred_raw = re.sub(r'(\w+):', r'"\1":', resp.text).replace("'", "\"")
    return json.loads(server_cred_raw)


@log_time
def conversion_ajax(server_cred, cookie_init, settings, upload_pdf, export_name):
    with open(os.path.dirname(__file__) + '/request_body.json', 'r') as f:
        payload = json.load(f)
    payload.update(settings)
    payload.update({
        'cid': _encode_cid(server_cred['cid']),
        'sid': cookie_init['SESSID'],
        'SETTINGS_ID': cookie_init['SETTINGS_ID'],
        'v': 3  # 240912
    })
    url = 'https://{}.online2pdf.com/conversion/ajax'.format(server_cred['server'])
    cookies = cookie_init.copy()
    cookies['language'] = 'en'
    with open(upload_pdf, 'rb') as f:

        # export_name = f.name if not export_name else export_name
        # export_name = export_name.split('/')[-1] if '/' in export_name else export_name
        # 24.12.13 修改：进一步兼容 windows 平台，修复产生长文件名的问题 converted_C__Users_luozh_Documents_UniAD.pdf
        export_name = os.path.basename(f.name) if not export_name else os.path.basename(export_name)
        export_name = export_name.split('/')[-1] if '/' in export_name else export_name

        payload.update({'output_name': export_name.split('.')[0]})  # 240912
        files = {'userfile[0][0]': (export_name, f, 'application/pdf')}  # 240912
        resp = requests.post(url=url, data=payload, cookies=cookies, files=files, proxies=proxies)
    resp_raw = re.sub(r'(\w+):', r'"\1":', resp.text).replace("'", "\"")
    return resp.cookies.get('SETTINGS_ID'), json.loads(resp_raw)['id']


def _encode_cid(cid):
    cid = cid.upper()
    cid2 = ''
    for i in range(len(cid)-1, -1, -1):
        cid2 += str(ord(cid[i]))
    cid2 = cid2[3:] + cid2[:3]
    return cid2


@log_time
def progress(cookie_init, ajax_id, server_cred):
    url = 'https://{}.online2pdf.com/progress'.format(server_cred['server'])
    payload = {
        'sid': cookie_init['SESSID'],
        'uid': ajax_id,
        'v': 3
    }
    cookies = cookie_init.copy()
    cookies['language'] = 'en'
    resp = requests.post(url, data=payload, cookies=cookies, proxies=proxies)
    resp_raw = re.sub(r'(\w+):', r'"\1":', resp.text).replace("'", "\"")
    return json.loads(resp_raw)


@log_time
def download_pdf(url, path, output_file=None):
    try:
        start_time = time.time()
        logging.info(f"开始下载PDF: https:{url}")
        
        response = requests.get(f'https:{url}', stream=True, proxies=proxies)
        response.raise_for_status()
        
        if response.headers['Content-Type'] == 'application/x-download':
            filename = output_file if output_file else 'converted_' + unquote(url.split('/')[-1])
            full_path = os.path.join(path, filename)
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded_size = 0
            
            with open(full_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    size = f.write(data)
                    downloaded_size += size
                    
                    if total_size > 0:
                        percent = (downloaded_size / total_size) * 100
                        elapsed_time = time.time() - start_time
                        speed = downloaded_size / (1024 * elapsed_time)
                        logging.info(f"下载进度: {percent:.2f}%, 速度: {speed:.2f} KB/s")
            
            end_time = time.time()
            total_time = end_time - start_time
            average_speed = (total_size / (1024 * 1024)) / total_time
            
            logging.info(f"PDF文件下载完成。总大小: {total_size/1024/1024:.2f} MB, 总时间: {total_time:.2f} 秒, 平均速度: {average_speed:.2f} MB/s")
            print(f"PDF file has been successfully downloaded.")
        else:
            print("The requested URL may not be a PDF file or is not accessible.")
            soup = BeautifulSoup(response.content, 'lxml')
            print(soup.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
    except IOError as e:
        print(f"An error occurred during file operations: {e}")


if __name__ == '__main__':
    start_time = time.time()
    logging.info("程序开始执行")

    # for more configuration options, please refer to `request_body.json`.
    settings = {
        'layout_border': 0,                             # PDF page layout: Without border
        'layout_mode_multiple_pages_per_sheet': 3,      # PDF page layout: Pages per sheet
        'layout_mode': 3,                               #             new: Pages per sheet MUST BE SAME AS `layout_mode_multiple_pages_per_sheet`
        'layout_page_orientation': 'portrait',          # Page layout: Orientation of the PDF page
        'layout_inner_margin': 0,                       # Inner margin: The space between the pages
        'layout_outer_margin': 0                        # Outer margin: The space between content and page margin
    }

    if len(sys.argv) < 2:
        print('Please provide the input PDF file as the first parameter.')
        sys.exit()
    input_file = sys.argv[1]
    if not input_file.endswith('.pdf'):
        print('The input file must be a PDF file with a .pdf extension.')
        sys.exit()
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    cookie_init = set_cookie()
    server_cred = check(cookie_init)
    logging.info('开始上传PDF')
    time.sleep(3)
    cookie_init['SETTINGS_ID'], ajax_id = conversion_ajax(server_cred, cookie_init, settings, input_file, output_file)
    logging.info('PDF已上传，正在处理')
    time.sleep(2)

    progress_start_time = time.time()
    while True:
        data = progress(cookie_init, ajax_id, server_cred)
        if data and data['action'] == 'message':  # 条件判断：使用短路策略
            pdf_url = data['url']
            break
        logging.info('PDF导出尚未就绪')
        time.sleep(2)
    logging.info(f"等待PDF导出完成时间: {time.time() - progress_start_time:.2f} 秒")

    output_dir = os.path.dirname(sys.argv[1]) or '.'
    download_pdf(pdf_url, output_dir, output_file)

    end_time = time.time()
    logging.info(f"程序总执行时间: {end_time - start_time:.2f} 秒")
    logging.info("程序执行完毕")
