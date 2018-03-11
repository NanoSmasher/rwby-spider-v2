import praw
from datetime import datetime
import requests
import json
import urllib
import urllib.request
import re

import pathlib
pathlib.Path('RWBY').mkdir(parents=True, exist_ok=True)

creds = []
with open('clients.key', 'r') as f: # wow much secure
    creds = f.read().splitlines()
#0 Reddit Client ID
#1 Reddit Client Secret
#2 Imgur Client ID

reddit = praw.Reddit(client_id=creds[0],client_secret=creds[1],user_agent='Python:r/RWBY Spider')

# Functions
def parse_token(token):
    """ Takes in either a URL and returns the string token.
    """
    domain_pattern = r"(https:/|http:/)?(/i\.)?(/m\.)?(/)?(imgur.com/)?(a/)?(gallery/)?(\.jpg.*|\.jpeg.*|\.png.*|\.gif.*)?(\?.*)?"
    token_pattern = r"([a-zA-Z0-9]+)"

    stripped_id = re.sub(domain_pattern, '', token, flags = re.IGNORECASE) # Drop the domain and extension.
    token = re.search(token_pattern, stripped_id).groups()[0] # Drop the album/gallery note.
    return token

def is_album(url):
    """ Parses a URL if it is an album or not directory. 

    Return True if the album URL is found,
    Return False otherwise.
    """
    domain_pattern = r"(imgur.com/)(a/|gallery/)"
    result = re.search(domain_pattern, url, flags = re.IGNORECASE)
    if result is None:
        return False
    else:
        return True
        
def download(date, url, name):
    pathlib.Path("RWBY/"+str(date.year)+"-"+str(date.month)).mkdir(parents=True, exist_ok=True)
    file = "RWBY/"+str(date.year)+"-"+str(date.month)+"/"+name
    if not pathlib.Path(file).is_file():
        urllib.request.urlretrieve(url,file)
        print("Created: "+file)
    else:
        print("Already existing: "+file)

headers = {'authorization': 'Client-ID '+creds[2]} # For Imgur authorization

##############################
# Part 1: Direct Imgur links #
##############################
print("Direct Imgur Links")

params = {'sort':'new', 'time_filter':'year'}
results = reddit.subreddit('rwby').search('flair:art site:imgur.com', **params)

for result in results:
    r = result.url
    d = datetime.utcfromtimestamp(result.created_utc)
    if is_album(r):
        url = "https://api.imgur.com/3/album/"+parse_token(r)+"/images"
        response = requests.request("GET", url, headers=headers)
        if json.loads(response.text)["success"]:
            for item in json.loads(response.text)["data"]:
                download(d,item["link"],item["link"][20:])
    else: # it's an image
        url = "https://api.imgur.com/3/image/" + parse_token(r)
        response = requests.request("GET", url, headers=headers)
        if json.loads(response.text)["success"]:
            j = json.loads(response.text)["data"]
            download(d,j["link"],j["link"][20:])

##################################################
# Part 2: Indirect Imgur links through velvetbot #
##################################################
print("Velvetbot links")
results = reddit.redditor('velvetbot').comments.new()
for result in results:
    r = re.search('\[Imgur( Album)?\]\((.*?)\)',result.body)
    if r is None:
        continue
    r = r.group(2)
    # group 0 is the entire thing, group 1 is the album match and group 2 is the link
    d = datetime.utcfromtimestamp(result.created_utc)
    if is_album(r):
        url = "https://api.imgur.com/3/album/"+parse_token(r)+"/images"
        response = requests.request("GET", url, headers=headers)
        j = json.loads(response.text)["data"]
        #if j["success"]:
        for item in j:
            download(d,item["link"],item["link"][20:])
    else: # it's an image
        url = "https://api.imgur.com/3/image/" + parse_token(r)
        response = requests.request("GET", url, headers=headers)
        j = json.loads(response.text)["data"]
        download(d,j["link"],j["link"][20:])

##################################
# Part 3: Direct i.redd.it links #
##################################
print("Reddit Links")
params = {'sort':'new', 'time_filter':'year'}
results = reddit.subreddit('rwby').search('flair:art site:i.redd.it', **params)
for result in results:
    r = result.url
    d = datetime.utcfromtimestamp(result.created_utc)
    download(d,r,r[18:])