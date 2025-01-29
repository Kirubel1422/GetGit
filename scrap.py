import requests
from bs4 import BeautifulSoup as BS
from queue import Queue
import threading
import sys
import os
from datetime import datetime
import shutil

ROOT_DOWNLOADS_FOLDER_NAME="GetGit-Downloads/"
BRANCH=None

demo_repo_url = "https://github.com/bkimo/linear-algebra-python"
targets = Queue()

def scrap(url: str, branch: str=None, ext:str = "pdf"):
    global BRANCH

    # GET request to repository
    resp = requests.get(url)

    # BS instance from response and parsing with html.parser
    soup = BS(resp.content, 'html.parser')
    
    # Assign branch name dynamically
    if branch is not None:
        BRANCH = branch
    else:
        BRANCH = soup.find('button', attrs={'id': 'branch-picker-repos-header-ref-selector'})
        BRANCH = BRANCH.findChildren('span', attrs={'class': 'eMMFM'})[0].text.strip()
    
    # Traverse the repo
    arrange(soup, ext)
    
def arrange(soup: BS, ext):
    # Search for all 'a' that are found in the repo
    for a in soup.find_all('a', attrs={'class': f'Link--primary'}):
        # Check if it is downloadable and endswith the specified extension

        if "/blob/" in a['href']:
            # Test if it is a file
            if f"/blob/{BRANCH}/" in a['href'] and a['href'].endswith(f'.{ext}'):
                target = {
                    'type': 'file',
                    'url': a['href']
                }
                
                # targets.put(target)
                
        elif "/tree/" in a['href']:
            # Test if it is a directory
            target = {
                'type': 'dir',
                'url': demo_repo_url+ a['href']
            }
            targets.put(target)

def download_content(url: str, sess: requests.Session):
    return
    endpoint = "https://raw.githubusercontent.com" + url
    endpoint = endpoint.replace('/blob/', '/refs/heads/')

    fname = url.split('/')[-1]
    resp = sess.get(url=endpoint, stream=True)
    
    if resp.status_code == 200:
        with open(ROOT_DOWNLOADS_FOLDER_NAME+fname, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)
            print(f"[+] Downloaded: {fname}")
    else:
        sys.stdout.write("x");sys.stdout.flush()
    

def download_content_from_dir(dir_url, sess: requests.Session):
    dir_name = dir_url.split('/')[-1]

    try:
        os.mkdir(ROOT_DOWNLOADS_FOLDER_NAME+dir_name)
    except FileExistsError as e:
        shutil.rmtree(ROOT_DOWNLOADS_FOLDER_NAME+dir_name)
        os.mkdir(ROOT_DOWNLOADS_FOLDER_NAME+dir_name)
        
    scrap(url=dir_url)

def main():
    scrap(demo_repo_url, ext="pdf")

    session = requests.session()
    threads = []

    if not targets.empty():
        try:
            os.mkdir(ROOT_DOWNLOADS_FOLDER_NAME)
        except FileExistsError as e:
            shutil.rmtree(ROOT_DOWNLOADS_FOLDER_NAME)
            os.mkdir(ROOT_DOWNLOADS_FOLDER_NAME)

    while not targets.empty():
        target = targets.get()

        if target['type'] == 'file':
            content_thread = threading.Thread(target=download_content, args=(target['url'],session))
            content_thread.start()
            threads.append(content_thread)

        elif target['type'] == 'dir':
            dir_thread = threading.Thread(target=download_content_from_dir, args=(target['url'],session))
            dir_thread.start()
            threads.append(dir_thread)

if __name__ == '__main__':
    main()