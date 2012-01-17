#!/usr/bin/python

#Icefilms.info v1.1.0 - anarchintosh / daledude / WestCoast13 / Eldorado

#All code Copyleft (GNU GPL v2) Anarchintosh and icefilms-xbmc team

############### Imports ############################
#standard module imports
import sys,os
import time,re
import urllib,urllib2,cookielib,base64
import unicodedata
import random
import copy
import threading
import string

############ Set prepare_zip to True in order to scrape the entire site to create a new meta pack ############
''' 
Setting to true will also enable a new menu option 'Create Meta Pack' which will scrape all categories and download covers & backdrops 
'''

#prepare_zip = True
prepare_zip = False


##############################################################################################################


import xbmc,xbmcplugin,xbmcgui,xbmcaddon, datetime

#get path to me
addon_id = 'plugin.video.icefilms'
selfAddon = xbmcaddon.Addon(id=addon_id)
icepath = selfAddon.getAddonInfo('path')

#append lib directory
sys.path.append( os.path.join( icepath, 'resources', 'lib' ) )

#imports of things bundled in the addon
import container_urls,clean_dirs,htmlcleaner,megaroutines
from metahandler import metahandlers
from cleaners import *
from xgoogle.BeautifulSoup import BeautifulSoup,BeautifulStoneSoup
from xgoogle.search import GoogleSearch
#Common Cache
import xbmcvfs
# plugin constants
dbg = True # Set to false if you don't want debugging

try:
  import StorageServer
except:
  import storageserverdummy as StorageServer
cache = StorageServer.StorageServer()
cache.table_name = "icefilms" # Name of your plugin.
   
####################################################

############## Constants / Variables ###############

# global constants
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
ICEFILMS_REFERRER = 'http://www.icefilms.info'

# global constants
ICEFILMS_URL = selfAddon.getSetting('icefilms-url')
ICEFILMS_AJAX = ICEFILMS_URL+'membersonly/components/com_iceplayer/video.phpAjaxResp.php'
ICEFILMS_REFERRER = 'http://www.icefilms.info'
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

#useful global strings:
iceurl = ICEFILMS_URL
meta_setting = selfAddon.getSetting('use-meta')
downloadPath = selfAddon.getSetting('download-folder')

#Auto-watch
currentTime = 1
totalTime = 1

callEndOfDirectory = True

#Variable for multi-part
finalPart = 0

#Params
url=None
name=None
mode=None
imdbnum=None
dirmode=None
season_num=None
episode_num=None
video_type=None

####################################################

def xbmcpath(path,filename):
     translatedpath = os.path.join(xbmc.translatePath( path ), ''+filename+'')
     return translatedpath
  
def Notify(typeq,title,message,times, line2='', line3=''):
     #simplified way to call notifications. common notifications here.
     if title == '':
          title='Icefilms Notification'
     if typeq == 'small' or typeq == 'Download Alert':
          if times == '':
               times='5000'
          smallicon=handle_file('smallicon')
          xbmc.executebuiltin("XBMC.Notification("+title+","+message+","+times+","+smallicon+")")
     elif typeq == 'big':
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ', line2, line3)
     elif typeq == 'megaalert1':
          ip = xbmc.getIPAddress()
          title='Megaupload Alert for IP '+ip
          message="Either you've reached your daily download limit\n or your IP is already downloading a file."
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')
     elif typeq == 'megaalert2':
          ip = xbmc.getIPAddress()
          title='Megaupload Info for IP '+ip
          message="No problems! You have not reached your limit."
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')
     else:
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')

#paths etc need sorting out. do for v1.1.0
icedatapath = 'special://profile/addon_data/plugin.video.icefilms'
metapath = icedatapath+'/mirror_page_meta_cache'
transmetapath = xbmcpath(metapath,'')
downinfopath = icedatapath+'/downloadinfologs'
transdowninfopath = xbmcpath(downinfopath,'')
translatedicedatapath = xbmcpath(icedatapath,'')
art = icepath+'/resources/art'


def handle_file(filename,getmode=''):
     #bad python code to add a get file routine.
     if filename == 'smallicon':
          return_file = xbmcpath(art,'smalltransparent2.png')
     elif filename == 'homepage':
          return_file = xbmcpath(art,'homepage.png')
     elif filename == 'movies':
          return_file = xbmcpath(art,'movies.png')
     elif filename == 'music':
          return_file = xbmcpath(art,'music.png')
     elif filename == 'tvshows':
          return_file = xbmcpath(art,'tvshows.png')
     elif filename == 'movies_fav':
        return_file = xbmcpath(art,'movies_fav.png')
     elif filename == 'tvshows_fav':
        return_file = xbmcpath(art,'tvshows_fav.png')

     elif filename == 'other':
          return_file = xbmcpath(art,'other.png')
     elif filename == 'search':
          return_file = xbmcpath(art,'search.png')
     elif filename == 'standup':
          return_file = xbmcpath(art,'standup.png')
     elif filename == 'megapic':
          return_file = xbmcpath(art,'megaupload.png')
     elif filename == 'shared2pic':
          return_file = xbmcpath(art,'2shared.png')
     elif filename == 'localpic':
          return_file = xbmcpath(art,'local_file.jpg')

     if getmode == '':
          return return_file
     if getmode == 'open':
          try:
               opened_return_file=openfile(return_file)
               return opened_return_file
          except:
               print 'opening failed'
     
def openfile(filename):
     fh = open(filename, 'r')
     contents=fh.read()
     fh.close()
     return contents

def save(filename,contents):  
     fh = open(filename, 'w')
     fh.write(contents)  
     fh.close()

def appendfile(filename,contents):  
     fh = open(filename, 'a')
     fh.write(contents)  
     fh.close()


def DLDirStartup():

  # Startup routines for handling and creating special download directory structure 
  SpecialDirs=selfAddon.getSetting('use-special-structure')

  if SpecialDirs == 'true':

     if downloadPath:
        if os.path.exists(downloadPath):
          #initial_path=os.path.join(downloadPath,'Icefilms Downloaded Videos')
          tvpath=os.path.join(downloadPath,'TV Shows')
          moviepath=os.path.join(downloadPath,'Movies')

          tv_path_exists=os.path.exists(tvpath)
          movie_path_exists=os.path.exists(moviepath)

          if tv_path_exists == False or movie_path_exists == False:

            #IF BASE DIRECTORY STRUCTURE DOESN'T EXIST, CREATE IT
            #Also Add README files to TV Show and Movies direcories.
            #(readme files stops folders being deleted when running the DirCleaner)

            if tv_path_exists == False:
               os.makedirs(tvpath)
               tvreadme='Add this folder to your XBMC Library, and set it as TV to scan for metadata with TVDB.'
               tvreadmepath=os.path.join(tvpath,'README.txt')
               save(tvreadmepath,tvreadme)

            if movie_path_exists == False:
               os.makedirs(moviepath)
               moviereadme='Add this folder to your XBMC Library, and set it as Movies to scan for metadata with TheMovieDB.'
               moviereadmepath=os.path.join(moviepath,'README.txt')
               save(moviereadmepath,moviereadme)

          else:
              #IF DIRECTORIES EXIST, CLEAN DIRECTORY STRUCTURE (REMOVE EMPTY DIRECTORIES)
               clean_dirs.do_clean(tvpath)
               clean_dirs.do_clean(moviepath)


def LoginStartup():
     #Get whether user has set an account to use.
     Account = selfAddon.getSetting('megaupload-account')

     mu=megaroutines.megaupload(translatedicedatapath)

     #delete old logins
     mu.delete_login()
     
     if Account == 'false':
          print 'Account: '+'no account set'
          return True

     elif Account == 'true':
          #check for megaupload login and do it
          
          megauser = selfAddon.getSetting('megaupload-username')
          megapass = selfAddon.getSetting('megaupload-password')

          try:
              login=mu.set_login(megauser,megapass)
                       
              if megapass != '' and megauser != '':
                   if login is False:
                        print 'Account: '+'login failed'
                        Notify('big','Megaupload','Login failed. Megaupload will load with no account.','')
                   elif login is True:
                        print 'Account: '+'login succeeded'
                        HideSuccessfulLogin = selfAddon.getSetting('hide-successful-login-messages')
                        if HideSuccessfulLogin == 'false':
                             Notify('small','Megaupload', 'Account login successful.','')
                             
              if megapass == '' or megauser == '':
                   print 'no login details specified, using no account'
                   Notify('big','Megaupload','Login failed. Megaupload will load with no account.','')
              return True
          except Exception, e:
              print '**** MegaUpload Error: %s' % e
              Notify('big','Megaupload Failed','Failed to connect with MegaUpload.', '', '', 'Please check your internet connection.')
              pass
              return False
              
                                
def ContainerStartup():

     #Check for previous Icefilms metadata install and delete
     meta_folder = os.path.join(translatedicedatapath, 'meta_caches')
     if os.path.exists(meta_folder):
         import shutil
         try:
             print 'Removing previous Icefilms meta folder: %s' % meta_folder
             shutil.rmtree(meta_folder)
         except Exception, e:
             print 'Failed to delete Icefilms meta folder: %s' % e
             pass

     #Initialize MetaHandler and MetaContainer classes
     #MetaContainer will clean up from previous installs, so good idea to always initialize at addon startup
     from metahandler import metacontainers
     mh=metahandlers.MetaData(preparezip=prepare_zip)
     mc = metacontainers.MetaContainer()

     #Check meta cache DB if meta pack has been installed     
     meta_installed = mh.check_meta_installed(addon_id)
     
     #get containers dict from container_urls.py
     containers = container_urls.get()  

     work_path = mc.work_path
                            
     if not meta_installed:

         #Offer to download the metadata DB
         dialog = xbmcgui.Dialog()
         ret = dialog.yesno('Download Meta Containers '+str(containers['date'])+' ?', 'There is a metadata container avaliable.','Install it to get meta information for videos.', 'Would you like to get it? Its a small '+str(containers['db_size'])+'MB download.','Remind me later', 'Install')
         
         if ret==True:
                 
              #download dem files
              get_db_zip=Zip_DL_and_Install(containers['db_url'],'database', work_path, mc)

              #do nice notification
              if get_db_zip==True:
                   Notify('small','Metacontainer DB Installation Success','','')
                   
                   #Update meta addons table to indicate meta pack was installed with covers
                   mh.insert_meta_installed(addon_id, last_update=containers['date'])
                   
                   #Re-check meta_installed
                   meta_installed = mh.check_meta_installed(addon_id)
              
              elif get_db_zip==False:
                   Notify('small','Metacontainer DB Installation Failure','','')

     #Only check/prompt for image pack downloads if the DB has been downloaded/installed
     if meta_installed:

         #Get metadata settings
         movie_fanart = selfAddon.getSetting('movie-fanart')
         movie_covers = selfAddon.getSetting('movie-covers')
         tv_covers = selfAddon.getSetting('tv-covers')
         tv_posters = selfAddon.getSetting('tv-posters')
         tv_fanart = selfAddon.getSetting('tv-fanart')
     
         #TV Covers/Banners
         if tv_covers =='true':
             if tv_posters == 'true':
                 tv_installed = meta_installed['tv_covers']
                 tv_zip = containers['tv_covers_url']
                 tv_size = containers['tv_cover_size']
             else:
                 tv_installed = meta_installed['tv_banners']
                 tv_zip = containers['tv_banners_url']
                 tv_size = containers['tv_banners_size']

             if tv_installed == 'false':
                 dialog = xbmcgui.Dialog()
                 ret = dialog.yesno('Download TV Covers?', 'There is a metadata container avaliable.','Install it to get cover images for TV Shows.', 'Would you like to get it? Its a large ' + str(tv_size) + 'MB download.','Remind me later', 'Install')
                 if ret==True:
                     #download dem files
                     get_cover_zip=Zip_DL_and_Install(tv_zip,'tv_images', work_path, mc)
                     
                     if get_cover_zip:
                         if tv_posters =='true':
                             mh.update_meta_installed(addon_id, tv_covers='true')
                         else:
                             mh.update_meta_installed(addon_id, tv_banners='true')
                         Notify('small','TV Cover Installation Success','','')
                     else:
                         print '******* ERROR - TV cover install failed'
                         Notify('small','TV Cover Installation Failure','','')                     
             else:
                 print 'TV Covers already installed'

         #Movie Covers
         if movie_covers =='true':
             if meta_installed['movie_covers'] == 'false':
                 dialog = xbmcgui.Dialog()
                 ret = dialog.yesno('Download Movie Covers?', 'There is a metadata container avaliable.','Install it to get cover images for Movies.', 'Would you like to get it? Its a large '+str(containers['mv_cover_size'])+'MB download.','Remind me later', 'Install')
                 if ret==True:
                     #download dem files
                     get_cover_zip=Zip_DL_and_Install(containers['mv_covers_url'],'movie_images', work_path, mc)
                     
                     if get_cover_zip:
                         mh.update_meta_installed(addon_id, movie_covers='true')
                         Notify('small','Movie Cover Installation Success','','')
                     else:
                         print '******* ERROR - Movie cover install failed'
                         Notify('small','Movie Cover Installation Failure','','')                     
             else:
                 print 'Movie Covers already installed'

         #Movie Fanart
         if movie_fanart =='true':
             if meta_installed['movie_backdrops'] == 'false':
                 dialog = xbmcgui.Dialog()
                 ret = dialog.yesno('Download Movie Fanart?', 'There is a metadata container avaliable.','Install it to get background images for Movies.', 'Would you like to get it? Its a large '+str(containers['mv_backdrop_size'])+'MB download.','Remind me later', 'Install')
                 if ret==True:
                     #download dem files
                     get_backdrop1_zip=Zip_DL_and_Install(containers['mv_backdrop_1_url'],'movie_images', work_path, mc)
                     get_backdrop2_zip=Zip_DL_and_Install(containers['mv_backdrop_2_url'],'movie_images', work_path, mc)
                     get_backdrop3_zip=Zip_DL_and_Install(containers['mv_backdrop_3_url'],'movie_images', work_path, mc)
                     
                     if get_backdrop1_zip and get_backdrop2_zip and get_backdrop3_zip:
                         mh.update_meta_installed(addon_id, movie_backdrops='true')
                         Notify('small','Movie Fanart Installation Success','','')
                     else:
                         print '******* ERROR - Movie backrop install failed'
                         Notify('small','Movie Fanart Installation Failure','','')
             else:
                 print 'Movie fanart already installed'

         #TV Fanart
         if tv_fanart =='true':
             if meta_installed['tv_backdrops'] == 'false':
                 dialog = xbmcgui.Dialog()
                 ret = dialog.yesno('Download TV Show Fanart?', 'There is a metadata container avaliable.','Install it to get background images for TV Shows.', 'Would you like to get it? Its a large '+str(containers['tv_backdrop_size'])+'MB download.','Remind me later', 'Install')
                 if ret==True:
                     #download dem files
                     get_backdrop_zip=Zip_DL_and_Install(containers['tv_backdrop_url'],'tv_images', work_path, mc)
                     
                     if get_backdrop_zip:
                         mh.update_meta_installed(addon_id, tv_backdrops='true')
                         Notify('small','TV Fanart Installation Success','','')
                     else:
                         print '******* ERROR - TV backrop install failed'
                         Notify('small','TV Fanart Installation Failure','','')                     
    
             else:
                 print 'TV fanart already installed'


def Zip_DL_and_Install(url,installtype,work_folder,mc):
     ####function to download and install a metacontainer. ####

     url = str(url)

     #get the download url
     mu=megaroutines.megaupload(translatedicedatapath)
     print 'Download URL: %s' % url
     thefile=mu.resolve_megaup(url)

     #define the path to save it to
     filepath=os.path.normpath(os.path.join(work_folder,thefile[1]))

     filepath_exists=os.path.exists(filepath)
     #if zip does not already exist, download from url, with nice display name.
     if filepath_exists==False:
                    
         print 'Downloading zip: %s' % thefile[0]
         do_wait(thefile[3], thefile[4])
         Download(thefile[0], filepath, installtype)
       
     elif filepath_exists==True:
          print 'zip already downloaded, attempting extraction'                   
          
     print '!!!!handling meta install!!!!'
     return mc.install_metadata_container(filepath, installtype)


def Startup_Routines():
     

     # avoid error on first run if no paths exists, by creating paths
     if not os.path.exists(translatedicedatapath): os.makedirs(translatedicedatapath)
     if not os.path.exists(transdowninfopath): os.makedirs(transdowninfopath)
     if not os.path.exists(transmetapath): os.makedirs(transmetapath)
         
     #force refresh addon repositories, to check for updates.
     #xbmc.executebuiltin('UpdateAddonRepos')
     
     # Run the startup routines for special download directory structure 
     DLDirStartup()

     # Run the login startup routines
     if LoginStartup():
     
         # Run the container checking startup routines, if enable meta is set to true
         if meta_setting=='true': ContainerStartup()

     
     #Rescan Next Aired on startup - actually only rescans every 24hrs
     xbmc.executebuiltin("RunScript(%s, silent=true)" % os.path.join(icepath, 'resources/script.tv.show.next.aired/default.py'))

def create_meta_pack():
       
    # This function will scrape all A-Z categories of the entire site
    
    A2Z=[chr(i) for i in xrange(ord('A'), ord('Z')+1)]
    
    print '### GETTING MOVIE METADATA FOR ALL *MUSIC* ENTRIES'
    MOVIEINDEX(iceurl + 'music/a-z/1')
    print '### GETTING MOVIE METADATA FOR ALL *STANDUP* ENTRIES'
    MOVIEINDEX(iceurl + 'standup/a-z/1')
    print '### GETTING MOVIE METADATA FOR ALL *OTHER* ENTRIES'
    MOVIEINDEX(iceurl + 'other/a-z/1')
    print '### GETTING MOVIE METADATA FOR ALL ENTRIES ON: '+'1'
    MOVIEINDEX(iceurl + 'movies/a-z/1')
    for theletter in A2Z:
         print '### GETTING MOVIE METADATA FOR ALL ENTRIES ON: '+theletter
         MOVIEINDEX(iceurl + 'movies/a-z/' + theletter)

         
    print '### GETTING TV METADATA FOR ALL ENTRIES ON: '+'1'
    TVINDEX(iceurl + 'tv/a-z/1')
    for theletter in A2Z:
         print '### GETTING TV METADATA FOR ALL ENTRIES ON: '+theletter
         TVINDEX(iceurl + 'tv/a-z/' + theletter)


def CATEGORIES():  #  (homescreen of addon)

          #run startup stuff
          Startup_Routines()
          print 'Homescreen'

          #get necessary paths
          homepage=handle_file('homepage','')
          tvshows=handle_file('tvshows','')
          movies=handle_file('movies','')
          music=handle_file('music','')
          standup=handle_file('standup','')
          other=handle_file('other','')
          search=handle_file('search','')

          #add directories
          HideHomepage = selfAddon.getSetting('hide-homepage')
          
          addDir('TV Shows',iceurl+'tv/a-z/1',50,tvshows)
          addDir('Movies',iceurl+'movies/a-z/1',51,movies)
          addDir('Music',iceurl+'music/a-z/1',52,music)
          addDir('Stand Up Comedy',iceurl+'standup/a-z/1',53,standup)
          addDir('Other',iceurl+'other/a-z/1',54,other)
          if HideHomepage == 'false':
                addDir('Homepage',iceurl+'index',56,homepage)
          addDir('Favourites',iceurl,57,os.path.join(art,'favourites.png'))
          addDir('Search',iceurl,55,search)
          
          #Only show if prepare_zip = True - meaning you are creating a meta pack
          if prepare_zip:
              addDir('Create Meta Pack',iceurl,666,'')


def prepare_list(directory,dircontents):
     #create new empty list
     stringList = []

     #Open all files in dir
     for thefile in dircontents:
          try:
               filecontents=openfile(os.path.join(directory,thefile))

               #add this to list
               stringList.append(filecontents)
                              
          except:
               print 'problem with opening a favourites item'

     #sort list alphabetically and return it.
     tupleList = [(x.lower(), x) for x in stringList]

     #wesaada's patch for ignoring The etc when sorting favourites list.
     articles = ("a","an","the")
     tupleList.sort(key=lambda s: tuple(word for word in s[1].split() if word.lower() not in articles))

     return [x[1] for x in tupleList]

def favRead(string):
     try:
          splitter=re.split('\|+', string)
          name=splitter[0]
          url=splitter[1]
          mode=int(splitter[2])
          try:
               imdb_id=str(splitter[3])
          except:
               imdb_id=''
     except:
          return None
     else:
          return name,url,mode,imdb_id

def addFavourites(enablemetadata,directory,dircontents,contentType):
    #get the strings of data from the files, and return them alphabetically
    stringlist=prepare_list(directory,dircontents)
    
    if enablemetadata == True:
        metaget=metahandlers.MetaData(preparezip=prepare_zip)
        meta_installed = metaget.check_meta_installed(addon_id)
    else:
        meta_installed = False
         
    #for each string
    for thestring in stringlist:
    
        #split it into its component parts
        info = favRead(thestring)
        if info is not None:
        
            if enablemetadata == True and meta_installed:
                #return the metadata dictionary
                if info[3] is not None:
                                       
                    #return the metadata dictionary
                    meta=metaget.get_meta(contentType, info[0], imdb_id=info[3])
                    
                    if meta is None:
                        #add all the items without meta
                        addDir(info[0],info[1],info[2],'',delfromfav=True, totalItems=len(stringlist), favourite=True)
                    else:
                        #add directories with meta
                        addDir(info[0],info[1],info[2],'',meta=meta,delfromfav=True,imdb=info[3], totalItems=len(stringlist), meta_install=meta_installed, favourite=True)
                else:
                    #add all the items without meta
                    addDir(info[0],info[1],info[2],'',delfromfav=True, totalItems=len(stringlist), favourite=True)
            else:
                #add all the items without meta
                addDir(info[0],info[1],info[2],'',delfromfav=True, totalItems=len(stringlist), favourite=True)


def FAVOURITES(url):
    #get necessary paths
    tvshows=handle_file('tvshows_fav','')
    movies=handle_file('movies_fav','')

    addDir('TV Shows',iceurl,570,tvshows)
    addDir('Movies',iceurl,571,movies)


def URL_TYPE(url):
     #Check whether url is a tv episode list or movie/mirrorpage
     if url.startswith(iceurl+'ip'):
               print 'url is a mirror page url'
               return 'mirrors'
     elif url.startswith(iceurl+'tv/series'):
               print 'url is a tv ep list url'
               return 'episodes'     

def METAFIXER(url):
     #Icefilms urls passed to me will have their proper names and imdb numbers returned.
     source=GetURL(url)

     url_type=URL_TYPE(url)

     #get proper name from the page. (in case it is a weird name)
     
     if url_type=='mirrors':
               #get imdb number.
               match=re.compile('<a class=iframe href=http://www.imdb.com/title/(.+?)/ ').findall(source)      

               #check if it is an episode. 
               epcheck=re.search('<a href=/tv/series/',source)

               #if it is, return the proper series name as opposed to the mirror page name.
               if epcheck is not None:
                    tvget=re.compile('<a href=/tv/series/(.+?)>').findall(source)
                    tvurl=iceurl+'tv/series/'+str(tvget[0])
                    #load ep page and get name from that. sorry icefilms bandwidth!
                    tvsource=GetURL(tvurl)
                    name=re.compile('<h1>(.+?)<a class').findall(tvsource)

               #return mirror page name.
               if epcheck is None:
                    name=re.compile('''<span style="font-size:large;color:white;">(.+?)</span>''').findall(source)
                    
               name=CLEANUP(name[0])
               return name,match[0]

     elif url_type=='episodes':
               #TV
               name=re.compile('<h1>(.+?)<a class').findall(source)
               match=re.compile('href="http://www.imdb.com/title/(.+?)/"').findall(source)
               name=CLEANUP(name[0])
               return name,match[0]
     
     
def ADD_TO_FAVOURITES(name,url,imdbnum):
     #Creates a new text file in favourites folder. The text file is named after the items name, and contains the name, url and relevant mode.
     print 'Adding to favourites: name: %s, imdbnum: %s, url: %s' % (name, imdbnum, url)

     if name is not None and url is not None:

          #Set favourites path, and create it if it does'nt exist.
          favpath=os.path.join(translatedicedatapath,'Favourites')
          tvfav=os.path.join(favpath,'TV')
          moviefav=os.path.join(favpath,'Movies')
          
          try:
               os.makedirs(tvfav)
          except:
               pass
          try:
               os.makedirs(moviefav)
          except:
               pass

          #Check what kind of url it is and set themode and savepath (helpful for metadata) accordingly
          

          #fix name and imdb number for Episode List entries in Search.
          if imdbnum == 'nothing':
               metafix=METAFIXER(url)
               name=metafix[0]
               imdbnum=metafix[1]

          
          url_type=URL_TYPE(url)

          if url_type=='mirrors':
               themode='100'
               savepath=moviefav
               
          elif url_type=='episodes':
               themode='12'
               savepath=tvfav

          print 'NAME:',name,'URL:',url,'IMDB NUMBER:',imdbnum

          #Delete HD entry from filename. using name as filename makes favourites appear alphabetically.
          adjustedname=Clean_Windows_String(name).strip()

          #encode the filename to the safe string
          #adjustedname=base64.urlsafe_b64encode(name)

          #Save the new favourite if it does not exist.
          NewFavFile=os.path.join(savepath,adjustedname+'.txt')
          if not os.path.exists(NewFavFile):

               #Use | as separators that can be used by re.split when reading favourites folder.
               favcontents=name+'|'+url+'|'+themode+'|'+imdbnum
               save(NewFavFile,favcontents)
               
               Notify('small',name + ' added to favourites','','6000')

               #Rescan Next Aired on startup - actually only rescans every 24hrs
               xbmc.executebuiltin("RunScript(%s, silent=true)" % os.path.join(icepath, 'resources/script.tv.show.next.aired/default.py'))
          else:
               print 'Warning - favourite already exists'
               Notify('small',name + ' favourite already exists','','6000')

     else:
          Notify('small','Unable to add to favourites','','')
          print 'Warning - favorite name or url is none:'
          print 'NAME: ',name
          print 'URL: ',url

     
def DELETE_FROM_FAVOURITES(name,url):



    #legacy check - encode the filename to the safe string *** to check ***
    old_name=base64.urlsafe_b64encode(name)
    
    #Deletes HD entry from filename
    name=Clean_Windows_String(name).strip()
      
    favpath=os.path.join(translatedicedatapath,'Favourites')
    
    url_type=URL_TYPE(url)
    
    if url_type=='mirrors':
         itempath=os.path.join(favpath,'Movies',name+'.txt')
         old_itempath=os.path.join(favpath,'Movies',old_name+'.txt')
    
    elif url_type=='episodes':
         itempath=os.path.join(favpath,'TV',name+'.txt')
         old_itempath=os.path.join(favpath,'TV',old_name+'.txt')
    
    print 'ITEMPATH: %s' % itempath
    print 'OLD ITEMPATH: %s' % old_itempath    
    
    if os.path.exists(itempath):
         os.remove(itempath)
         xbmc.executebuiltin("XBMC.Container.Refresh")
         
    if os.path.exists(old_itempath):
         os.remove(old_itempath)
         xbmc.executebuiltin("XBMC.Container.Refresh")         


def CLEAR_FAVOURITES(url):
     
     dialog = xbmcgui.Dialog()
     ret = dialog.yesno('WARNING!', 'Delete all your favourites?','','','Cancel','Go Nuclear')
     if ret==True:
          import shutil
          favpath=os.path.join(translatedicedatapath,'Favourites')
          tvfav=os.path.join(favpath,'TV')
          moviefav=os.path.join(favpath,'Movies')
          try:
               shutil.rmtree(tvfav)
          except:
               pass
          try:
               shutil.rmtree(moviefav)
          except:
               pass

def ICEHOMEPAGE(url):
        addDir('Recently Added',iceurl+'index',60,os.path.join(art,'recently added.png'))
        addDir('Latest Releases',iceurl+'index',61,os.path.join(art,'latest releases.png'))
        addDir('Being Watched Now',iceurl+'index',62,os.path.join(art,'being watched now.png'))
        setView(None, 'default-view')


def check_episode(name):
    #Episode will have eg. 01x15 within the name, else we can assume it's a movie
    if re.search('([0-9]+x[0-9]+)', name):
        return True
    else:
        return False


def get_video_name(name):
    video = {}
    if check_episode(name):
        r = re.search('[0-9]+x[0-9]+ (.+?) [(]([0-9]{4})[)]', name)        
    else:
        r = re.search('(.+?) [(]([0-9]{4})[)]',name)
    if r:
        video['name'] = r.group(1)
        video['year'] = r.group(2)
    else:
        video['name'] = name
        video['year'] = ''
    return video
        

def check_video_meta(name, metaget):
    #Determine if it's a movie or tvshow by the title returned - tv show will contain eg. 01x15 to signal season/episode number
    episode = check_episode(name)
    if episode:
        episode_info = re.search('([0-9]+)x([0-9]+)', name)
        season = int(episode_info.group(1))
        episode = int(episode_info.group(2))
        episode_title = re.search('(.+?) [0-9]+x[0-9]+', name).group(1)
        tv_meta = metaget.get_meta('tvshow',episode_title)
        meta=metaget.get_episode_meta(episode_title, tv_meta['imdb_id'], season, episode)
    else:
        r=re.search('(.+?) [(]([0-9]{4})[)]',name)
        if r:
            name = r.group(1)
            year = r.group(2)
        else:
            year = ''
        meta = metaget.get_meta('movie',name, year=year)
    return meta


def RECENT(url):
        link=GetURL(url)

        #initialise meta class before loop
        if meta_setting=='true':
            metaget=metahandlers.MetaData(preparezip=prepare_zip)
            meta_installed = metaget.check_meta_installed(addon_id)
        else:
            meta_installed = False
              
        homepage=re.compile('<h1>Recently Added</h1>(.+?)<h1>Statistics</h1>', re.DOTALL).findall(link)
        for scrape in homepage:
                scrape='<h1>Recently Added</h1>'+scrape+'<h1>Statistics</h1>'
                recadd=re.compile('<h1>Recently Added</h1>(.+?)<h1>Latest Releases</h1>', re.DOTALL).findall(scrape)
                for scraped in recadd:
                        mirlinks=re.compile('<a href=/(.+?)>(.+?)</a>').findall(scraped)
                        for url,name in mirlinks:
                                url=iceurl+url
                                name=CLEANUP(name)
                                
                                if check_episode(name):
                                    mode = 14
                                else:
                                    mode = 100

                                if meta_installed and meta_setting=='true':
                                    meta = check_video_meta(name, metaget)
                                    addDir(name,url,mode,'',meta=meta,disablefav=True, disablewatch=True, meta_install=meta_installed)
                                else:
                                    addDir(name,url,mode,'',disablefav=True, disablewatch=True)
        setView(None, 'default-view')                                    
        
def LATEST(url):
        link=GetURL(url)
        
        #initialise meta class before loop
        if meta_setting=='true':
            metaget=metahandlers.MetaData(preparezip=prepare_zip)
            meta_installed = metaget.check_meta_installed(addon_id)
        else:
            meta_installed = False
                    
        homepage=re.compile('<h1>Recently Added</h1>(.+?)<h1>Statistics</h1>', re.DOTALL).findall(link)
        for scrape in homepage:
                scrape='<h1>Recently Added</h1>'+scrape+'<h1>Statistics</h1>'
                latrel=re.compile('<h1>Latest Releases</h1>(.+?)<h1>Being Watched Now</h1>', re.DOTALL).findall(scrape)
                for scraped in latrel:
                        mirlinks=re.compile('<a href=/(.+?)>(.+?)</a>').findall(scraped)
                        for url,name in mirlinks:
                                url=iceurl+url
                                name=CLEANUP(name)

                                if check_episode(name):
                                    mode = 14
                                else:
                                    mode = 100
                                                                    
                                if meta_installed and meta_setting=='true':
                                    meta = check_video_meta(name, metaget)
                                    addDir(name,url,mode,'',meta=meta,disablefav=True, disablewatch=True, meta_install=meta_installed)
                                else:
                                    addDir(name,url,mode,'',disablefav=True, disablewatch=True)
        setView(None, 'default-view')


def WATCHINGNOW(url):
        link=GetURL(url)

        #initialise meta class before loop
        if meta_setting=='true':
            metaget=metahandlers.MetaData(preparezip=prepare_zip)
            meta_installed = metaget.check_meta_installed(addon_id)
        else:
            meta_installed = False
                    
        homepage=re.compile('<h1>Recently Added</h1>(.+?)<h1>Statistics</h1>', re.DOTALL).findall(link)
        for scrape in homepage:
                scrapy='<h1>Recently Added</h1>'+scrape+'<h1>Statistics</h1>'
                watnow=re.compile('<h1>Being Watched Now</h1>(.+?)<h1>Statistics</h1>', re.DOTALL).findall(scrapy)
                for scraped in watnow:
                        mirlinks=re.compile('href=/(.+?)>(.+?)</a>').findall(scraped)
                        for url,name in mirlinks:
                                url=iceurl+url
                                name=CLEANUP(name)

                                if check_episode(name):
                                    mode = 14
                                else:
                                    mode = 100
                                                                    
                                if meta_installed and meta_setting=='true':
                                    meta = check_video_meta(name, metaget)
                                    addDir(name,url,mode,'',meta=meta,disablefav=True, disablewatch=True, meta_install=meta_installed)
                                else:
                                    addDir(name,url,mode,'',disablefav=True, disablewatch=True) 
        setView(None, 'default-view')

def SEARCH(url):
    kb = xbmc.Keyboard('', 'Search Icefilms.info', False)
    kb.doModal()
    if (kb.isConfirmed()):
        search = kb.getText()
        if search != '':
            DoEpListSearch(search)
            DoSearch(search)
            
    setView('movies', 'movies-view')
    
                               
def DoSearch(search):        
        finished = False
        nextPage = 0
        results = None
        gs = GoogleSearch('site:http://www.icefilms.info/ip '+search+'')
        gs.results_per_page = 10

        while not finished:
            gs.page = nextPage             
            if (results == None):
                results = gs.get_results()
            else:
                finished = True
                local = gs.get_results()                
                for res in local:
                   if not FindSearchResult(res.title, results):
                       finished = False
                       results.append(res)   
                 
            nextPage = nextPage + 1

            if len(results) == 30:
                finished = True

        find_meta_for_search_results(results, 100)
   

def FindSearchResult(name, results):
        for res in results:
            if res.title == name:
                  return True            
        return False


def DoEpListSearch(search):
        tvurl='http://www.icefilms.info/tv/series'              
        
        # use urllib.quote_plus() on search instead of re.sub ?
        searcher=urllib.quote_plus(search)
        #searcher=re.sub(' ','+',search)
        url='http://www.google.com/search?hl=en&q=site:'+tvurl+'+'+searcher+'&btnG=Search&aq=f&aqi=&aql=&oq='
        link=GetURL(url)
        
        match=re.compile('<h3 class="r"><a href="'+tvurl+'(.+?)"(.+?)">(.+?)</h3>').findall(link)
        match = sorted(match, key=lambda result: result[2])
        find_meta_for_search_results(match, 12, search)


def TVCATEGORIES(url):
        caturl = iceurl+'tv/'        
        setmode = '11'
        addDir('A-Z Directories',caturl+'a-z/1',10,os.path.join(art,'az directories.png'))            
        ADDITIONALCATS(setmode,caturl)
        setView(None, 'default-view')


def MOVIECATEGORIES(url):
        caturl = iceurl+'movies/'        
        setmode = '2'
        addDir('A-Z Directories',caturl+'a-z/1',1,os.path.join(art,'az directories.png'))
        ADDITIONALCATS(setmode,caturl)
        setView(None, 'default-view')


def MUSICCATEGORIES(url):
        caturl = iceurl+'music/'        
        setmode = '2'
        addDir('A-Z List',caturl+'a-z/1',setmode,os.path.join(art,'az lists.png'))
        ADDITIONALCATS(setmode,caturl)
        setView(None, 'default-view')


def STANDUPCATEGORIES(url):
        caturl = iceurl+'standup/'        
        setmode = '2'
        addDir('A-Z List',caturl+'a-z/1',setmode,os.path.join(art,'az lists.png'))
        ADDITIONALCATS(setmode,caturl)
        setView(None, 'default-view')


def OTHERCATEGORIES(url):
        caturl = iceurl+'other/'        
        setmode = '2'
        addDir('A-Z List',caturl+'a-z/1',setmode,os.path.join(art,'az lists.png'))
        ADDITIONALCATS(setmode,caturl)
        setView(None, 'default-view')


def ADDITIONALCATS(setmode,caturl):
        if caturl == iceurl+'movies/':
             addDir('HD 720p',caturl,63,os.path.join(art,'HD 720p.png'))
        PopRatLat(setmode,caturl,'1')
        addDir('Genres',caturl,64,os.path.join(art,'genres.png'))

def PopRatLat(modeset,caturl,genre):
        if caturl == iceurl+'tv/':
             setmode = '11'
        else:
             setmode = '2'
        addDir('Popular',caturl+'popular/'+genre,setmode,os.path.join(art,'popular.png'))
        addDir('Highly Rated',caturl+'rating/'+genre,setmode,os.path.join(art,'highly rated.png'))
        addDir('Latest Releases',caturl+'release/'+genre,setmode,os.path.join(art,'latest releases.png'))
        addDir('Recently Added',caturl+'added/'+genre,setmode,os.path.join(art,'recently added.png'))
        setView(None, 'default-view')


def HD720pCat(url):
        PopRatLat('2',url,'hd')
        setView(None, 'default-view')


def Genres(url):
        addDir('Action',url,70,'')
        addDir('Animation',url,71,'')
        addDir('Comedy',url,72,'')
        addDir('Documentary',url,73,'')
        addDir('Drama',url,74,'')
        addDir('Family',url,75,'')
        addDir('Horror',url,76,'')
        addDir('Romance',url,77,'')
        addDir('Sci-Fi',url,78,'')
        addDir('Thriller',url,79,'')
        setView(None, 'default-view')


def Action(url):
     PopRatLat('2',url,'action')
     setView(None, 'default-view')

def Animation(url):
     PopRatLat('2',url,'animation')
     setView(None, 'default-view')

def Comedy(url):
     PopRatLat('2',url,'comedy')
     setView(None, 'default-view')

def Documentary(url):
     PopRatLat('2',url,'documentary')
     setView(None, 'default-view')

def Drama(url):
     PopRatLat('2',url,'drama')
     setView(None, 'default-view')

def Family(url):
     PopRatLat('2',url,'family')
     setView(None, 'default-view')

def Horror(url):
     PopRatLat('2',url,'horror')
     setView(None, 'default-view')

def Romance(url):
     PopRatLat('2',url,'romance')
     setView(None, 'default-view')

def SciFi(url):
     PopRatLat('2',url,'sci-fi')
     setView(None, 'default-view')

def Thriller(url):
     PopRatLat('2',url,'thriller')
     setView(None, 'default-view')

def MOVIEA2ZDirectories(url):
        setmode = '2'
        caturl = iceurl+'movies/a-z/'
        
        #Generate A-Z list and add directories for all letters.
        A2Z=[chr(i) for i in xrange(ord('A'), ord('Z')+1)]

        #Add number directory
        addDir ('#1234',caturl+'1',setmode,os.path.join(art,'letters','1.png'))
        for theletter in A2Z:
             addDir (theletter,caturl+theletter,setmode,os.path.join(art,'letters',theletter+'.png'))
        setView(None, 'default-view')


def TVA2ZDirectories(url):
        setmode = '11'
        caturl = iceurl+'tv/a-z/'

        #Generate A-Z list and add directories for all letters.
        A2Z=[chr(i) for i in xrange(ord('A'), ord('Z')+1)]

        #Add number directory
        addDir ('#1234',caturl+'1',setmode,os.path.join(art,'letters','1.png'))
        for theletter in A2Z:
            addDir (theletter,caturl+theletter,setmode,os.path.join(art,'letters',theletter+'.png'))
        setView(None, 'default-view')


def MOVIEINDEX(url):
    #Indexer for most things. (Movies,Music,Stand-up etc) 
    
    link=GetURL(url)
    
    # we do this to fix the problem when there is no imdb_id. 
    # I have found only one movie with this problem, but we must check this...
    link = re.sub('<a name=i id=>','<a name=i id=None>',link)
    
    scrape=re.compile('<a name=i id=(.+?)></a><img class=star><a href=/(.+?)>(.+?)<br>').findall(link)
    if scrape:
        getMeta(scrape, 100)
    
    # Enable library mode & set the right view for the content
    setView('movies', 'movies-view')


def TVINDEX(url):
    #Indexer for TV Shows only.

    link=GetURL(url)

    #list scraper now tries to get number of episodes on icefilms for show. this only works in A-Z.
    #match=re.compile('<a name=i id=(.+?)></a><img class=star><a href=/(.+?)>(.+?)</a>').findall(link)
    match=re.compile('<a name=i id=(.+?)></a><img class=star><a href=/(.+?)>(.+?)</a>(.+?)br>').findall(link)
    
    getMeta(match, 12)
    print 'TVindex loader'
    
    # Enable library mode & set the right view for the content
    setView('tvshows', 'tvshows-view')


def TVSEASONS(url, imdb_id):
# displays by seasons. pays attention to settings.

        FlattenSingleSeasons = selfAddon.getSetting('flatten-single-season')
        source=GetURL(url)

        #Save the tv show name for use in special download directories.
        match=re.compile('<h1>(.+?)<a class').findall(source)
        cache.set('tvshowname',match[0])
        r=re.search('(.+?) [(][0-9]{4}[)]',match[0])
        if r:
            showname = r.group(1)
        else:
            showname = match[0]

        # get and save the TV Show poster link
        try:
          imgcheck1 = re.search('<a class=img target=_blank href=', link)
          imgcheck2 = re.search('<iframe src=http://referer.us/f/\?url=', link)
          if imgcheck1 is not None:
               match4=re.compile('<a class=img target=_blank href=(.+?)>').findall(link)
               cache.set('poster',match4[0])
          if imgcheck2 is not None:
               match5=re.compile('<iframe src=http://referer.us/f/\?url=(.+?) width=').findall(link)
               cache.set('poster',match5[0])
        except:
          pass
        
        ep_list = str(BeautifulSoup(source).find("span", { "class" : "list" } ))

        showname = CLEANUP_FOR_META(showname)
        season_list=re.compile('<h3><a name.+?></a>(.+?)<a.+?</a></h3>').findall(ep_list)
        listlength=len(season_list)
        if listlength > 0:
            seasons = str(season_list)
            season_nums = re.compile('Season ([0-9]{1,2}) ').findall(seasons)                        
            
            if meta_setting=='true':
                metaget=metahandlers.MetaData(preparezip=prepare_zip)
                meta_installed = metaget.check_meta_installed(addon_id)
                if meta_installed:
                    season_meta = metaget.get_seasons(showname, imdb_id, season_nums)
            else:
                meta_installed = False
        num = 0
        for seasons in season_list:
            if FlattenSingleSeasons==True and listlength <= 1:             
            
                #proceed straight to adding episodes.
                TVEPISODES(seasons.strip(),source=ep_list,imdb_id=''+str(imdb_id))
            else:
                #save episode page source code
                cache.set('episodesrc',repr(ep_list))
                #add season directories
                if meta_installed and meta_setting=='true' and season_meta:
                    temp = season_meta[num]
                    addDir(seasons.strip(),'',13,temp['cover_url'],imdb=''+str(imdb_id), meta=season_meta[num], totalItems=len(season_list), meta_install=meta_installed) 
                    num = num + 1                     
                else:
                    addDir(seasons.strip(),'',13,'', imdb=''+str(imdb_id), totalItems=len(season_list))
                setView('seasons', 'seasons-view')


def TVEPISODES(name,url=None,source=None,imdb_id=None):
    #Save the season name for use in the special download directories.
    cache.set('mediatvseasonname',name)

    #If source wasn't passed to function, open the file it should be saved to.
    if source is None:
        source = eval(cache.get('episodesrc'))
        
    #special hack to deal with annoying re problems when recieving brackets ( )
    if re.search('\(',name) is not None:
        name = str((re.split('\(+', name))[0])
        #name=str(name[0])
    
    #quick hack of source code to simplfy scraping.
    source=re.sub('</span>','<h3>',source)
    
    #get all the source under season heading.
    #Use .+?/h4> not .+?</h4> for The Daily Show et al to work.
    match=re.compile('<h3><a name="[0-9]+?"></a>'+name+'.+?/h3>(.+?)<h3>').findall(source)
    for seasonSRC in match:
        print "Season Source is " + name
        TVEPLINKS(seasonSRC, name, imdb_id)
    setView('episodes', 'episodes-view')


def TVEPLINKS(source, season, imdb_id):
    
    # displays all episodes in the source it is passed.
    match=re.compile('<img class="star" /><a href="/(.+?)&amp;">(.+?)</a>').findall(source)
        
    if meta_setting=='true':
        #initialise meta class before loop
        metaget=metahandlers.MetaData(preparezip=prepare_zip)
        meta_installed = metaget.check_meta_installed(addon_id)
    else:
        metaget=False
        meta_installed=False
    for url,name in match:
            print " TVepLinks name " + name           
            get_episode(season, name, imdb_id, url, metaget, meta_installed, totalitems=len(match)) 
    
    # Enable library mode & set the right view for the content
    setView('episodes', 'episodes-view')
             
def LOADMIRRORS(url):
     # This proceeds from the file page to the separate frame where the mirrors can be found,
     # then executes code to scrape the mirrors

     link=GetURL(url)  
     
     #---------------Begin phantom metadata getting--------

     #Save metadata on page to files, for use when playing.
     # Also used for creating the download directory structures.

     # get and save videoname     
     namematch=re.compile('''<span style="font-size:large;color:white;">(.+?)</span>''').findall(link)
     if not namematch:
         Notify('big','Error Loading Sources','An error occured loading sources.\nCheck your connection and/or the Icefilms site.','')
         callEndOfDirectory = False
         return
     
     try:
         cache.set('videoname',namematch[0])
     except:
         pass

     # get and save description
     match2=re.compile('<th>Description:</th><td>(.+?)<').findall(link)
     try:
          cache.set('description',match2[0])
     except:
          pass
     
     # get and save poster link
     try:
          imgcheck1 = re.search('<img width=250 src=', link)
          imgcheck2 = re.search('<iframe src=/noref.php\?url=', link)
          if imgcheck1 is not None:
               match4=re.compile('<img width=250 src=(.+?) style').findall(link)
               cache.set('poster',match4[0])
          if imgcheck2 is not None:
               match5=re.compile('<iframe src=/noref.php\?url=(.+?) width=').findall(link)
               cache.set('poster',match5[0])
     except:
          pass

     #get and save mpaa     
     mpaacheck = re.search('MPAA Rating:', link)         
     if mpaacheck is not None:     
          match4=re.compile('<th>MPAA Rating:</th><td>(.+?)</td>').findall(link)
          mpaa=re.sub('Rated ','',match4[0])
          try:
               cache.set('mpaa',mpaa)
          except:
               pass


     ########### get and save potential file path. This is for use in download function later on.
     epcheck1 = re.search('Episodes</a>', link)
     epcheck2 = re.search('Episode</a>', link)
     if epcheck1 is not None or epcheck2 is not None:
          if cache.get('mediatvshowname'):
               #open media file if it exists, as that has show name with date.
               showname=cache.get('mediatvshowname')
          else:
               #fall back to scraping show name without date from the page.
               print 'USING FALLBACK SHOW NAME'
               fallbackshowname=re.compile("alt\='Show series\: (.+?)'").findall(link)
               showname=fallbackshowname[0]
          try:
               #if season name file exists
               if cache.get('mediatvshowname'):
                    seasonname=cache.get('mediatvshowname')
                    cache.set('mediapath','TV Shows/'+showname+'/'+seasonname)
               else:
                    cache.set('mediapath','TV Shows/'+showname)
          except:
               print "FAILED TO SAVE TV SHOW FILE PATH!"
     else:
          
          try:
              cache.set('mediapath','Movies/'+namematch[0])
          except:
              pass

     #---------------End phantom metadata getting stuff --------------

     match=re.compile('/membersonly/components/com_iceplayer/(.+?img=).*?" width=').findall(link)
     match[0]=re.sub('%29',')',match[0])
     match[0]=re.sub('%28','(',match[0])
     for url in match:
          mirrorpageurl = iceurl+'membersonly/components/com_iceplayer/'+url
      
     mirror_page=GetURL(mirrorpageurl, save_cookie = True)

     # check for recaptcha
     has_recaptcha = check_for_captcha(mirror_page)

     if has_recaptcha is False:
          GETMIRRORS(mirrorpageurl,mirror_page)
     elif has_recaptcha is True:
          RECAPTCHA(mirrorpageurl)
     setView(None, 'default-view')


def check_for_captcha(source):
     #check for recaptcha in the page source, and return true or false.
     has_recaptcha = re.search('recaptcha_challenge_field', source)

     if has_recaptcha is None:
          return False
     else:
          return True

def RECAPTCHA(url):
     print 'initiating recaptcha passthrough'
     source = GetURL(url)
     match = re.compile('<iframe src="http://www.google.com/recaptcha/api/noscript\?k\=(.+?)" height').findall(source)

     for token in match:
          surl = 'http://www.google.com/recaptcha/api/challenge?k=' + token
     tokenlink=GetURL(surl)
     matchy=re.compile("challenge : '(.+?)'").findall(tokenlink)
     for challenge in matchy:
          imageurl='http://www.google.com/recaptcha/api/image?c='+challenge

     #hacky method --- save all captcha details and mirrorpageurl to file, to reopen in next step
     cache.set('captcha', challenge)
     cache.set('pageurl', url)

     #addDir uses imageurl as url, to avoid xbmc displaying old cached image as the fresh captcha
     addDir('Enter Captcha - Type the letters',imageurl,99,imageurl)

def CAPTCHAENTER(surl):
     url=cache.get('pageurl')
     kb = xbmc.Keyboard('', 'Type the letters in the captcha image', False)
     kb.doModal()
     if (kb.isConfirmed()):
          userInput = kb.getText()
          if userInput != '':
               challengeToken=cache.get('captcha')
               print 'challenge token: '+challengeToken
               parameters = urllib.urlencode({'recaptcha_challenge_field': challengeToken, 'recaptcha_response_field': userInput})
               source = GetURL(url, parameters)
               has_recaptcha = check_for_captcha(source)
               if has_recaptcha:
                    Notify('big', 'Text does not match captcha image!', 'To try again, close this box and then: \n Press backspace twice, and reselect your video.', '')
               else:
                    GETMIRRORS(url,source)
          elif userInput == '':
               Notify('big', 'No text entered!', 'To try again, close this box and then: \n Press backspace twice, and reselect your video.', '')               

def GETMIRRORS(url,link):
# This scrapes the megaupload mirrors from the separate url used for the video frame.
# It also displays them in an informative fashion to user.
# Displays in three directory levels: HD / DVDRip etc , Source, PART
    print "getting mirrors for: %s" % url
        
    #hacky method -- save page source to cache
    cache.set('mirror', link)
    
    #check for the existence of categories, and set values.
    if re.search('<div class=ripdiv><b>DVDRip / Standard Def</b>', link) is not None: dvdrip = 1
    else: dvdrip = 0
    
    if re.search('<div class=ripdiv><b>HD 720p</b>', link) is not None: hd720p = 1
    else: hd720p = 0
    
    if re.search('<div class=ripdiv><b>DVD Screener</b>', link) is not None: dvdscreener = 1
    else: dvdscreener = 0
    
    if re.search('<div class=ripdiv><b>R5/R6 DVDRip</b>', link) is not None: r5r6 = 1
    else: r5r6 = 0
    
    FlattenSrcType = selfAddon.getSetting('flatten-source-type')        
     
    # Search if there is a local version of the file
    #get proper name of vid
    #vidname=handle_file('videoname','open')
    #mypath=Get_Path(name,vidname)
    #if mypath != 'path not set':
    #    if os.path.isfile(mypath) is True:
    #        localpic=handle_file('localpic','')
    #        addExecute('Source    | Local | Full',mypath,205,localpic)
    
    #only detect and proceed directly to adding sources if flatten sources setting is true
    if FlattenSrcType == 'true':
    
         #add up total number of categories.
         total = dvdrip + hd720p + dvdscreener + r5r6
    
         #if there is only one category, skip to adding sources.
         if total == 1:
              if dvdrip == 1:
                   DVDRip(url)
              elif hd720p == 1:
                   HD720p(url)
              elif dvdscreener == 1:
                   DVDScreener(url)
              elif r5r6 == 1:
                   R5R6(url)
    
         #if there are multiple categories, add sub directories.
         elif total > 1:
              addCatDir(url,dvdrip,hd720p,dvdscreener,r5r6)
    
    #if flattensources is set to false, don't flatten                
    elif FlattenSrcType == 'false':
         addCatDir(url,dvdrip,hd720p,dvdscreener,r5r6)

                
def addCatDir(url,dvdrip,hd720p,dvdscreener,r5r6):
       
        if dvdrip == 1:
                addDir('DVDRip',url,101,os.path.join(art,'source_types','dvd.png'), imdb=imdbnum)
        if hd720p == 1:
                addDir('HD 720p',url,102,os.path.join(art,'source_types','hd720p.png'), imdb=imdbnum)
        if dvdscreener == 1:
                addDir('DVD Screener',url,103,os.path.join(art,'source_types','dvdscreener.png'), imdb=imdbnum)
        if r5r6 == 1:
                addDir('R5/R6 DVDRip',url,104,os.path.join(art,'source_types','r5r6.png'), imdb=imdbnum)


def PART(scrap,sourcenumber,args,cookie,megapic,shared2pic):
     #check if source exists
     sourcestring='Source #'+sourcenumber
     checkforsource = re.search(sourcestring, scrap)
     
     #if source exists proceed.
     if checkforsource is not None:
          
          #check if source contains multiple parts
          multiple_part = re.search('<p>Source #'+sourcenumber+':', scrap)
          
          if multiple_part is not None:
               print sourcestring+' has multiple parts'
               #get all text under source if it has multiple parts
               multi_part_source=re.compile('<p>Source #'+sourcenumber+': (.+?)PART 1(.+?)</i><p>').findall(scrap)

               #put scrape back together
               for sourcescrape1,sourcescrape2 in multi_part_source:
                    scrape=sourcescrape1+'PART 1'+sourcescrape2
                    pair = re.compile("onclick='go\((\d+)\)'>PART\s+(\d+)").findall(scrape)
                    for id, partnum in pair:
                        url = GetSource(id, args, cookie)
                        # check if source is megaupload or 2shared, and add all parts as links
                        ismega = re.search('\.megaupload\.com/', url)
                        is2shared = re.search('\.2shared\.com/', url)

                        if ismega is not None:
                              partname='Part '+partnum
                              fullname=sourcestring+' | MU | '+partname
                              try:
                                  sources = eval(cache.get("source"+str(sourcenumber)+"parts"))
                              except:
                                  sources = {partnum: url}
                                  print 'sources havent been set yet...'  
                              sources[partnum] = url                          
                              cache.set("source"+str(sourcenumber)+"parts", repr(sources))
                              if selfAddon.getSetting('stack-multi-part') == 'true' and partnum == '1':
                                  name = fullname.replace('Part 1', 'Multiple Parts')
                                  addExecute(name,url,199,megapic)
                              elif selfAddon.getSetting('stack-multi-part') == 'false':
                                  addExecute(fullname,url,get_default_action(),megapic)
                        elif is2shared is not None:
                             #print sourcestring+' is hosted by 2shared' 
                             part=re.compile('&url=http://www.2shared.com/(.+?)>PART (.+?)</a>').findall(scrape)
                             for url,name in part:
                                  fullurl='http://www.2shared.com/'+url
                                  partname='Part '+name
                                  fullname=sourcestring+' | 2S  | '+partname
                                  addExecute(fullname,url,get_default_action(),shared2pic)

          # if source does not have multiple parts...
          elif multiple_part is None:
               # print sourcestring+' is single part'
               # find corresponding '<a rel=?' entry and add as a one-link source
               source5=re.compile('<a\s+rel='+sourcenumber+'.+?onclick=\'go\((\d+)\)\'>Source\s+#'+sourcenumber+':').findall(scrap)
               # print source5
               for id in source5:
                    url = GetSource(id, args, cookie)
                    ismega = re.search('\.megaupload\.com/', url)
                    is2shared = re.search('\.2shared\.com/', url)
                    if ismega is not None:
                         # print 'Source #'+sourcenumber+' is hosted by megaupload'
                         fullname=sourcestring+' | MU | Full'
                         addExecute(fullname,url,get_default_action(),megapic)
                    elif is2shared is not None:
                         #print 'Source #'+sourcenumber+' is hosted by 2shared' 
                         fullname=sourcestring+' | 2S  | Full'
                         addExecute(fullname,url,200,shared2pic)


def GetSource(id, args, cookie):
    m = random.randrange(100, 300) * -1
    s = random.randrange(5, 50)
    params = copy.copy(args)
    params['id'] = id
    params['m'] = m
    params['s'] = s
    paramsenc = urllib.urlencode(params)
    body = GetURL(ICEFILMS_AJAX, params = paramsenc, cookie = cookie)
    print 'response: %s' % body
    source = re.search('url=(http[^&]+)', body)
    if source:
        url = urllib.unquote(source.group(1))
    else:
        print 'GetSource - URL String not found'
        url = ''
    print 'url: %s' % url
    return url


def SOURCE(page, sources):
          # Delete old source parts
          cache.delete('source%')

          # get settings
          megapic=handle_file('megapic','')
          shared2pic=handle_file('shared2pic','')

          # extract the ingredients used to generate the XHR request
          #
          # set here:
          #
          #     iqs: not used?
          #     url: not used?
          #     cap: form field for recaptcha? - always set to empty in the JS
          #     sec: secret identifier: hardwired in the JS
          #     t:   token: hardwired in the JS
          #
          # set in GetSource:
          #
          #     m:   starts at 0, decremented each time a mousemove event is fired e.g. -123
          #     s:   seconds since page loaded (> 5, < 250)
          #     id:  source ID in the link's onclick attribute (extracted in PART)

          args = {
              'iqs': '',
              'url': '',
              'cap': ''
          }

          sec = re.search("f\.lastChild\.value=\"([^']+)\",a", page).group(1)
          t = re.search('"&t=([^"]+)",', page).group(1)

          args['sec'] = sec
          args['t'] = t
          
          cookie = re.search('<cookie>(.+?)</cookie>', page).group(1)
          print "saved cookie: %s" % cookie

          #add cached source
          vidname=cache.get('videoname')
          dlDir = Get_Path("noext","")
    
          listitem=Item_Meta(vidname)

          try:
              for fname in os.listdir(dlDir):
                  match = re.match(re.escape(vidname)+' *(.*)\.avi$', fname)
                  if match is not None:
                      if os.path.exists(os.path.join(dlDir,fname)+'.dling'):
                          listitem.setLabel("Play Downloading "+match.group(0))
                          addDownloadControls(match.group(0),os.path.join(dlDir,fname), listitem)
                      else:
                          listitem.setLabel("Play Local File" + match.group(0))
                          addLocal("Play Local File " + match.group(0), os.path.join(dlDir,fname), listitem)
          except:
              pass

          # create a list of numbers: 1-21
          num = 1
          numlist = list('1')
          while num < 21:
              num = num+1
              numlist.append(str(num))

          #for every number, run PART.
          #The first thing PART does is check whether that number source exists...
          #...so it's not as CPU intensive as you might think.

          for thenumber in numlist:
               PART(sources,thenumber,args,cookie,megapic,shared2pic)
          setView(None, 'default-view')

def DVDRip(url):
        link=cache.get('mirror')
#string for all text under standard def border
        defcat=re.compile('<div class=ripdiv><b>DVDRip / Standard Def</b>(.+?)</div>').findall(link)
        for scrape in defcat:
                SOURCE(link, scrape)
        setView(None, 'default-view')

def HD720p(url):
        link=cache.get('mirror')
#string for all text under hd720p border
        defcat=re.compile('<div class=ripdiv><b>HD 720p</b>(.+?)</div>').findall(link)
        for scrape in defcat:
                SOURCE(link, scrape)
        setView(None, 'default-view')

def DVDScreener(url):
        link=cache.get('mirror')
#string for all text under dvd screener border
        defcat=re.compile('<div class=ripdiv><b>DVD Screener</b>(.+?)</div>').findall(link)
        for scrape in defcat:
                SOURCE(link, scrape)
        setView(None, 'default-view')
        
def R5R6(url):
        link=cache.get('mirror')
#string for all text under r5/r6 border
        defcat=re.compile('<div class=ripdiv><b>R5/R6 DVDRip</b>(.+?)</div>').findall(link)
        for scrape in defcat:
                SOURCE(link, scrape)
        setView(None, 'default-view')
        
class TwoSharedDownloader:
     
     def __init__(self):
          self.cookieString = ""
          self.re2sUrl = re.compile('(?<=window.location \=\')([^\']+)')
     
     def returnLink(self, pageUrl):

          # Open the 2Shared page and read its source to htmlSource
          request = urllib2.Request(pageUrl)
          response = urllib2.urlopen(request)
          htmlSource = response.read()
     
          # Search the source for link to the video and store it for later use
          match = re.compile('">(.+?)</div>').findall(htmlSource)
          fileUrl = match[0]
          
          # Return the valid link
          return fileUrl 
     

     
          
def SHARED2_HANDLER(url):
          downloader2Shared = TwoSharedDownloader()
          vidFile = downloader2Shared.returnLink(url)

          print '2Shared Direct Link: '+vidFile
          finalUrl = [1]
          finalUrl[0] = vidFile
          return finalUrl


def GetURL(url, params = None, referrer = ICEFILMS_REFERRER, cookie = None, save_cookie = False):
     print 'GetUrl: ' + url
     print 'params: ' + repr(params)
     print 'referrer: ' + repr(referrer)
     print 'cookie: ' + repr(cookie)
     print 'save_cookie: ' + repr(save_cookie)

     if params:
        req = urllib2.Request(url, params)
        # req.add_header('Content-type', 'application/x-www-form-urlencoded')
     else:
         req = urllib2.Request(url)

     req.add_header('User-Agent', USER_AGENT)

     # as of 2011-06-02, IceFilms sources aren't displayed unless a valid referrer header is supplied:
     # http://forum.xbmc.org/showpost.php?p=810288&postcount=1146
     if referrer:
         req.add_header('Referer', referrer)

     if cookie:
         req.add_header('Cookie', cookie)

     # avoid Python >= 2.5 ternary operator for backwards compatibility
     # http://wiki.xbmc.org/index.php?title=Python_Development#Version
     try:
         response = urllib2.urlopen(req)
         body = response.read()

         if save_cookie:
             setcookie = response.info().get('Set-Cookie', None)
             print "Set-Cookie: %s" % repr(setcookie)
             if setcookie:
                 setcookie = re.search('([^=]+=[^=;]+)', setcookie).group(1)
                 body = body + '<cookie>' + setcookie + '</cookie>'
    
         response.close()

     except Exception, e:
         print '****** ERROR: %s' % e
         Notify('big','Error Requesting Site','An error has occured communicating with Icefilms', '', '', 'Check your connection and the Icefilms site.' )
         body = ''
         pass

     return body

def WaitIf():
     #killing playback is necessary if switching playing of one megaup/2share stream to another
     if xbmc.Player().isPlayingVideo() == True:
               #currentvid=xbmc.Player().getPlayingFile()
               #isice = re.search('.megaupload', currentvid)
                xbmc.Player().stop()


#Quick helper function used to strip characters that are invalid for Windows filenames/folders
def Clean_Windows_String(string):
     return re.sub('[^-a-zA-Z0-9_.()\\\/ ]+', '',  string)


def Get_Path(srcname,vidname):
     ##Gets the path the file will be downloaded to, and if necessary makes the folders##
         
     #clean video name of unwanted characters
     vidname = Clean_Windows_String(vidname)
    
     if os.path.exists(downloadPath):

          #if source is split into parts, attach part number to the videoname.
          if re.search('Part',srcname) is not None and selfAddon.getSetting('stack-multi-part') == 'false':
               srcname=(re.split('\|+', srcname))[-1]
               vidname=vidname + ' part' + ((re.split('\ +', srcname))[-1])
               #add file extension
               vidname = vidname+'.avi'
          elif selfAddon.getSetting('stack-multi-part') == 'true':
               vidname=vidname + ' part 1'
          elif srcname is not "noext":
               #add file extension
               vidname = vidname+'.avi'

          #initial_path=os.path.join(downloadPath,'Icefilms Downloaded Videos')

          #is use special directory structure set to true?
          SpecialDirs=selfAddon.getSetting('use-special-structure')

          if SpecialDirs == 'true':
               mediapath=Clean_Windows_String(os.path.normpath(cache.get('mediapath')))
               mediapath=os.path.join(downloadPath,mediapath)              
               
               if not os.path.exists(mediapath):
                    try:
                        os.makedirs(mediapath)
                    except Exception, e:
                        print 'Failed to create media path: %s' % mediapath
                        print 'With error: %s' % e
                        pass
               finalpath=os.path.join(mediapath,vidname)
               return finalpath
     
          elif SpecialDirs == 'false':
               mypath=os.path.join(downloadPath,vidname)
               return mypath
     else:
          return 'path not set'


def Item_Meta(name):
          #set metadata, for selected source. this is done from 'phantom meta'.
          # ie, meta saved earlier when we loaded the mirror page.
          # very important that things are contained within try blocks, because streaming will fail if something in this function fails.

          #set name and description, unicode cleaned.
          try: open_vidname=cache.get('videoname')
          except:
               vidname = ''
               print 'OPENING VIDNAME FAILED!'
          else:
               try: get_vidname = htmlcleaner.clean(open_vidname)
               except:
                    print 'CLEANING VIDNAME FAILED! :',open_vidname
                    vidname = open_vidname
               else: vidname = get_vidname

          try: open_desc=cache.get('description')
          except:
               description = ''
               print 'OPENING DESCRIPTION FAILED!'
          else:
               try: get_desc = htmlcleaner.clean(open_desc)
               except:
                    print 'CLEANING DESCRIPTION FAILED! :',open_desc
                    description = open_desc
               else: description = get_desc
          
          #set other metadata strings from strings saved earlier
          try: get_poster=cache.get('poster')
          except: poster = ''
          else: poster = get_poster

          try: get_mpaa=cache.get('mpaa')
          except: mpaa = None
          else: mpaa = get_mpaa
          
          #srcname=handle_file('sourcename','open')
          srcname=name

          listitem = xbmcgui.ListItem(srcname)
          if not mpaa:
               listitem.setInfo('video', {'Title': vidname, 'plotoutline': description, 'plot': description})
          if mpaa:
               listitem.setInfo('video', {'Title': vidname, 'plotoutline': description, 'plot': description, 'mpaa': mpaa})
          listitem.setThumbnailImage(poster)

          return listitem


def do_wait(account, wait_time, quiet=False):
     # do the necessary wait, with  a nice notice and pre-set waiting time. I have found the below waiting times to never fail.
     if quiet == True:
         xbmc.sleep(wait_time*1000)     
         return True
     else:
         if account == 'platinum':    
              return handle_wait(int(wait_time),'Megaupload','Loading video with your *Platinum* account.')
                   
         elif account == 'premium':    
              return handle_wait(int(wait_time),'Megaupload','Loading video with your *Premium* account.')
                 
         elif account == 'free':
              return handle_wait(int(wait_time),'Megaupload Free User','Loading video with your free account.')

         else:
              return handle_wait(int(wait_time),'Megaupload','Loading video.')


def handle_wait(time_to_wait,title,text):

    print 'waiting '+str(time_to_wait)+' secs'    

    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create(' '+title)

    secs=0
    percent=0
    increment = float(100) / time_to_wait
    increment = int(round(increment))

    cancelled = False
    while secs < time_to_wait:
        secs = secs + 1
        percent = increment*secs
        secs_left = str((time_to_wait - secs))
        remaining_display = ' Wait '+secs_left+' seconds for the video stream to activate...'
        pDialog.update(percent,' '+ text, remaining_display)
        xbmc.sleep(1000)
        if (pDialog.iscanceled()):
             cancelled = True
             break
    if cancelled == True:     
         print 'wait cancelled'
         return False
    else:
         print 'done waiting'
         return True

def Handle_Vidlink(url, wait=True):
     #video link preflight, pays attention to settings / checks if url is mega or 2shared
     ismega = re.search('\.megaupload\.com/', url)
     is2shared = re.search('\.2shared\.com/', url)
     
     if ismega is not None:
          if wait == True:
               WaitIf()
          
          mu = megaroutines.megaupload(translatedicedatapath)
          link = mu.resolve_megaup(url)

          finished = do_wait(link[3], link[4], True)


          if finished == True:
               return link
          else:
               return None

     elif is2shared is not None:
          #Notify('big','2Shared','2Shared is not supported by this addon. (Yet)','')
          #return False
          shared2url=SHARED2_HANDLER(url)
          return shared2url


def PlayFile(name,url):
    
    listitem=Item_Meta(name)
    print 'attempting to play local file'
    try:
        #directly call xbmc player (provides more options)
        play_with_watched(url, listitem, '')
        
        #xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play( url, listitem )
    except:
        print 'local file playing failed'


def Stream_Source(name,url):
    
    callEndOfDirectory = False
    
    vidname=cache.get('videoname')
    mypath = Get_Path(name,vidname)
    listitem = Item_Meta(name)

    video_seeking = selfAddon.getSetting('video-seeking')

    stack_multi = selfAddon.getSetting('stack-multi-parts')
    play_action = selfAddon.getSetting('play-action')
    #Play File normal as a stream
    if video_seeking == 'false' and play_action == '0':
        try:
            link = Handle_Vidlink(url)
        except Exception, e:
            print '**** Stream error: %s' % e
            Notify('big','Invalid Source','Unable to play selected source. \n Please try another.','')
            return
    
        if link:
            play_with_watched(link[0], listitem, mypath)
    
    elif stack_multi == 'true' and play_action == '2':
        Download_And_Play_With_Parts(name,url,video_seek=False)
    #Download file in a separate thread then play - delete file when done
    else:
        Download_And_Play(name,url, video_seek=True)
        CancelDownload(name, video_seek=True)


def play_with_watched(url, listitem, mypath):
    global currentTime
    global totalTime
    global watched_percent
    global finalPart
    
    finalPart = 1
    watched_percent = get_watched_percent()    

    mplayer = MyPlayer()
    mplayer.play(url, listitem)

    try:
        totalTime = mplayer.getTotalTime()
    except Exception:
        xbmc.sleep(20000) #wait 20 seconds until the video is playing before getting totalTime
        try:
            totalTime = mplayer.getTotalTime()
        except Exception:
            return
    while(1):
        try:
            currentTime= mplayer.getTime()
        except Exception:
            print 'XBMC is not currently playing a media file'
            break
        xbmc.sleep(1000)
        

def get_watched_percent():
     watched_values = [.5, .6, .7, .8, .9]
     return watched_values[int(selfAddon.getSetting('watched-percent'))]


def Stream_Source_with_parts(name,url):
    global currentTime
    global totalTime
    global watched_percent
    global finalPart
    #Find which source
    sourcenumber = name[8:9]
    #print 'this is the sourcenum %s from name %s' % (sourcenumber, name)
    source = eval(cache.get("source"+str(sourcenumber)+"parts"))

    watched_percent = get_watched_percent()
    link=Handle_Vidlink(source['1'])
    listitem=Item_Meta(name)
    print '--- Attempting to stream file: ' + str(link) + ' from url: ' + str(url)
     
    mplayer = MyPlayer()
    mplayer.play(link[0], listitem)

    index = 2
    
    # first part is playing... now wait to start 2nd part
    while finalPart != 1:
        #Set the currentTime and totalTime to arbitrary numbers. This keeps it from pre-maturely starting the 3rd part immediately after the 2nd part starts
        # using currentTime and totalTime from the first part.
        currentTime = 0
        totalTime = 20
        try:
            #Try to get the totalTime and currentTime from the player... If there is an exception and nothing is retrieved set it back to 20 to avoid moving
            # on to the next part.
            totalTime = mplayer.getTotalTime()
            if totalTime == 0:
                totalTime = 20
            currentTime= mplayer.getTime()
        except Exception:
            print 'XBMC is not currently playing a media file'
        #start next part
        #When the current part has less than 3 seconds remaining get ready to start next part.
        if currentTime > totalTime-3:
            xbmc.sleep(4000)
            #Check the part list to see if there are parts remaining
            if source[str(index)]:
                link2=Handle_Vidlink(source[str(index)])
                listitem=Item_Meta(name)
                try:
                    nextPart = source[str(index+1)]
                except:
                    print 'Attempting to stream the final part: %s' % str(link2)
                    finalPart = 1
                    pass
                mplayer = MyPlayer()
                mplayer.play(link2[0], listitem)
                index+=1
        xbmc.sleep(500) 


class MyPlayer (xbmc.Player):
     def __init__ (self):
        self.dialog = None
        xbmc.Player.__init__(self)
        
        print 'Initializing myPlayer...'
        
     def play(self, url, listitem):
        print 'Now im playing... '+url

        xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(url, listitem)            
        
     def isplaying(self):
        xbmc.Player.isPlaying(self)

     def onPlayBackEnded(self):
        global currentTime
        global totalTime
        global finalPart
        if finalPart == 1:
            percentWatched = currentTime / totalTime
            print 'current time: ' + str(currentTime) + ' total time: ' + str(totalTime) + ' percent watched: ' + str(percentWatched)
            if percentWatched >= watched_percent:
                #set watched
                vidname=cache.get('videoname')
                video = get_video_name(vidname)
                print 'Auto-Watch - Setting %s to watched' % video
                ChangeWatched(imdbnum, video_type, video['name'], season_num, episode_num, video['year'], watched=7)

     def onPlayBackStopped(self):
        global currentTime
        global totalTime
        global finalPart
        if finalPart == 1:
            percentWatched = currentTime / totalTime
            print 'current time: ' + str(currentTime) + ' total time: ' + str(totalTime) + ' percent watched: ' + str(percentWatched)
            if percentWatched >= watched_percent and totalTime > 1:
                #set watched
                vidname=cache.get('videoname')
                video = get_video_name(vidname)
                print 'Auto-Watch - Setting %s to watched' % video            
                ChangeWatched(imdbnum, video_type, video['name'], season_num, episode_num, video['year'], watched=7)

############## End MyPlayer Class ################


class DownloadThread (threading.Thread):
    def __init__(self, url, dest, vidname=False):
        self.url = url
        self.dest = dest
        self.vidname = vidname
        self.dialog = None
        
        threading.Thread.__init__(self)
        
    def run(self):
        #save the thread id to a .tid file. This file can then be read if the user navigates away from the 
        #download info page to get the thread ID again and generate the download info links
        #the tid file will also denote a download in progress
        #Note: if xbmc is killed during a download, the tid file will remain, therefore:
        #TODO: add remove incomplete download link
        
        save(self.dest + '.dling', 'dling')

        #get settings
        save(os.path.join(downloadPath,'Downloading'),self.dest+'\n'+self.vidname)
          
        delete_incomplete = selfAddon.getSetting('delete-incomplete-downloads')
        
        start_time = time.time() 
        try: 
            urllib.urlretrieve(self.url, self.dest, lambda nb, bs, fs: _dlhook(nb, bs, fs, self, start_time))
            if os.path.getsize(self.dest) < 10000:
                print 'Got a very small file'
                raise SmallFile('Small File')
            if self.dialog <> None:
                self.dialog.close()
                self.dialog = None
                print 'Download finished successfully'
            try:
              os.remove(self.dest + '.dling')
            except:
              pass
            os.remove(os.path.join(downloadPath,'Downloading'))
        
        except:
            if self.dialog <> None:
                self.dialog.close()
                self.dialog = None
                
            print 'Download interrupted'
            os.remove(os.path.join(downloadPath,'Downloading'))
            
            #download is killed so remove .dling file
            try:
                os.remove(self.dest + '.dling')
            except:
                pass
            
            if delete_incomplete == 'true':
                #delete partially downloaded file if setting says to.
                while os.path.exists(self.dest):
                    try:
                        os.remove(self.dest)
                        break
                    except:
                        pass
            
            if sys.exc_info()[0] in (StopDownloading,):
                Notify('big','Download Canceled','Download has been canceled','')
            else:
                raise 


    def show_dialog(self):
        self.dialog = xbmcgui.DialogProgress()
        self.dialog.create('Downloading', '', self.vidname)
    
    def hide_dialog(self):
        self.dialog.close() 
        self.dialog = None

############## End DownloadThread Class ################

class StopDownloading(Exception): 
        def __init__(self, value): 
            self.value = value 
        def __str__(self): 
            return repr(self.value)

class SmallFile(Exception): 
        def __init__(self, value): 
            self.value = value 
        def __str__(self): 
            return repr(self.value)

def Download_And_Play(name,url, video_seek=False):

    #get proper name of vid                                                                                                           
    vidname=cache.get('videoname')

    mypath=Get_Path(name,vidname)
     
    print 'MYPATH: ',mypath
    if mypath == 'path not set':
        Notify('Download Alert','You have not set the download folder.\n Please access the addon settings and set it.','','')
        return

    if os.path.exists(os.path.join(downloadPath, 'Ping')):
        os.remove(os.path.join(downloadPath, 'Ping'))
    if os.path.exists(os.path.join(downloadPath, 'Alive')):
        os.remove(os.path.join(downloadPath, 'Alive'))

    if os.path.exists(os.path.join(downloadPath, 'Downloading')):
      fhPing = open(os.path.join(downloadPath, 'Ping'), 'w')
      fhPing.close()
      xbmc.sleep(1000)
      
      if os.path.exists(os.path.join(downloadPath, 'Alive')):
          fh = open(os.path.join(downloadPath, 'Alive'))          
          filePathAlive = fh.readline().strip('\n')
          fileNameAlive = fh.readline().strip('\n')
          fh.close()
          
          try:
              os.remove(os.path.join(downloadPath, 'Alive'))
          except:
              pass
          
          Notify('Download Alert','Currently downloading '+fileNameAlive,'','')
          addDownloadControls(fileNameAlive, filePathAlive)
          return

      else:
          os.remove(os.path.join(downloadPath, 'Ping'))
          delete_incomplete = selfAddon.getSetting('delete-incomplete-downloads')
          
          if delete_incomplete == 'true':
              if os.path.exists(os.path.join(downloadPath, 'Downloading')):
                  fh = open(os.path.join(downloadPath, 'Downloading'))          
                  filePathDownloading = fh.readline().strip('\n')
                  fh.close()
                  
                  try:
                      os.remove(filePathDownloading)
                  except:
                      pass
                  try:
                      os.remove(filePathDownloading + '.dling')
                  except:
                      pass

          if os.path.exists(os.path.join(downloadPath, 'Downloading')):
              os.remove(os.path.join(downloadPath, 'Downloading'))


    if os.path.isfile(mypath) is True:
        if os.path.isfile(mypath + '.dling'):
            try:
                os.remove(mypath)
                os.remove(mypath + '.dling')
            except:
                print 'download failed: existing incomplete files cannot be removed'
                return
        else:
            Notify('Download Alert','The video you are trying to download already exists!','','')

    try: 
        link=Handle_Vidlink(url)
    except:
        Notify('big','Invalid Source','Unable to play selected source. \n Please try another.','') 
        callEndOfDirectory = False
        return
    if link == None:
        callEndOfDirectory = False
        return

    print 'attempting to download and play file'

    try:
        print "Starting Download Thread"
        dlThread = DownloadThread(link[0], mypath, vidname)
        dlThread.start()
        buffer_delay = int(selfAddon.getSetting('buffer-delay'))
        handle_wait(buffer_delay, "Buffering", "Waiting a bit before playing...")
        if os.path.exists(mypath):
            if dlThread.isAlive():
                listitem=Item_Meta(name)
                              
                play_with_watched(mypath, listitem, '')
                
                if video_seek:
                    if os.path.exists(mypath):
                        try:
                            os.remove(mypath)
                        except:
                            print 'Failed to delete file after video seeking'
                else:
                    addDownloadControls(name,mypath, listitem)
            else:
                raise
        else:
            raise
    except Exception, e:
        print 'EXCEPTION %s' % e
        if sys.exc_info()[0] in (urllib.ContentTooShortError,): 
            Notify('big','Download and Play failed!','Error: Content Too Short','')
        if sys.exc_info()[0] in (OSError,): 
            Notify('big','Download and Play failed!','Error: Cannot write file to disk','')
        if sys.exc_info()[0] in (SmallFile,): 
            Notify('big','Download and Play failed!','Error: Got a file smaller than 10KB','')

def Download_And_Play_With_Parts(name,url, video_seek=False):
    
    #Clear the video playlist 
    playList = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    playList.clear()

    #Find which source
    sourcenumber = name[8:9]
    source = eval(cache.get("source"+str(sourcenumber)+"parts"))
    print 'This is the number of parts %s' % len(source)

    #get proper name of vid                                                                                                           
    vidname=cache.get('videoname')
    print 'this is the vidname returned %s' % vidname

    mypath=Get_Path(name,vidname)
    vidname = vidname + ' Part 1'
     
    print 'MYPATH: ',mypath
    if mypath == 'path not set':
        Notify('Download Alert','You have not set the download folder.\n Please access the addon settings and set it.','','')
        return

    if os.path.exists(os.path.join(downloadPath, 'Ping')):
        os.remove(os.path.join(downloadPath, 'Ping'))
    if os.path.exists(os.path.join(downloadPath, 'Alive')):
        os.remove(os.path.join(downloadPath, 'Alive'))

    if os.path.exists(os.path.join(downloadPath, 'Downloading')):
      fhPing = open(os.path.join(downloadPath, 'Ping'), 'w')
      fhPing.close()
      xbmc.sleep(1000)
      
      if os.path.exists(os.path.join(downloadPath, 'Alive')):
          fh = open(os.path.join(downloadPath, 'Alive'))          
          filePathAlive = fh.readline().strip('\n')
          fileNameAlive = fh.readline().strip('\n')
          fh.close()
          
          try:
              os.remove(os.path.join(downloadPath, 'Alive'))
          except:
              pass
          
          Notify('Download Alert','Currently downloading '+fileNameAlive,'','')
          addDownloadControls(fileNameAlive, filePathAlive)
          return

      else:
          os.remove(os.path.join(downloadPath, 'Ping'))
          delete_incomplete = selfAddon.getSetting('delete-incomplete-downloads')
          
          if delete_incomplete == 'true':
              if os.path.exists(os.path.join(downloadPath, 'Downloading')):
                  fh = open(os.path.join(downloadPath, 'Downloading'))          
                  filePathDownloading = fh.readline().strip('\n')
                  fh.close()
                  
                  try:
                      os.remove(filePathDownloading)
                  except:
                      pass
                  try:
                      os.remove(filePathDownloading + '.dling')
                  except:
                      pass

          if os.path.exists(os.path.join(downloadPath, 'Downloading')):
              os.remove(os.path.join(downloadPath, 'Downloading'))


    if os.path.isfile(mypath) is True:
        if os.path.isfile(mypath + '.dling'):
            try:
                os.remove(mypath)
                os.remove(mypath + '.dling')
            except:
                print 'download failed: existing incomplete files cannot be removed'
                return
        else:
            Notify('Download Alert','The video you are trying to download already exists!','','')

    try: 
        link=Handle_Vidlink(source['1'])
    except:
        Notify('big','Invalid Source','Unable to play selected source. \n Please try another.','') 
        callEndOfDirectory = False
        return
    if link == None:
        callEndOfDirectory = False
        return

    print 'attempting to download and play file'

    try:
        print "Starting Download Thread"
        dlThread = DownloadThread(link[0], mypath, vidname)
        dlThread.start()
        buffer_delay = int(selfAddon.getSetting('buffer-delay'))
        handle_wait(buffer_delay, "Buffering", "Waiting a bit before playing...")
        if os.path.exists(mypath):
            if dlThread.isAlive():
                listitem=Item_Meta(vidname)
                playList.add(mypath, listitem)
                xbmc.Player().play(playList)
                
                if video_seek:
                    if os.path.exists(mypath):
                        try:
                            os.remove(mypath)
                        except:
                            print 'Failed to delete file after video seeking'
                else:
                    addDownloadControls(name,mypath, listitem)
            else:
                raise
        else:
            raise
    except Exception, e:
        print 'EXCEPTION %s' % e
        if sys.exc_info()[0] in (urllib.ContentTooShortError,): 
            Notify('big','Download and Play failed!','Error: Content Too Short','')
        if sys.exc_info()[0] in (OSError,): 
            Notify('big','Download and Play failed!','Error: Cannot write file to disk','')
        if sys.exc_info()[0] in (SmallFile,): 
            Notify('big','Download and Play failed!','Error: Got a file smaller than 10KB','')
        
    print '***** Made it this far *****'
    
    i=2
    while i <= len(source):
        if os.path.isfile(mypath + '.dling'):
            print '*****Still downloading the current source'
            xbmc.sleep(5000)
        else:
            print '*****start downloading part %s' % str(i)
            link=Handle_Vidlink(source[str(i)], False)
            if link == None:
                callEndOfDirectory = False
                return

            print 'attempting to download and play part %s' % str(i)
            mypath = mypath[0:len(mypath)-1] + str(i)
            vidname = vidname[0:len(vidname)-1] + str(i)
            listitem=Item_Meta(vidname)
            try:
                print "Starting Download Thread"
                dlThread = DownloadThread(link[0], mypath, vidname)
                dlThread.start()

            except Exception, e:
                print 'EXCEPTION %s' % e
                if sys.exc_info()[0] in (urllib.ContentTooShortError,): 
                    Notify('big','Download and Play failed!','Error: Content Too Short','')
                if sys.exc_info()[0] in (OSError,): 
                    Notify('big','Download and Play failed!','Error: Cannot write file to disk','')
                if sys.exc_info()[0] in (SmallFile,): 
                    Notify('big','Download and Play failed!','Error: Got a file smaller than 10KB','')
            
            playList.add(mypath, listitem)
            xbmc.sleep(10000)        
            i+=1
def _dlhook(numblocks, blocksize, filesize, dt, start_time):

    if dt.dialog != None:
        
        try: 
            percent = min(numblocks * blocksize * 100 / filesize, 100)
            currently_downloaded = float(numblocks) * blocksize / (1024 * 1024)
            kbps_speed = numblocks * blocksize / (time.time() - start_time)
            
            if kbps_speed > 0: 
                eta = (filesize - numblocks * blocksize) / kbps_speed 
            else: 
                eta = 0 
            
            kbps_speed = kbps_speed / 1024 
            total = float(filesize) / (1024 * 1024) 
            mbs = '%.02f MB of %.02f MB' % (currently_downloaded, total) 
            e = 'Speed: %.02f Kb/s ' % kbps_speed 
            e += 'ETA: %02d:%02d' % divmod(eta, 60)
            dt.dialog.update(percent, mbs, e)
        
        except: 
            percent = 100 
            dt.dialog.update(percent) 
        
        if dt.dialog.iscanceled():
            dt.hide_dialog()
            
    elif os.path.exists(os.path.join(downloadPath, 'ShowDLInfo')):
        while os.path.exists(os.path.join(downloadPath, 'ShowDLInfo')):
            
            try:
                os.remove(os.path.join(downloadPath, 'ShowDLInfo'))
            except:
                continue
            break
        
        dt.show_dialog()
        
    elif os.path.exists(os.path.join(downloadPath, 'Cancel')):
        while os.path.exists(os.path.join(downloadPath, 'Cancel')):
            
            try:
                os.remove(os.path.join(downloadPath, 'Cancel'))
            except:
                continue
            break
        
        print "Stopping download"
        raise StopDownloading('Stopped Downloading')
        
    elif os.path.exists(os.path.join(downloadPath, 'Ping')):
        while os.path.exists(os.path.join(downloadPath, 'Ping')):
            
            try:
                os.remove(os.path.join(downloadPath, 'Ping'))
            except:
                continue
            break
        
        save(os.path.join(downloadPath,'Alive'),dt.dest+'\n'+dt.vidname)


def Download_Source(name,url):
    #get proper name of vid
    vidname=cache.get('videoname')
    
    mypath=Get_Path(name,vidname)
           
    if mypath == 'path not set':
        Notify('Download Alert','You have not set the download folder.\n Please access the addon settings and set it.','','')
    else:
        if os.path.isfile(mypath) is True:
            Notify('Download Alert','The video you are trying to download already exists!','','')
        else:              
            
            try:
                link=Handle_Vidlink(url)
            except Exception, e:
                print '**** Download error: %s' % e
                Notify('big','Invalid Source','Unable to download select source. \n    Please try another.','')
                callEndOfDirectory = False
                return
            
            DownloadInBack=selfAddon.getSetting('download-in-background')
            print 'attempting to download file, silent = '+ DownloadInBack
            try:
                if DownloadInBack == 'true':
                    QuietDownload(link[0], mypath, vidname)
                else:
                    Download(link[0], mypath, vidname)
            except:
                print 'download failed'


def Check_Mega_Limits(name,url):
     WaitIf()
     mu=megaroutines.megaupload(translatedicedatapath)
     limit=mu.dls_limited()
     if limit is True:
          Notify('megaalert1','','','')
     elif limit is False:
          Notify('megaalert2','','','')

def Kill_Streaming(name,url):
     xbmc.Player().stop()     

class StopDownloading(Exception): 
        def __init__(self, value): 
            self.value = value 
        def __str__(self): 
            return repr(self.value)
          
def Download(url, dest, displayname=False):
         
        if displayname == False:
            displayname=url
        delete_incomplete = selfAddon.getSetting('delete-incomplete-downloads')
        dp = xbmcgui.DialogProgress()
        dp.create('Downloading', '', displayname)
        start_time = time.time() 
        try: 
            urllib.urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(nb, bs, fs, dp, start_time)) 
        except:
            if delete_incomplete == 'true':
                #delete partially downloaded file if setting says to.
                while os.path.exists(dest): 
                    try: 
                        os.remove(dest) 
                        break 
                    except: 
                        pass 
            #only handle StopDownloading (from cancel), ContentTooShort (from urlretrieve), and OS (from the race condition); let other exceptions bubble 
            if sys.exc_info()[0] in (urllib.ContentTooShortError, StopDownloading, OSError): 
                return 'false' 
            else: 
                raise 
        return 'downloaded'

'''     
def QuietDownload(url, dest):
#possibly useful in future addon versions
     
        #dp = xbmcgui.DialogProgress() 
        #dp.create('Downloading', '', name) 
        start_time = time.time() 
        try: 
            #urllib.urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(nb, bs, fs, dp, start_time))
            urllib.urlretrieve(url, dest)
            #xbmc.Player().play(dest)
        except: 
            #delete partially downloaded file 
            while os.path.exists(dest): 
                try: 
                    #os.remove(dest) 
                    break 
                except: 
                     pass 
            #only handle StopDownloading (from cancel), ContentTooShort (from urlretrieve), and OS (from the race condition); let other exceptions bubble 
            if sys.exc_info()[0] in (urllib.ContentTooShortError, StopDownloading, OSError): 
                return 'false' 
            else: 
                raise 
        return 'downloaded' 
'''
def QuietDownload(url, dest, videoname):
    #quote parameters passed to download script     
    q_url = urllib.quote_plus(url)
    q_dest = urllib.quote_plus(dest)
    q_vidname = urllib.quote_plus(videoname)
    
    #Create possible values for notification
    notifyValues = [2, 5, 10, 20, 25, 50, 100]

    # get notify value from settings
    NotifyPercent=int(selfAddon.getSetting('notify-percent'))
    
    script = os.path.join( icepath, 'resources', 'lib', "DownloadInBackground.py" )
    xbmc.executebuiltin( "RunScript(%s, %s, %s, %s, %s)" % ( script, q_url, q_dest, q_vidname, str(notifyValues[NotifyPercent]) ) )
             

def _pbhook(numblocks, blocksize, filesize, dp, start_time):
        try: 
            percent = min(numblocks * blocksize * 100 / filesize, 100) 
            currently_downloaded = float(numblocks) * blocksize / (1024 * 1024) 
            kbps_speed = numblocks * blocksize / (time.time() - start_time) 
            if kbps_speed > 0: 
                eta = (filesize - numblocks * blocksize) / kbps_speed 
            else: 
                eta = 0 
            kbps_speed = kbps_speed / 1024 
            total = float(filesize) / (1024 * 1024) 
            # print ( 
                # percent, 
                # numblocks, 
                # blocksize, 
                # filesize, 
                # currently_downloaded, 
                # kbps_speed, 
                # eta, 
                # ) 
            mbs = '%.02f MB of %.02f MB' % (currently_downloaded, total) 
            e = 'Speed: %.02f Kb/s ' % kbps_speed 
            e += 'ETA: %02d:%02d' % divmod(eta, 60) 
            dp.update(percent, mbs, e)
            #print percent, mbs, e 
        except: 
            percent = 100 
            dp.update(percent) 
        if dp.iscanceled(): 
            dp.close() 
            raise StopDownloading('Stopped Downloading')

   
def addExecute(name,url,mode,iconimage):

    # A list item that executes the next mode, but doesn't clear the screen of current list items.

    #encode url and name, so they can pass through the sys.argv[0] related strings
    sysname = urllib.quote_plus(name)
    sysurl = urllib.quote_plus(url)
    
    u = sys.argv[0] + "?url=" + sysurl + "&mode=" + str(mode) + "&name=" + sysname + "&imdbnum=" + urllib.quote_plus(str(imdbnum))  + "&videoType=" + video_type + "&season=" + str(season_num) + "&episode=" + str(episode_num)
    ok=True

    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    stack_multi=selfAddon.getSetting('stack-multi-part')
    print 'this is the value from stack_multi: %s' % stack_multi
    if stack_multi=='true':
        mode = '209'
    else:
        mode = '206'
        
    #handle adding context menus
    contextMenuItems = []

    contextMenuItems.append(('Play Stream', 'XBMC.RunPlugin(%s?mode=200&name=%s&url=%s)' % (sys.argv[0], sysname, sysurl)))
    contextMenuItems.append(('Download', 'XBMC.RunPlugin(%s?mode=201&name=%s&url=%s)' % (sys.argv[0], sysname, sysurl)))
    contextMenuItems.append(('Download And Watch', 'XBMC.RunPlugin(%s?mode=%s&name=%s&url=%s)' % (sys.argv[0], mode, sysname, sysurl)))
    contextMenuItems.append(('Download with jDownloader', 'XBMC.RunPlugin(plugin://plugin.program.jdownloader/?action=addlink&url=%s)' % (sysurl)))
    contextMenuItems.append(('Check Mega Limits', 'XBMC.RunPlugin(%s?mode=202&name=%s&url=%s)' % (sys.argv[0], sysname, sysurl)))
    contextMenuItems.append(('Kill Streams', 'XBMC.RunPlugin(%s?mode=203&name=%s&url=%s)' % (sys.argv[0], sysname, sysurl)))

    liz.addContextMenuItems(contextMenuItems, replaceItems=True)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    return ok


def addDir(name, url, mode, iconimage, meta=False, imdb=False, delfromfav=False, disablefav=False, searchMode=False, totalItems=0, disablewatch=False, meta_install=False, favourite=False):
     ###  addDir with context menus and meta support  ###

     #encode url and name, so they can pass through the sys.argv[0] related strings
     sysname = urllib.quote_plus(name)
     sysurl = urllib.quote_plus(url)
     dirmode=mode

     #get nice unicode name text.
     #name has to pass through lots of weird operations earlier in the script,
     #so it should only be unicodified just before it is displayed.
     name = htmlcleaner.clean(name)
                 
     #handle adding context menus
     contextMenuItems = []
     
     if mode == 12: # TV series
         videoType = 'tvshow'
     elif mode == 13: # TV Season
         videoType = 'season'
     elif mode == 14: # TV Episode
         videoType = 'episode'
     elif mode == 100: # movies
         videoType = 'movie'
     else:
          videoType = video_type
     
     season = ''
     episode = ''
                 
     if season_num:
         season = season_num
     if episode_num:
         episode = episode_num

     #handle adding meta
     if meta == False:
         liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
         liz.setInfo(type="Video", infoLabels={"Title": name})

     else:
                 
         #check covers installed
         covers_url = ''
         if mode == 12:

             #check tv posters vs banners setting 
             tv_posters = selfAddon.getSetting('tv-posters')
             if tv_posters == 'true':
                 if meta_install['tv_covers'] == 'true':
                     covers_url = meta['cover_url']
             else:
                 if meta_install['tv_banners'] == 'true':
                     covers_url = meta['banner_url']
         else:
             if meta_install['movie_covers'] == 'true':
                 covers_url = meta['cover_url']

         #Set XBMC list item
         liz = xbmcgui.ListItem(name, iconImage=covers_url, thumbnailImage=covers_url)
         liz.setInfo(type="Video", infoLabels=meta)

         #Set fanart/backdrop setting variables
         movie_fanart = selfAddon.getSetting('movie-fanart')
         tv_fanart = selfAddon.getSetting('tv-fanart')
         if meta_install:
             movie_fanart_installed = meta_install['movie_backdrops']
             tv_fanart_installed = meta_install['tv_backdrops']

         # mark as watched or unwatched 
         addWatched = False
         if mode == 12: # TV series
             if int(meta['episode']) > 0:
                 episodes_unwatched = str(int(meta['episode']) - meta['playcount'])
                 liz.setProperty('UnWatchedEpisodes', episodes_unwatched)
                 liz.setProperty('WatchedEpisodes', str(meta['playcount']))
             addWatched = True
             if tv_fanart == 'true' and tv_fanart_installed == 'true':
                 liz.setProperty('fanart_image', meta['backdrop_url'])
             contextMenuItems.append(('Show Information', 'XBMC.Action(Info)'))
             if favourite:
                 contextMenuItems.append(('Show Next Aired', 'RunScript(%s)' % os.path.join(icepath, 'resources/script.tv.show.next.aired/default.py')))
         elif mode == 13: # TV Season
             addWatched = True
             if tv_fanart == 'true' and tv_fanart_installed == 'true':
                 liz.setProperty('fanart_image', meta['backdrop_url'])                

             season = meta['season']
             contextMenuItems.append(('Refresh Info', 'XBMC.RunPlugin(%s?mode=998&name=%s&url=%s&imdbnum=%s&dirmode=%s&videoType=%s&season=%s)' % (sys.argv[0], sysname, sysurl, urllib.quote_plus(str(imdb)), dirmode, videoType, season)))             
         elif mode == 14: # TV Episode
             addWatched = True
             if tv_fanart == 'true' and tv_fanart_installed == 'true':
                 liz.setProperty('fanart_image', meta['backdrop_url'])
             season = meta['season']
             episode = meta['episode']
             contextMenuItems.append(('Episode Information', 'XBMC.Action(Info)'))
             contextMenuItems.append(('Refresh Info', 'XBMC.RunPlugin(%s?mode=997&name=%s&url=%s&imdbnum=%s&dirmode=%s&videoType=%s&season=%s&episode=%s)' % (sys.argv[0], sysname, sysurl, urllib.quote_plus(str(imdb)), dirmode, videoType, season, episode)))
         elif mode == 100: # movies
             addWatched = True
             if movie_fanart == 'true' and movie_fanart_installed == 'true':
                 liz.setProperty('fanart_image', meta['backdrop_url'])
             #if searchMode == False:
             contextMenuItems.append(('Movie Information', 'XBMC.Action(Info)'))
         #Add Refresh & Trailer Search context menu
         if searchMode==False:
             if mode in (12, 100):
                 contextMenuItems.append(('Refresh Info', 'XBMC.RunPlugin(%s?mode=999&name=%s&url=%s&imdbnum=%s&dirmode=%s&videoType=%s)' % (sys.argv[0], sysname, sysurl, urllib.quote_plus(str(imdb)), dirmode, videoType)))
                 contextMenuItems.append(('Search for trailer', 
                                          'XBMC.RunPlugin(%s?mode=996&name=%s&url=%s&dirmode=%s&imdbnum=%s)' 
                                          % (sys.argv[0], sysname, sysurl, dirmode, urllib.quote_plus(str(imdb))) ))                        
                     
         #Add Watch/Unwatch context menu             
         if addWatched and not disablewatch:
             if meta['overlay'] == 6:
                 watchedMenu='Mark as Watched'
             else:
                 watchedMenu='Mark as Unwatched'
             if searchMode==False:
                 contextMenuItems.append((watchedMenu, 'XBMC.RunPlugin(%s?mode=990&name=%s&url=%s&imdbnum=%s&videoType=%s&season=%s&episode=%s)' 
                     % (sys.argv[0], sysname, sysurl, urllib.quote_plus(str(imdb)), videoType, season, episode)))
    
     # add/delete favourite
     if disablefav is False: # disable fav is necessary for the scrapes in the homepage category.
         if delfromfav is True:
             #settings for when in the Favourites folder
             contextMenuItems.append(('Delete from Ice Favourites', 'XBMC.RunPlugin(%s?mode=111&name=%s&url=%s)' % (sys.argv[0], sysname, sysurl)))
         else:
             #if directory is an tv show or movie NOT and episode
             if mode == 100 or mode == 12:
                 if imdb is not False:
                     sysimdb = urllib.quote_plus(str(imdb))
                 else:
                     #if no imdb number, it will have no metadata in Favourites
                     sysimdb = urllib.quote_plus('nothing')
                 #if searchMode==False:
                 contextMenuItems.append(('Add to Ice Favourites', 'XBMC.RunPlugin(%s?mode=110&name=%s&url=%s&imdbnum=%s)' % (sys.argv[0], sysname, sysurl, sysimdb)))
                        
     if contextMenuItems:
         liz.addContextMenuItems(contextMenuItems, replaceItems=True)

     if mode == 14:
         if check_episode(name):
             episode_info = re.search('([0-9]+)x([0-9]+)', name)
             season = int(episode_info.group(1))
             episode = int(episode_info.group(2))
             mode = 100

     if mode in (12, 13, 100, 101, 102, 103, 104):
         u = sys.argv[0] + "?url=" + sysurl + "&mode=" + str(mode) + "&name=" + sysname + "&imdbnum=" + urllib.quote_plus(str(imdb)) + "&videoType=" + videoType + "&season=" + str(season) + "&episode=" + str(episode)
     else:
         u = sys.argv[0] + "?url=" + sysurl + "&mode=" + str(mode) + "&name=" + sysname
     ok = True

     ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True, totalItems=totalItems)
     return ok
     

#VANILLA ADDDIR (kept for reference)
def VaddDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


def setView(content, viewType):
    
    # set content type so library shows more views and info
    if content:
        xbmcplugin.setContent(int(sys.argv[1]), content)
    if selfAddon.getSetting('auto-view') == 'true':
        xbmc.executebuiltin("Container.SetViewMode(%s)" % selfAddon.getSetting(viewType) )
    
    # set sort methods - probably we don't need all of them
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    
#Movie Favourites folder.
def MOVIE_FAVOURITES(url):
    
    #get settings
    favpath=os.path.join(translatedicedatapath,'Favourites')
    moviefav=os.path.join(favpath,'Movies')
    try:
        moviedircontents=os.listdir(moviefav)
    except:
        moviedircontents=None
    
    if moviedircontents == None:
        Notify('big','No Movie Favourites Saved','To save a favourite press the C key on a movie or\n TV Show and select Add To Icefilms Favourites','')
    
    else:
        #add clear favourites entry - Not sure if we must put it here, cause it will mess up the sorting
        #addExecute('* Clear Favourites Folder *',url,58,os.path.join(art,'deletefavs.png'))
        
        #handler for all movie favourites
        if moviedircontents is not None:
 
             #add with metadata -- imdb is still passed for use with Add to Favourites
            if meta_setting=='true':
                addFavourites(True,moviefav,moviedircontents, 'movie')                      
            #add without metadata -- imdb is still passed for use with Add to Favourites
            else:
                addFavourites(False,moviefav,moviedircontents, 'movie')
            

        else:
            print 'moviedircontents is none!'
            
    # Enable library mode & set the right view for the content
    setView('movies', 'movies-view')


#TV Shows Favourites folder
def TV_FAVOURITES(url):
    
    favpath=os.path.join(translatedicedatapath,'Favourites')
    tvfav=os.path.join(favpath,'TV')
    try:
        tvdircontents=os.listdir(tvfav)
    except:
        tvdircontents=None
 
    if tvdircontents == None:
        Notify('big','No TV Favourites Saved','To save a favourite press the C key on a movie or\n TV Show and select Add To Icefilms Favourites','')

    else:
        #add clear favourites entry - Not sure if we must put it here, cause it will mess up the sorting
        #addExecute('* Clear Favourites Folder *',url,58,os.path.join(art,'deletefavs.png'))
               
        #handler for all tv favourites
        if tvdircontents is not None:
                       
            #add with metadata -- imdb is still passed for use with Add to Favourites
            if meta_setting=='true':
                addFavourites(True,tvfav,tvdircontents,'tvshow')  
            #add without metadata -- imdb is still passed for use with Add to Favourites
            else:
                addFavourites(False,tvfav,tvdircontents,'tvshow')
                
           
        else:
            print 'tvshows dircontents is none!'
    
    # Enable library mode & set the right view for the content
    setView('tvshows', 'tvshows-view')


def cleanUnicode(string):
    try:
        string = string.replace("'","").replace(unicode(u'\u201c'), '"').replace(unicode(u'\u201d'), '"').replace(unicode(u'\u2019'),'').replace(unicode(u'\u2026'),'...').replace(unicode(u'\u2018'),'').replace(unicode(u'\u2013'),'-')
        return string
    except:
        return string


def getMeta(scrape, mode):

    #check settings over whether to display the number of episodes next to tv show name.
    show_num_of_eps=selfAddon.getSetting('display-show-eps')
    
    #print scrape

    #add with metadata
    if meta_setting=='true':
    
        #initialise meta class before loop
        metaget=metahandlers.MetaData(preparezip=prepare_zip)
        meta_installed = metaget.check_meta_installed(addon_id)

        #determine whether to show number of eps
        if scrape[3] and show_num_of_eps == 'true' and mode == 12:
            for imdb_id,url,name,num_of_eps in scrape:
                num_of_eps=re.sub('<','',num_of_eps)
                num_of_eps=re.sub('isode','',num_of_eps)#turn Episode{s} into Ep(s)
                ADD_ITEM(metaget,meta_installed,imdb_id,url,name,mode,num_of_eps, totalitems=len(scrape))
        elif mode == 12: # fix for tvshows with num of episodes disabled
            for imdb_id,url,name, blank in scrape:
                ADD_ITEM(metaget,meta_installed,imdb_id,url,name,mode, totalitems=len(scrape))
        else:
            for imdb_id,url,name in scrape:
                ADD_ITEM(metaget,meta_installed,imdb_id,url,name,mode, totalitems=len(scrape))
                
    #add without metadata -- imdb is still passed for use with Add to Favourites
    else:
        for imdb_id,url,name in scrape:
            name=CLEANUP(name)
            addDir(name,iceurl+url,mode,'',imdb='tt'+str(imdb_id), totalItems=len(scrape))
            

def ADD_ITEM(metaget, meta_installed, imdb_id,url,name,mode,num_of_eps=False, totalitems=0):
            #clean name of unwanted stuff
            name=CLEANUP(name)
            if url.startswith('http://www.icefilms.info') == False:
                url=iceurl+url

            #append number of episodes to the display name, AFTER THE NAME HAS BEEN USED FOR META LOOKUP
            if num_of_eps is not False:
                name = name + ' ' + str(num_of_eps)
                
            if meta_installed and meta_setting=='true':
                #return the metadata dictionary
                #we want a clean name with the year separated for proper meta search and storing
                meta_name = CLEANUP_FOR_META(name)           
                r=re.search('(.+?) [(]([0-9]{4})[)]',meta_name)
                if r:
                    meta_name = r.group(1)
                    year = r.group(2)
                else:
                    year = ''
                if mode==100:
                    #return the metadata dictionary
                    meta=metaget.get_meta('movie', meta_name, imdb_id=imdb_id, year=year)
                elif mode==12:
                    #return the metadata dictionary
                    meta=metaget.get_meta('tvshow', meta_name, imdb_id=imdb_id)
                
                addDir(name,url,mode,'',meta=meta,imdb='tt'+str(imdb_id),totalItems=totalitems, meta_install=meta_installed)  
           
            else:
                #add directories without meta
                if imdb_id == None:
                    imdb_id == ''
                else:
                    imdb_id = 'tt'+str(imdb_id)
                addDir(name,url,mode,'',imdb=imdb_id,totalItems=totalitems)


def REFRESH(videoType, url,imdb_id,name,dirmode):
        #refresh info for a Tvshow or movie
               
        print 'In Refresh ' + str(sys.argv[1])
        imdb_id = imdb_id.replace('tttt','')

        if meta_setting=='true':
            metaget=metahandlers.MetaData(preparezip=prepare_zip)
            meta_installed = metaget.check_meta_installed(addon_id)          
            
            if meta_installed:
                name=CLEANUP(name)
                r=re.search('(.+?) [(]([0-9]{4})[)]',name)
                if r:
                    name = r.group(1)
                    year = r.group(2)
                else:
                    year = ''
                metaget.update_meta(videoType, name, imdb_id, year=year)
                xbmc.executebuiltin("XBMC.Container.Refresh")           


def episode_refresh(url, imdb_id, name, dirmode, season, episode):
        #refresh info for an episode
               
        print 'In Episode Refresh ' + str(sys.argv[1])
        imdb_id = imdb_id.replace('tttt','')

        if meta_setting=='true':
            metaget=metahandlers.MetaData(preparezip=prepare_zip)
            meta_installed = metaget.check_meta_installed(addon_id)          
            
            if meta_installed:
                name=CLEANUP(name)
                metaget.update_episode_meta(name, imdb_id, season, episode)
                xbmc.executebuiltin("XBMC.Container.Refresh")



def season_refresh(url, imdb_id, name, dirmode, season):
        #refresh info for an episode
               
        print 'In Season Refresh ' + str(sys.argv[1])
        imdb_id = imdb_id.replace('tttt','')

        if meta_setting=='true':
            metaget=metahandlers.MetaData(preparezip=prepare_zip)
            meta_installed = metaget.check_meta_installed(addon_id)          
            
            if meta_installed:
                name=CLEANUP(name)            	
                metaget.update_season(name, imdb_id, season)
                xbmc.executebuiltin("XBMC.Container.Refresh")


def get_episode(season, episode, imdb_id, url, metaget, meta_installed, tmp_season_num=-1, tmp_episode_num=-1, totalitems=0):
        # displays all episodes in the source it is passed.
        imdb_id = imdb_id.replace('t','')
   
        #add with metadata
        if metaget:
            
            #clean name of unwanted stuff
            episode=CLEANUP(episode)
             
            #Get tvshow name - don't want the year portion
            showname=cache.get('mediatvshowname')
            r=re.search('(.+?) [(][0-9]{4}[)]',showname)
            if r:
                showname = r.group(1)
                           
            #return the metadata dictionary
            ep = re.search('[0-9]+x([0-9]+)', episode)
            if ep: 
                tmp_episode_num = int(ep.group(1))
            se = re.search('Season ([0-9]{1,2})', season)
            if se:
                tmp_season_num = int(se.group(1))

            meta = {}
            
            if meta_installed and tmp_episode_num >= 0:
                showname = CLEANUP_FOR_META(showname)
                meta=metaget.get_episode_meta(showname, imdb_id, tmp_season_num, tmp_episode_num)
                      
            if meta and meta_installed:
                #add directories with meta
                addDir(episode,iceurl+url,14,'',meta=meta,imdb='tt'+str(imdb_id),totalItems=totalitems, meta_install=meta_installed)
            else:
                #add directories without meta
                addDir(episode,iceurl+url,14,'',imdb='tt'+str(imdb_id),totalItems=totalitems)

        
        #add without metadata -- imdb is still passed for use with Add to Favourites
        else:
            episode=CLEANUP(episode)
            addDir(episode,iceurl+url,100,'',imdb='tt'+str(imdb_id),totalItems=totalitems)                

              
def find_meta_for_search_results(results, mode, search=''):
    
    #initialise meta class before loop
    metaget=metahandlers.MetaData(preparezip=prepare_zip)
    meta_installed = metaget.check_meta_installed(addon_id)
    
    if mode == 100:        
        for res in results:
            name=res.title.encode('utf8')
            name=CLEANSEARCH(name)
                
            url=res.url.encode('utf8')
            url=re.sub('&amp;','&',url)

            if check_episode(name):
                mode = 14
            else:
                mode = 100
                                                                       
            if meta_installed and meta_setting=='true':
                meta = check_video_meta(name, metaget)
                addDir(name,url,mode,'',meta=meta,imdb=meta['imdb_id'],searchMode=True, meta_install=meta_installed)
            else:
                addDir(name,url,mode,'',searchMode=True)

            
    elif mode == 12:
        for myurl,interim,name in results:
            print myurl, interim, name
            if len(interim) < 180:
                name=CLEANSEARCH(name)                              
                hasnameintitle=re.search(search,name,re.IGNORECASE)
                print 'NAME: %s' % name
                print 'SEARCH: %s' % search
                if hasnameintitle:
                    myurl='http://www.icefilms.info/tv/series'+myurl
                    myurl=re.sub('&amp;','',myurl)
                    if myurl.startswith('http://www.icefilms.info/tv/series'):
                        if meta_installed==True and meta_setting=='true':
                            meta = metaget.get_meta('tvshow',name)
                            addDir(name,myurl,12,'',meta=meta,imdb=meta['imdb_id'],searchMode=True)                           
                        else:
                            addDir(name,myurl,12,'',searchMode=True)
                    else:
                        addDir(name,myurl,12,'',searchMode=True)
 
         
def SearchGoogle(search):
    gs = GoogleSearch(''+search+' site:http://www.youtube.com ')
    gs.results_per_page = 25
    gs.page = 0
    try:
        results = gs.get_results()
    except Exception, e:
        print '***** Error: %s' % e
        Notify('big','Google Search','Error encountered searching.','')
        return None
    return results
                               
def SearchForTrailer(search, imdb_id, type, manual=False):
    search = search.replace(' *HD 720p*', '')
    res_name = []
    res_url = []
    res_name.append('Manualy enter search...')
    
    if manual:
        results = SearchGoogle(search)
        for res in results:
            if res.url.encode('utf8').startswith('http://www.youtube.com/watch'):
                res_name.append(res.title.encode('utf8'))
                res_url.append(res.url.encode('utf8'))
    else:
        results = SearchGoogle(search+' official trailer')
        for res in results:
            if res.url.encode('utf8').startswith('http://www.youtube.com/watch'):
                res_name.append(res.title.encode('utf8'))
                res_url.append(res.url.encode('utf8'))
        results = SearchGoogle(search[:(len(search)-7)]+' official trailer')
        for res in results:
            if res.url.encode('utf8').startswith('http://www.youtube.com/watch') and res.url.encode('utf8') not in res_url:
                res_name.append(res.title.encode('utf8'))
                res_url.append(res.url.encode('utf8'))
            
    dialog = xbmcgui.Dialog()
    ret = dialog.select(search + ' trailer search',res_name)
    
    # Manual search for trailer
    if ret == 0:
        if manual:
            default = search
            title = 'Manual Search for '+search
        else:
            default = search+' official trailer'
            title = 'Manual Trailer Search for '+search
        keyboard = xbmc.Keyboard(default, title)
        #keyboard.setHiddenInput(hidden)
        keyboard.doModal()
        
        if keyboard.isConfirmed():
            result = keyboard.getText()
            SearchForTrailer(result, imdb_id, type, manual=True) 
    # Found trailers
    elif ret > 1:
        trailer_url = res_url[ret - 2]
        print trailer_url
        xbmc.executebuiltin(
            "PlayMedia(plugin://plugin.video.youtube/?action=play_video&videoid=%s&quality=720p)" 
            % str(trailer_url)[str(trailer_url).rfind("v=")+2:] )
        
        #dialog.ok(' title ', ' message ')
        metaget=metahandlers.MetaData(preparezip=prepare_zip)
        if type==100:
            type='movie'
        elif type==12:
            type='tvshow'
        metaget.update_trailer(type, imdb_id, trailer_url)
        xbmc.executebuiltin("XBMC.Container.Refresh")
    else:
        res_name.append('Nothing Found. Thanks!!!')


def ChangeWatched(imdb_id, videoType, name, season, episode, year='', watched='', refresh=False):
    metaget=metahandlers.MetaData(preparezip=prepare_zip)
    metaget.change_watched(videoType, name, imdb_id, season=season, episode=episode, year=year, watched=watched)
    if refresh:
        xbmc.executebuiltin("XBMC.Container.Refresh")


def addLocal(name,filename, listitem=False):

    if listitem == None:
        liz=xbmcgui.ListItem(name)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
    else:
        liz = listitem
    ok=True
    liz=xbmcgui.ListItem(name)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
 
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=filename,listitem=liz,isFolder=False)
    return ok
     
     
def addDownloadControls(name,localFilePath, listitem=None):
    #encode name
    sysname = urllib.quote_plus(name)
    
    statusUrl = sys.argv[0] + "?mode=207&name=" + sysname
    cancelUrl = sys.argv[0] + "?&mode=208&name=" + sysname
    ok = True
    
    #add Download info
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=statusUrl,listitem=xbmcgui.ListItem("Download Info"),isFolder=False)
    print 'Ok: %s' % ok
          
    #add Cancel Download
    ok = ok and xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=cancelUrl,listitem=xbmcgui.ListItem("Cancel Download"),isFolder=False)
    print 'Ok: %s' % ok

    #add Play File
    ok = ok and addLocal("Play Downloading " + name, localFilePath, listitem)
    print 'Ok: %s' % ok
    
    return ok


def ShowDownloadInfo(name):
    if not os.path.exists(os.path.join(downloadPath, 'Downloading')):
        Notify('big','Download Inactive!','Download is not active','')
    else:
        save(os.path.join(downloadPath, 'ShowDLInfo'),'ShowDLInfo')
    return True
 

def CancelDownload(name, video_seek=False):
    if not os.path.exists(os.path.join(downloadPath, 'Downloading')):
        if not video_seek:
            Notify('big','Download Inactive!','Download is not active','')
    else:
        save(os.path.join(downloadPath, 'Cancel'),'Cancel')    
    return True


def get_default_action():
   action_setting = selfAddon.getSetting('play-action')
   print "action_setting =" + action_setting
   if action_setting == "1":
       return 201
   elif action_setting == "2":
       return 206

   #default is stream
   return 200


def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

params=get_params()

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        imdbnum=urllib.unquote_plus(params["imdbnum"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        dirmode=int(params["dirmode"])
except:
        pass
try:
        season_num=urllib.unquote_plus(params["season"])
        #season=params["season"]
except:
        pass
try:
        episode_num=urllib.unquote_plus(params["episode"])
        #season=params["episode"]
except:
        pass        
try:
        video_type=urllib.unquote_plus(params["videoType"])
except:
        pass
print '==========================PARAMS:\nURL: %s\nNAME: %s\nMODE: %s\nIMDBNUM: %s\nVIDEOTYPE: %s\nMYHANDLE: %s\nPARAMS: %s' % ( url, name, mode, imdbnum, video_type, sys.argv[1], params )

if mode==None: #or url==None or len(url)<1:
        print ""
        CATEGORIES()

elif mode==999:
        print "Mode 999 ******* dirmode is " + str(dirmode) + " *************  url is -> "+url
        REFRESH(video_type, url,imdbnum,name,dirmode)


elif mode==998:
        print "Mode 998 (season meta refresh) ******* dirmode is " + str(dirmode) + " *************  url is -> "+url
        season_refresh(url,imdbnum,name,dirmode,season_num)
        
elif mode==997:
        print "Mode 997 (episode meta refresh) ******* dirmode is " + str(dirmode) + " *************  url is -> "+url
        episode_refresh(url,imdbnum,name,dirmode,season_num,episode_num)    


elif mode==996:
        print "Mode 996 (trailer search) ******* name is " + str(name) + " *************  url is -> "+url
        SearchForTrailer(name, imdbnum, dirmode)
        
elif mode==990:
        print "Mode 990 (Change watched value) ******* name is " + str(name) + " *************  season is -> '"+season_num+"'" + " *************  episode is -> '"+episode_num+"'"
        ChangeWatched(imdbnum, video_type, name, season_num, episode_num, refresh=True)
 
elif mode==50:
        print ""+url
        TVCATEGORIES(url)

elif mode==51:
        print ""+url
        MOVIECATEGORIES(url)

elif mode==52:
        print ""+url
        MUSICCATEGORIES(url)

elif mode==53:
        print ""+url
        STANDUPCATEGORIES(url)

elif mode==54:
        print ""+url
        OTHERCATEGORIES(url)

elif mode==55:
        print ""+url
        SEARCH(url)

elif mode==56:
        print ""+url
        ICEHOMEPAGE(url)

elif mode==57:
        print ""+url
        FAVOURITES(url)

elif mode==570:
        print ""+url
        TV_FAVOURITES(url)

elif mode==571:
        print ""+url
        MOVIE_FAVOURITES(url)

elif mode==58:
        print ""+url
        CLEAR_FAVOURITES(url)

elif mode==60:
        print ""+url
        RECENT(url)

elif mode==61:
        print ""+url
        LATEST(url)

elif mode==62:
        print ""+url
        WATCHINGNOW(url)

elif mode==63:
        print ""+url
        HD720pCat(url)
        
elif mode==64:
        print ""+url
        Genres(url)

elif mode==70:
        print ""+url
        Action(url)

elif mode==71:
        print ""+url
        Animation(url)

elif mode==72:
        print ""+url
        Comedy(url)

elif mode==73:
        print ""+url
        Documentary(url)

elif mode==74:
        print ""+url
        Drama(url)

elif mode==75:
        print ""+url
        Family(url)

elif mode==76:
        print ""+url
        Horror(url)

elif mode==77:
        print ""+url
        Romance(url)

elif mode==78:
        print ""+url
        SciFi(url)

elif mode==79:
        print ""+url
        Thriller(url)
    
elif mode==1:
        print ""+url
        MOVIEA2ZDirectories(url)

elif mode==2:
        print ""+url
        MOVIEINDEX(url)
        
elif mode==10:
        print ""+url
        TVA2ZDirectories(url)

elif mode==11:
        print ""+url
        TVINDEX(url)

elif mode==12:
        print ""+url
        TVSEASONS(url,imdbnum)

elif mode==13:
        print ""+url
        TVEPISODES(name,url,None,imdbnum)

elif mode==99:
        print ""+url
        CAPTCHAENTER(url)
        
elif mode==100:
        print ""+url
        LOADMIRRORS(url)

elif mode==101:
        print ""+url
        DVDRip(url)

elif mode==102:
        print ""+url
        HD720p(url)

elif mode==103:
        print ""+url
        DVDScreener(url)

elif mode==104:
        print ""+url
        R5R6(url)

elif mode==110:
        # if you dont use the "url", "name" params() then you need to define the value# along with the other params.
        ADD_TO_FAVOURITES(name,url,imdbnum)

elif mode==111:
        print ""+url
        DELETE_FROM_FAVOURITES(name,url)

elif mode==199:
        print ""+url
        Stream_Source_with_parts(name,url)

elif mode==200:
        print ""+url      
        Stream_Source(name,url)

elif mode==201:
        Download_Source(name,url)

elif mode==202:
        Check_Mega_Limits(name,url)

elif mode==203:
        Kill_Streaming(name,url)

elif mode==205:
        PlayFile(name,url)
        
elif mode==206:
        Download_And_Play(name,url)

elif mode==207:
        ShowDownloadInfo(name)

elif mode==208:
        CancelDownload(name)        
elif mode==209:
        Download_And_Play_With_Parts(name,url) 
         
elif mode==666:
        create_meta_pack()

if callEndOfDirectory and int(sys.argv[1]) <> -1:
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
#xbmcplugin.endOfDirectory(int(sys.argv[1]))
