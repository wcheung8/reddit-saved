# Based on a reddit script: https://gist.github.com/dmarx/4225456
import os
import re
import imgur_album
from urllib.request import urlopen
# You probably need to download these libraries
import praw  # install with pip or easy_install
from praw.models import Comment
from PIL import Image  # install from binary: http://www.pythonware.com/products/pil/
import string
from os import listdir
from os.path import isfile, join
from bs4 import BeautifulSoup
from cred import *
import traceback

error = open('error.txt', 'w')
nonimg = open('not_img.txt', 'w')
links = open('links.txt', 'a+')
download_read = open('downloaded.txt', 'r')
download = open('downloaded.txt', 'a')

downloaded = []
for i in download_read:
    downloaded.append(i.strip())
print(downloaded)

# file types to be downloaded
_image_formats = ['bmp', 'dib', 'eps', 'ps', 'gif', 'gifv', 'im', 'jpg', 'jpe', 'jpeg',
                  'pcd', 'pcx', 'png', 'pbm', 'pgm', 'ppm', 'psd', 'tif', 'tiff',
                  'xbm', 'xpm', 'rgb', 'rast', 'svg']
_image_hosts = ['imgur', 'gfycat']


# checks for valid file type to download
def is_image_link(submission):
    for host in _image_hosts:
        if host in submission.url:
            return True
    return submission.url.split('.')[-1] in _image_formats

# formats the title to a valid filename to save
def format_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    return filename

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# requests and writes to image file
def saveImage(url, fpath):
    contents = urlopen(url)
    f = open(fpath, 'wb')
    f.write(contents.read())
    f.close()

# checks if file already exists
def fileExists(filename, path="./"):
    return format_filename(filename) in [format_filename(f) for f in listdir(path) if isfile(join(path, f))]

def writeLink(link):
    if isinstance(link, Comment):
        links.write('https://www.reddit.com/'+str(link)+'\n')
        links.write("---------------------------------------------------------\n")
    links.write(format_filename(link.title) + '\n')
    links.write('https://www.reddit.com/'+str(link)+'\n')
    links.write("---------------------------------------------------------\n")


# create directory to save
mkdir('./saved/')

# enter credentials
r = praw.Reddit(client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                username=user,
                password=password)

# instantiate reddit user and query for saved links
user = r.user.me()
saved = user.saved(limit=None)


# list of links that need fixing
issue_links = []
# go through each link and download
for link in saved:

    # skip comments
    if isinstance(link, Comment):
        continue

    try:
        
        # skip downloaded files
        if str(link) in downloaded:
            continue
    
        # init filename and params
        fname = link.url.split('/')[-1]
        extension = fname.split('.')[-1]
        title = format_filename(link.title)
        url = link.url

        # check gfycat
        if 'gfycat.com' in url:
            html = str(urlopen(url).readlines())
            parsed_html = BeautifulSoup(html, "lxml")
            url = parsed_html.body.find('a', attrs={'id':'large-gif'})['href']
            extension = ".gif"
        
        # check imgur album
        match = re.match("(https?)\:\/\/(www\.)?(?:m\.)?imgur\.com/(a|gallery)/([a-zA-Z0-9]+)(#[0-9]+)?", url)
        if match:
            mkdir(str(link.subreddit))
            path = str(link.subreddit) + "/"
            downloader = imgur_album.ImgurAlbumDownloader(url)
            downloader.save_images(path+title)
            continue

        # check not image
        if not is_image_link(link):
            nonimg.write(link.url + "\n")
            continue

        # create folder to place link based on subreddit
        mkdir(str(link.subreddit))
        path = str(link.subreddit) + "/"
            
        # check gifv extension
        if 'gifv' in extension:
            extension = ".gif"
            url = url[:-5] + '.gif'
        else:
            filename = title + '.' + extension

        # print progress
        print(title, "\n", url, "\n---------------------------------------------------------")

        # S E C U R I T Y
        if 'https' not in url:
            url = url.replace("http", "https")

        
        # download file
        if fileExists(filename, path):
            filename = title +"_" + str(len([format_filename(f) for f in listdir(path) if isfile(join(path, f))])) + extension

        saveImage(url, path + filename)

        downloaded.append(str(link))
        download.write(str(link) + "\n")
        writeLink(link)

    except Exception as e:
        # Encountered issue downloading image. Image is probably somewhere in the page
        # or might not be a filetype supported by PIL
        error.write(link.url + "\n")
        traceback.print_exc()
        try:
            print('rip - ' + link.url)
        except:
            print('rip')

