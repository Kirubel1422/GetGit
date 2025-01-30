# GetHub - GitHub Repository Content Downloader 🔍📥

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/downloads/)
![Dependencies](https://img.shields.io/badge/dependencies-requests%20%7C%20beautifulsoup4-green)

A powerful tool to download specific file types from GitHub repositories. Perfect for researchers, developers, and content curators who need to extract specific assets from GitHub projects.

## Features ✨

- ⚡ **Fast concurrent downloads** using threading
- 🎯 **Target specific file extensions** (PDF, Python, JPG, etc.)
- 🌿 **Branch-specific scraping** (master/main or custom branches)
- 📂 **Automatic directory structure preservation**
- 🛡️ **Session persistence** for efficient downloading
- 📊 Progress feedback with real-time status updates

## Installation 📦

```bash
# Clone repository
git clone https://github.com/Kirubel1422/GetHub.git

# Install dependencies
pip install -r requirements.txt

# (Recommended) Use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

## Usage 🚀

### Basic Command

```bash
python3 gethub.py -u <repository_url> -e <file_extension>
```

### Examples

```bash
# Download all Python files from a repository
python3 gethub.py -u https://github.com/Kirubel1422/GetHub -e py

# Download PDFs from specific branch
python3 gethub.py -u https://github.com/Kirubel1422/GetHub -e pdf -b main

# Download multiple file types (run sequentially)
python3 gethub.py -u https://github.com/user/repo -e py && \
python3 gethub.py -u https://github.com/user/repo -e md
```

## Contributing 🤝

- Fork the repository
- Create feature branch: git checkout -b feat/new-feature
- Commit changes: git commit -m 'Add awesome feature'
- Push to branch: git push origin feat/new-feature
- Open pull request
