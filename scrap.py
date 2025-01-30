import requests
from bs4 import BeautifulSoup as BS
from queue import Queue
import threading
import sys
import os
import shutil

ROOT_DOWNLOADS_FOLDER_NAME="GetGit-Downloads/"
BRANCH=None

demo_repo_url = "https://github.com/pawelborkar/awesome-repos"
root_targets = Queue()
dir_targets = Queue()

def scrap(url: str, branch: str=None, ext:str = "pdf", from_dir: bool = False):
    global BRANCH

    # GET request to repository
    resp = requests.get(url)

    # BS instance from response and parsing with html.parser
    soup = BS(resp.text, 'html.parser')

    # Assign branch name dynamically
    if branch is not None:
        BRANCH = branch
    else:
        BRANCH = soup.find('button', attrs={'id': 'branch-picker-repos-header-ref-selector'})
        BRANCH = BRANCH.findChildren('span', attrs={'class': 'eMMFM'})[0].text.strip()

    # Traverse the repo
    arrange(soup, ext, from_dir)
    
def arrange(soup: BS, ext: str, from_dir: bool = False):
    # Search for all 'a' that are found in the repo
    for a in soup.find_all('a', attrs={'class': f'Link--primary'}):
        # Check if it is downloadable and endswith the specified extension
        if "/blob/" in a['href']:
            # Test if it is a file
            if f"/blob/{BRANCH}/" in a['href'] and a['href'].endswith(f'.{ext}'):
                target = {
                    'type': 'file',
                    'url': a['href'],
                    'from_dir': from_dir
                }
                if from_dir:
                    dir_targets.put(target)
                else:
                    root_targets.put(target)
                
        elif "/tree/" in a['href']:
            # Test if it is a directory
            url = f"https://github.com{a['href']}"
            target = {
                'type': 'dir',
                'url': url,
            }
            root_targets.put(target)

def download_content(url: str, sess: requests.Session, dir_path: str = None):
    endpoint = "https://raw.githubusercontent.com" + url
    endpoint = endpoint.replace('/blob/', '/refs/heads/')

    fname = url.split('/')[-1]
    resp = sess.get(url=endpoint, stream=True)
    
    if resp.status_code == 200:
        with open((dir_path or "") +fname, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)
            sys.stdout.write(f"[+] Downloaded: {fname}\n");sys.stdout.flush()
    else:
        sys.stdout.write("x");sys.stdout.flush()
    
def download_content_from_dir(dir_url: str, branch: str, ext: str):
    scrap(url=dir_url, branch=branch, ext=ext, from_dir=True)

def main(ext: str, branch: str, repo_url:str):
    scrap(repo_url, branch, ext=ext)

    session = requests.session()
    threads = []

    if not root_targets.empty():
        try:
            os.mkdir(ROOT_DOWNLOADS_FOLDER_NAME)
        except FileExistsError as e:
            pass

    while not root_targets.empty():
        root_target = root_targets.get()

        if root_target['type'] == 'file':
            content_thread = threading.Thread(target=download_content, args=(root_target['url'],session, ROOT_DOWNLOADS_FOLDER_NAME))
            content_thread.start()
            threads.append(content_thread)

        elif root_target['type'] == 'dir':
            dir_thread = threading.Thread(target=download_content_from_dir, args=(root_target['url'], branch, ext))
            dir_thread.start()
            threads.append(dir_thread)
    
    for thread in threads:
        thread.join()

    while not dir_targets.empty():
        dir_target = dir_targets.get()
        dir_path = ROOT_DOWNLOADS_FOLDER_NAME + dir_target['url'].split("/")[-2] + "/"

        try:
            os.mkdir(dir_path)
        except FileExistsError as e:
            pass

        url = dir_target['url']

        download_content(url, sess=session, dir_path=dir_path)

if __name__ == '__main__':
    main()