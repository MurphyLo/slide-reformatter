import json
import re
import sys
import time
import requests
from urllib.parse import unquote
from pprint import pprint

def set_cookie():
    url = 'https://online2pdf.com/multiple-pages-per-sheet'
    resp = requests.get(url)
    keys = ['C', 'SESSID', 'SETTINGS_ID', 'U', 'A']  # 240912
    return {key: resp.cookies.get(key) for key in keys}


def check(cookie_init):
    url = 'https://online2pdf.com/check'
    params = {
        'v': '3',  # 240912
        'ab': '11',
        'ra': None,  # 240912
    }
    cookies = {'language': 'en',}
    cookies.update(cookie_init)
    resp = requests.post(url, data=params, cookies=cookies)
    server_cred_raw = re.sub(r'(\w+):', r'"\1":', resp.text).replace("'", "\"")
    return json.loads(server_cred_raw)


def conversion_ajax(server_cred, cookie_init, settings, upload_pdf, export_name):
    with open('request_body.json', 'r') as f:
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
        export_name = f.name if not export_name else export_name
        export_name = export_name.split('/')[-1] if '/' in export_name else export_name
        payload.update({'output_name': export_name.split('.')[0]})  # 240912
        files = {'userfile[0][0]': (export_name, f, 'application/pdf')}  # 240912
        resp = requests.post(url=url, data=payload, cookies=cookies, files=files)
    resp_raw = re.sub(r'(\w+):', r'"\1":', resp.text).replace("'", "\"")
    return resp.cookies.get('SETTINGS_ID'), json.loads(resp_raw)['id']


def _encode_cid(cid):
    cid = cid.upper()
    cid2 = ''
    for i in range(len(cid)-1, -1, -1):
        cid2 += str(ord(cid[i]))
    cid2 = cid2[3:] + cid2[:3]
    return cid2


def progress(cookie_init, ajax_id, server_cred):
    url = 'https://{}.online2pdf.com/progress'.format(server_cred['server'])
    payload = {
        'sid': cookie_init['SESSID'],
        'uid': ajax_id,
        'v': 3
    }
    cookies = cookie_init.copy()
    cookies['language'] = 'en'
    resp = requests.post(url, data=payload, cookies=cookies)
    resp_raw = re.sub(r'(\w+):', r'"\1":', resp.text).replace("'", "\"")
    return json.loads(resp_raw)


def download_pdf(url):
    try:
        response = requests.get(url)
        if response.status_code == 200 and response.headers['Content-Type'] == 'application/x-download':
            with open(unquote(url.split('/')[-1]), 'wb') as f:
                f.write(response.content)
            print(f"PDF file has been successfully downloaded.")
        else:
            print("The requested URL may not be a PDF file or is not accessible.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
    except IOError as e:
        print(f"An error occurred during file operations: {e}")


if __name__ == '__main__':

    # for more configuration options, please refer to `request_body.json`.
    settings = {
        'layout_border': 0,                             # PDF page layout: Without border
        'layout_mode_multiple_pages_per_sheet': 3,      # PDF page layout: Pages per sheet
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
    print('Begin uploading PDF.')
    time.sleep(3)
    cookie_init['SETTINGS_ID'], ajax_id = conversion_ajax(server_cred, cookie_init, settings, input_file, output_file)
    print('PDF uploaded. Processing.')
    time.sleep(2)

    while True:
        data = progress(cookie_init, ajax_id, server_cred)
        if data and data['action'] == 'message':  # 条件判断：使用短路策略
            pdf_url = data['url']
            break
        print('Pdf export not ready.')
        time.sleep(2)

    download_pdf('https:'+data['url'])