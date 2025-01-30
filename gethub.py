import requests
from bs4 import BeautifulSoup as BS
from queue import Queue
import threading
import sys
import os
import argparse
import textwrap

# Global variable to define the root folder name where downloaded content will be stored
ROOT_DOWNLOADS_FOLDER_NAME = "GetHub-Downloads/"

# Global variable to store the branch name of the GitHub repository being processed
# Initially set to None, it will be dynamically assigned during the scraping process
BRANCH = None

# Global queue to store root-level targets (files and directories) for processing
# This queue is used to manage the initial set of files and directories found in the repository
root_targets = Queue()

# Global queue to store directory-specific targets (files within directories) for processing
# This queue is used to manage files found within subdirectories of the repository
dir_targets = Queue()

# Function to scrape content from a GitHub repository URL
def scrap(url: str, branch: str = None, ext: str = "pdf", from_dir: bool = False):
    global BRANCH  # Use a global variable to store the branch name

    # Send a GET request to the repository URL
    resp = requests.get(url)

    # Create a BeautifulSoup instance to parse the HTML content
    soup = BS(resp.text, 'html.parser')

    # Assign the branch name dynamically
    if branch is not None:
        # If a branch is provided as an argument, use it
        BRANCH = branch
    else:
        # If no branch is provided, extract the branch name from the GitHub page
        BRANCH = soup.find('button', attrs={'id': 'branch-picker-repos-header-ref-selector'})
        BRANCH = BRANCH.findChildren('span', attrs={'class': 'eMMFM'})[0].text.strip()

    # Traverse the repository and organize the content
    arrange(soup, ext, from_dir)


# Function to organize and categorize the content found in the repository
def arrange(soup: BS, ext: str, from_dir: bool = False):
    # Search for all 'a' tags with the class 'Link--primary' (these are typically links to files or directories)
    for a in soup.find_all('a', attrs={'class': 'Link--primary'}):
        # Check if the link points to a file (contains '/blob/')
        if "/blob/" in a['href']:
            # Verify if the file is in the specified branch and has the desired file extension
            if f"/blob/{BRANCH}/" in a['href'] and a['href'].endswith(f'.{ext}'):
                # Create a target dictionary for the file
                target = {
                    'type': 'file',  # Indicates this is a file
                    'url': a['href'],  # URL of the file
                    'from_dir': from_dir  # Flag to indicate if it's from a directory
                }
                # Add the target to the appropriate queue based on the `from_dir` flag
                if from_dir:
                    dir_targets.put(target)  # Add to directory targets queue
                else:
                    root_targets.put(target)  # Add to root targets queue

        # Check if the link points to a directory (contains '/tree/')
        elif "/tree/" in a['href']:
            # Construct the full URL for the directory
            url = f"https://github.com{a['href']}"
            # Create a target dictionary for the directory
            target = {
                'type': 'dir',  # Indicates this is a directory
                'url': url,  # URL of the directory
            }
            # Add the target to the root targets queue
            root_targets.put(target)

# Function to download content from a given URL using a requests session
def download_content(url: str, sess: requests.Session, dir_path: str = None):
    # Construct the raw content URL for GitHub by replacing '/blob/' with '/refs/heads/'
    endpoint = "https://raw.githubusercontent.com" + url
    endpoint = endpoint.replace('/blob/', '/refs/heads/')

    # Extract the filename from the URL
    fname = url.split('/')[-1]

    # Send a GET request to the endpoint with streaming enabled
    resp = sess.get(url=endpoint, stream=True)
    
    # Check if the request was successful (status code 200)
    if resp.status_code == 200:
        # Open a file in binary write mode to save the downloaded content
        with open((dir_path or "") + fname, "wb") as f:
            # Write the content in chunks to handle large files efficiently
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)
            # Print a success message indicating the file has been downloaded
            sys.stdout.write(f"[+] Downloaded: {fname}\n");sys.stdout.flush() 
    else:
        # Print an error indicator if the request failed
        sys.stderr.write("x");sys.stdout.flush()
    
def download_content_from_dir(dir_url: str, branch: str, ext: str):
    scrap(url=dir_url, branch=branch, ext=ext, from_dir=True)

def main(ext: str, branch: str, repo_url:str):
    # Function to scrape content from a repository URL, given a branch and file extension
    scrap(repo_url, branch, ext=ext)
    
    # Create a session to manage and persist requests
    session = requests.session()
    
    # List to keep track of all threads for concurrent downloads
    threads = []

    # Check if there are any root targets to process
    if not root_targets.empty():
        try:
            # Create a directory to store downloaded content
            os.mkdir(ROOT_DOWNLOADS_FOLDER_NAME)
        except FileExistsError as e:
            # If directory already exists, ignore the error
            pass

    # Process all root targets until the queue is empty
    while not root_targets.empty():
        # Get the next root target from the queue
        root_target = root_targets.get()

        # Check if the target is a file
        if root_target['type'] == 'file':
            # Create a thread to download the file content
            content_thread = threading.Thread(target=download_content, args=(root_target['url'], session, ROOT_DOWNLOADS_FOLDER_NAME))
            content_thread.start()
            threads.append(content_thread)

        # Check if the target is a directory
        elif root_target['type'] == 'dir':
            # Create a thread to download content from the directory
            dir_thread = threading.Thread(target=download_content_from_dir, args=(root_target['url'], branch, ext))
            dir_thread.start()
            threads.append(dir_thread)
    
    # Wait for all threads to complete their execution
    for thread in threads:
        thread.join()

    # Process all directory targets until the queue is empty
    while not dir_targets.empty():
        # Get the next directory target from the queue
        dir_target = dir_targets.get()
        
        # Create a directory path based on the URL
        dir_path = ROOT_DOWNLOADS_FOLDER_NAME + dir_target['url'].split("/")[-2] + "/"

        try:
            # Create the directory to store downloaded content
            os.mkdir(dir_path)
        except FileExistsError as e:
            # If directory already exists, ignore the error
            pass

        # Get the URL of the directory target
        url = dir_target['url']

        # Download the content from the directory
        download_content(url, sess=session, dir_path=dir_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="GetHub", # Description dedicated to
        formatter_class=argparse.RawDescriptionHelpFormatter, 
        epilog=textwrap.dedent(
        '''
        Example: 
        python3 gethub.py -u https://github.com/Kirubel1422/GetHub -e py # file extensions
        python3 gethub.py -u https://github.com/Kirubel1422/GetHub -e py -b main # specify branch (not required)
        '''
    ))

    parser.add_argument('-u', '--url', required=True, help='Specify Repository URL')
    parser.add_argument('-e', '--extension', required=True, help='Specify file extension (eg: py, pdf, ...) without .')
    parser.add_argument('-b', '--branch', required=False, help='Specify repository branch (eg: master, main, ...)')

    arg_parse = parser.parse_args()

    branch, ext, repo_url = None, None, None
    if(arg_parse.branch):
        branch = arg_parse.branch
    
    if(arg_parse.extension):
        ext = arg_parse.extension
    
    if(arg_parse.url):
        repo_url = arg_parse.url

    main(repo_url=repo_url, ext=ext, branch=branch)