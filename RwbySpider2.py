import praw # reddit API
import prawcore.exceptions
from datetime import datetime
import requests
import json
import urllib
import urllib.request
import re
import pathlib
import configparser # reading config file
import base64 # encryption
import getpass

def main():
    c = [0,0,0,0,0,0] # counts images
    pathlib.Path('RWBY').mkdir(parents=True, exist_ok=True) # create RWBY folder

    # settings.ini file not found
    if not pathlib.Path("settings.ini").is_file():
        print("settings.ini not found. Creating new file...")
        new_settings()
    
    # reading settings.ini file
    config = configparser.ConfigParser()
    config.read('settings.ini')
    DEBUG = config['DEFAULT'].getboolean('debug',False) # enable/[disable] debug messages
    
    # optional decryption
    p = ""
    if config['DEFAULT'].getboolean('encrypt',False):
        p = getpass.getpass("Client information is encrpyted. Please enter password: ")
    
    # test to see if reddit credentials are correct
    reddit = praw.Reddit(client_id=decode(p,config['DEFAULT'].get('Reddit Client ID')),
                         client_secret=decode(p,config['DEFAULT'].get('Reddit Client Secret')),
                         user_agent='Python:r/RWBY Spider')
    
    try:
        reddit.user.preferences()
    except prawcore.exceptions.Forbidden as E:
        error = E.args[0]
        if '403' in error:
            print("Reddit Application accepted")
    except prawcore.exceptions.ResponseException:
        print("Reddit Application Error. Either the key is incorrect, or your client credentials are wrong.")
        print("(If you continue to have problems, you can reset your settings by deleting the settings.ini file)")
        input("Press Enter to continue...")
        exit()
   
    # test to see if Imgur credentials are correct
    headers = {'authorization': 'Client-ID '+decode(p,config['DEFAULT'].get('Imgur Client ID'))} # For Imgur authorization
    url = "https://api.imgur.com/3/credits"
    response = requests.request("GET", url,headers=headers)
    if json.loads(response.text)["success"]:
        print("Imgur Application accepted")
    else:
        print("Imgur Application Error. Either the key is incorrect, or your client credentials are wrong.")
        print("(If you continue to have problems, you can reset your settings by deleting the settings.ini file)")
        input("Press Enter to continue...")
        exit()

    ##############################
    # Part 1: Direct Imgur links #
    ##############################
    print("Downloading Direct Imgur Links")
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
                    c[0] += 1
                    c[1] += download(d,item["link"],item["link"][20:],DEBUG)
            else:
                if DEBUG: print("Unable to retrieve album " + parse_token(r))
                continue
        else: # it's an image
            url = "https://api.imgur.com/3/image/" + parse_token(r)
            response = requests.request("GET", url, headers=headers)
            if json.loads(response.text)["success"]:
                j = json.loads(response.text)["data"]
                c[0] += 1
                c[1] += download(d,j["link"],j["link"][20:],DEBUG)
    
    ##################################################
    # Part 2: Indirect Imgur links through velvetbot #
    ##################################################
    print("Downloading Velvetbot links")
    results = reddit.redditor('velvetbot').comments.new()
    for result in results:
        r = re.search('\[Imgur( Album)?\]\((.*?)\)',result.body)
        if r is None:
            continue
        r = r.group(2) # group 0 is the entire thing, group 1 is the album match and group 2 is the link
        d = datetime.utcfromtimestamp(result.created_utc)
        if is_album(r):
            url = "https://api.imgur.com/3/album/"+parse_token(r)+"/images"
            response = requests.request("GET", url, headers=headers)
            if json.loads(response.text)["success"]:
                for item in json.loads(response.text)["data"]:
                    c[2] += 1
                    c[3] += download(d,item["link"],item["link"][20:],DEBUG)
            else:
                if DEBUG: print("Unable to retrieve album " + parse_token(r))
                continue
        else: # it's an image
            url = "https://api.imgur.com/3/image/" + parse_token(r)
            response = requests.request("GET", url, headers=headers)
            if json.loads(response.text)["success"]:
                j = json.loads(response.text)["data"]
                c[2] += 1
                c[3] += download(d,j["link"],j["link"][20:],DEBUG)

    ##################################
    # Part 3: Direct i.redd.it links #
    ##################################
    print("Downloading Reddit Links")
    params = {'sort':'new', 'time_filter':'year'}
    results = reddit.subreddit('rwby').search('flair:art site:i.redd.it', **params)
    for result in results:
        r = result.url
        d = datetime.utcfromtimestamp(result.created_utc)
        c[4] += 1
        c[5] += download(d,r,r[18:],DEBUG)
    
    print("Summary")
    print("Downloaded Direct Imgur Links: " + str(c[1]))
    print("Existing Direct Imgur Links: " + str(c[0]))
    print("Downloaded Velvetbot Links: " + str(c[3]))
    print("Existing Velvetbot Links: " + str(c[2]))
    print("Downloaded Direct Reddit Links: " + str(c[5]))
    print("Existing Direct Reddit Links: " + str(c[4]))
    print("Done!")
    if DEBUG: input("Press Enter to continue...")
    exit()

# https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password
def encode(key, clear):
    """ Vigenere cipher encoder """
    if not len(key): return clear
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.b64encode("".join(enc).encode()).decode()

def decode(key, enc):
    """ Vigenere cipher decoder """
    if not len(key): return enc
    dec = []
    enc = base64.b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

def parse_token(token):
    """ Parses an Imgur URL and returns the string token. """
    domain_pattern = r"(https:/|http:/)?(/i\.)?(/m\.)?(/)?(imgur.com/)?(a/)?(gallery/)?(\.jpg.*|\.jpeg.*|\.png.*|\.gif.*)?(\?.*)?"
    token_pattern = r"([a-zA-Z0-9]+)"

    stripped_id = re.sub(domain_pattern, '', token, flags = re.IGNORECASE) # Drop the domain and extension.
    token = re.search(token_pattern, stripped_id).groups()[0] # Drop the album/gallery note.
    return token

def is_album(url):
    """ Parses an Imgur URL and returns True if it is an album or directory. """
    domain_pattern = r"(imgur.com/)(a/|gallery/)"
    result = re.search(domain_pattern, url, flags = re.IGNORECASE)
    if result is None:
        return False
    else:
        return True
        
def download(date, url, name, DEBUG):
    """ Downloads image file, returning 1 is file is downloaded, and 0 if file already exists."""
    pathlib.Path("RWBY/"+str(date.year)+"-"+str(date.month)).mkdir(parents=True, exist_ok=True)
    file = "RWBY/"+str(date.year)+"-"+str(date.month)+"/"+name
    if not pathlib.Path(file).is_file():
        urllib.request.urlretrieve(url,file)
        if DEBUG: print("Downloaded: "+url)
        return 1
    else:
        if DEBUG: print("Already existing: "+url)
        return 0
        
def new_settings():
    """ Creates settings.ini with the following information:
    
    Reddit Client ID
    Reddit Client Secret
    Imgur Client ID
    Optional Encrpytion of the above credentials
    """
    config = configparser.ConfigParser()
    config['DEFAULT'] = {}
    config['DEFAULT']['debug'] = '0'
    config['DEFAULT']['encrypt'] = '0'
    config['DEFAULT']['Reddit Client ID'] = input("Please enter your Reddit Client ID: ")
    config['DEFAULT']['Reddit Client Secret'] = input("Please enter your Reddit Client Secret: ")
    config['DEFAULT']['Imgur Client ID'] = input("Please enter your Imgur Client ID: ")
    while True:
        a = input("Do you want to encrypt your clients.key file? [Y/n]: ")
        if a in ['Y','y','N','n','']: break
        print("invalid response")
    if a in ['Y','y','']:
        p = getpass.getpass("Enter password to use: ")
        config['DEFAULT']['Reddit Client ID'] = encode(p,config['DEFAULT']['Reddit Client ID'])
        config['DEFAULT']['Reddit Client Secret'] = encode(p,config['DEFAULT']['Reddit Client Secret'])
        config['DEFAULT']['Imgur Client ID'] = encode(p,config['DEFAULT']['Imgur Client ID'])
        config['DEFAULT']['encrypt'] = 1
    with open('settings.ini', 'w') as cf:
        config.write(cf)


if __name__ == "__main__":
    main()