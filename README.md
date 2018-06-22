# rwby-spider-v2  
Updated spider to download all images from the r/RWBY subreddit flaired as art

# Details  
This spider goes through the r/RWBY subreddit in 3 phases:

1. Piggybacks on u/velvetbot's hard work for non-imgur submissions :3.

2. Goes through the submissions flaired as "art" and picks out i.redd.it images. Direct downloads.

3. Goes through the submissions flaired as "art" and picks out imgur.com images. Uses the Imgur API to download these.

# Usage

1. Have praw and imgurpython installed in your python 3.2+ environment.

```
pip install praw
pip install imgurpython
```

2. Apply for the reddit and imgur clients.

 - [Reddit Client](https://www.reddit.com/prefs/apps). Record the Application ID and secret.  
   \*NOTE: You can read more about the [PRAW](https://praw.readthedocs.io/en/latest/index.html) commands if you wish.
 - [Imgur Client](https://api.imgur.com/oauth2/addclient). Record the Client ID and secret.
   \*NOTE: You can read more about the [Imgurpython](https://apidocs.imgur.com/) commands if you wish.

3. Run **RwbySpider.py**. On the first run it will ask for your Reddit application ID, Reddit Application secret, and Imgue Client ID (not the secret). After that it should automatically  downloaded everything to /RWBY/ ordered by year-month.

# Todo

[X] Improved debugging   
[X] Grab images that Velvetbot doesn't catch?   
[ ] Create UI   
[ ] Setting to grab even older images    
[ ] Grabbing NSFW images (requires user authentication)    
[ ] Determine not Exception method to confirm reddit credentials    

