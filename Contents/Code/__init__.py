import re, os
from base64 import b64encode

###################################################################################################
##
##  TODO:   ?integrate new CouchPotato API (when it is released)?
##  
###################################################################################################

PREFIX = "/video/couchpotato"

NAME = L('CouchPotato')

ART           = 'art-default.jpg'
ICON          = 'icon-default.png'
SEARCH_ICON   = 'icon-search.png'
PREFS_ICON    = 'icon-prefs.png'
SNATCHED_ICON = 'sab-icon.png'
DL_ICON       = 'Plex_256x256.png'
MOVIE_ICON    = 'movie-reel.jpg'
THEATRE_ICON  = 'popcorn.jpg'
BD_ICON       = 'BD_icon.jpg'

#TRAILER RELATED GLOBAL VARIABLES#
##BORROWED FROM AVForums PLUGIN##
YOUTUBE_VIDEO_PAGE = 'http://www.youtube.com/watch?v=%s'
YT_GET_VIDEO_URL = 'http://www.youtube.com/get_video?video_id=%s&t=%s&fmt=%d&asv=3'

YOUTUBE_VIDEO_FORMATS = ['Standard', 'Medium', 'High', '720p', '1080p']
YOUTUBE_FMT = [34, 18, 35, 22, 37]

####################################################################################################

def Start():
    '''Setup plugin for use'''
    #Plugin.AddPrefixHandler(PREFIX, MainMenu, L('CouchPotato'), ICON, ART)
    
    if Dict['MovieSectionID'] == None:
        Plugin.AddPrefixHandler(PREFIX, GetMovieSectionID, NAME, ICON, ART)
    else:
        Plugin.AddPrefixHandler(PREFIX, MainMenu, NAME, ICON, ART)
    
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    HTTP.CacheTime=3600

    #if Prefs['cpUser'] and Prefs['cpPass']:
    #    HTTP.SetPassword(url=Get_CP_URL(), username=Prefs['cpUser'], password=Prefs['cpPass'])

####################################################################################################

def AuthHeader():
    header = {}

    if Prefs['cpUser'] and Prefs['cpPass']:
        header = {'Authorization': 'Basic ' + b64encode(Prefs['cpUser'] + ':' + Prefs['cpPass'])}

    return header

####################################################################################################

def ValidatePrefs():
    #if Prefs['cpUser'] and Prefs['cpPass']:
    #    HTTP.SetPassword(url=Get_CP_URL(), username=Prefs['cpUser'], password=Prefs['cpPass'])
    return

####################################################################################################

def MainMenu():
    '''Populate main menu options'''
    dir = MediaContainer(viewGroup="InfoList", title="CouchPotato", noCache=True, cacheTime=0)

    dir.Append(Function(DirectoryItem(MoviesMenu,"Movies","Wanted List",
        summary="View and edit your CouchPotato wanted movies list",thumb=R(ICON))))
    dir.Append(Function(DirectoryItem(ComingSoonMenu,"Coming Soon", "",
        summary="Browse upcoming movies and add them to your wanted list",thumb=R(ICON))))
    dir.Append(Function(InputDirectoryItem(SearchResults,"Search","Movie Search",
        summary="Find movies to add to your wanted list",thumb=R(SEARCH_ICON))))
    dir.Append(PrefsItem(title="Preferences",subtitle="CouchPotato plugin preferences",
        summary="Set prefs to allow plugin to connect to CouchPotato app",thumb=R(PREFS_ICON)))
    if Prefs['allowDEL']:
        dir.Append(Function(DirectoryItem(RecentlyViewedMenu, L('Delete recently viewed'),
            L('Select movies from the recently viewed list to remove from the library'), thumb=R(ICON))))
    if UpdateAvailable():
        Log('Update available')
        dir.Append(Function(PopupDirectoryItem(UpdateMenu, title='CouchPotato update available',
            subtitle='Ruudburger\'s been busy', summary='Update your CouchPotato install to the newest version',
            thumb=R(ICON))))

    return dir

################################################################################

def MoviesMenu(sender):
    '''Populate the movies menu with available options'''
    dir = MediaContainer(viewGroup="InfoList", title2="Wanted Movies")

    dir.Append(Function(DirectoryItem(WantedMenu,"Wanted", subtitle=None,
        summary="View and edit your wanted movies list",thumb=R(ICON))))
    dir.Append(Function(DirectoryItem(WaitingMenu,"Waiting", subtitle=None,
        summary="View and edit list of waiting movies from your wanted list",thumb=R(ICON))))
    dir.Append(Function(DirectoryItem(SnatchedMenu,"Snatched", subtitle=None,
        summary="View and edit list of snatched movies from your wanted list",thumb=R(SNATCHED_ICON))))
    dir.Append(Function(DirectoryItem(DownloadedMenu,"Downloaded", subtitle=None,
        summary="View and edit list of downloaded movies from your wanted list",thumb=R(DL_ICON))))
    return dir
    
################################################################################

def WantedMenu(sender):
    '''Scrape wanted movies from CouchPotato and populate the list with results'''
    url = Get_CP_URL()  + '/movie/'
    dir = MediaContainer(viewGroup="InfoList", title2="Wanted", noCache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', headers=AuthHeader(), cacheTime=0)
    
    for item in wantedPage.xpath('//div[@class="item want"]'):
        # get thumb from tmdb.org
        tmdbLink = item.xpath('./span[@class="info"]/a')[1].get('href')
        try: thumbUrl = HTML.ElementFromURL(
            tmdbLink,errors='ignore').xpath(
            '//div[@id="leftCol"]/a/img')[0].get(
            'src')    
        except: thumbUrl = 'http://hwcdn.themoviedb.org/images/no-poster.jpg'
        title = item.xpath('./span/span/h2')[0].text
        #Log('Parsing ' + title)
        try: summary = item.xpath('./span/span/span')[0].text
        except: summary = 'No Overview'
        try: rating = item.xpath('./span/span/span')[1].text
        except: rating = 'No Rating'
        year = item.xpath('./span')[1].text
        dir.Append(Function(PopupDirectoryItem(WantedList, title, year, summary, thumb=Function(GetThumb, url=thumbUrl)), key = item.xpath('.')[0].get('data-id')))
    
    return dir
  
################################################################################

def WaitingMenu(sender):
    '''Scrape waiting movies from CouchPotato and populate the list with results.
        Note: waiting movies differ from wanted movies only by one tag'''
    url = Get_CP_URL() + '/movie/'
    dir = MediaContainer(viewGroup="InfoList", title2="Waiting", noCache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', headers=AuthHeader(), cacheTime=0)
    
    for item in wantedPage.xpath('//div[@class="item waiting"]'):
        #Log('parsing movie item')
        # get thumb from tmdb.org
        tmdbLink = item.xpath('./span[@class="info"]/a')[1].get('href')
        #Log('tmdb: ' + tmdbLink)
        #thumb = GetPoster(tmdbLink)
        try: thumbUrl = HTML.ElementFromURL(
            tmdbLink,errors='ignore').xpath(
            '//div[@id="leftCol"]/a/img')[0].get(
            'src')    
        except: thumbUrl = 'http://hwcdn.themoviedb.org/images/no-poster.jpg'
        title = item.xpath('./span/span/h2')[0].text
        #Log('Parsing ' + title)
        try: summary = item.xpath('./span/span/span')[0].text
        except: summary = 'No Overview'
        #Log(title + ' overview: ...')
        try: rating = item.xpath('./span/span/span')[1].text
        except: rating = 'No Rating'
        #Log(title  + ' rating: ' + rating)
        year = item.xpath('./span')[1].text
        #Log(title + ' year: ' + year)
        dir.Append(Function(PopupDirectoryItem(WantedList, title, year, summary, thumb=Function(GetThumb, url=thumbUrl)), key = item.xpath('.')[0].get('data-id')))
    
    return dir
  
################################################################################

def SnatchedMenu(sender):
    '''Scrape snatched movies from CouchPotato and populate the list with results'''
    url = Get_CP_URL() + '/movie/'
    dir = MediaContainer(viewGroup="InfoList", title2="Snatched", noCache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0)
    thumb = R(SNATCHED_ICON)
    summary = 'This movie should now appear in your downloads queue.'
    
    for item in wantedPage.xpath('//div[@id="snatched"]/span'):
        Log('parsing movie item')
        title = item.text.replace('\n','').replace('\t','')
        Log('Parsing ' + title)
        dir.Append(Function(PopupDirectoryItem(SnatchedList, title, "Queued", summary, thumb), key = item.xpath('./a')[1].get('data-id')))
    
    return dir
  
################################################################################

def DownloadedMenu(sender):
    '''Scrape downloaded movies from CouchPotato and populate the list with results'''
    url = Get_CP_URL() + '/movie/'
    dir = MediaContainer(viewGroup="InfoList", title2="Downloaded", noCache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', headers=AuthHeader(), cacheTime=0)
    thumb = R(DL_ICON)
    summary = 'This movie should now be available in your Plex library.'
    
    for item in wantedPage.xpath('//div[@id="downloaded"]/span'):
        title = item.text.replace('\n','').replace('\t','')
        Log('Parsing ' + title)
        dir.Append(Function(PopupDirectoryItem(SnatchedList, title, "Downloaded", summary, thumb), key = item.xpath('./a')[1].get('data-id')))
    
    return dir
  
################################################################################

def WantedList(sender, key):
    '''Display an action-context menu for the selected movie'''
    movieID = key
    dir = MediaContainer(title2="Wanted Movies")
    dir.Append(Function(DirectoryItem(ForceRefresh, title='Refresh'), key=movieID))
    dir.Append(Function(DirectoryItem(RemoveMovie, title='Delete'), key=movieID))
    return dir

################################################################################

def SnatchedList(sender, key):
    '''Display an action-context menu for the selected movie'''
    movieID = key
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(DownloadComplete, title='Mark Download Complete'), key=movieID))
    dir.Append(Function(DirectoryItem(FailedRetry, title='Failed - Try Again'), key=movieID))
    dir.Append(Function(DirectoryItem(FailedFindNew, title='Failed - Find New Source'), key=movieID))
    return dir

################################################################################

def ForceRefresh(sender, key):
    '''Force CouchPotato to refresh info and search for the selected movie'''
    url = Get_CP_URL() + '/cron/forceSingle/?id=' + key
    Log('Forcecheck url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return MessageContainer("CouchPotato", L('Forcing refresh/search'))

################################################################################

def RemoveMovie(sender, key):
    '''Tell CouchPotato to remove the selected movie from the wanted list'''
    url = Get_CP_URL() + '/movie/delete/?id=' + key
    Log('DeleteMovie url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return MessageContainer("CouchPotato", L('Deleting from wanted list'))

################################################################################

def DownloadComplete(sender, key):
    '''Tell CouchPotato to mark the selected movie as a completed download'''
    url = Get_CP_URL() + '/movie/downloaded/?id=' + key
    Log('Downloaded url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return MessageContainer("CouchPotato", L('Marked Download Complete'))

################################################################################

def FailedRetry(sender, key):
    '''Tell CouchPotato to mark the selected movie as a failed download and retry using the same file'''
    url = Get_CP_URL() + '/movie/reAdd/?id=' + key
    Log('Retry url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return MessageContainer("CouchPotato", L('Downloaded re-added to queue'))

################################################################################

def FailedFindNew(sender, key):
    '''Tell CouchPotato to mark the selected movie as a failed download and find a different file to retry'''
    url = Get_CP_URL() + '/movie/reAdd/?id=' + key + '&failed=true'
    Log('FindNew url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return MessageContainer("CouchPotato", L('Movie re-added to "Wanted" list'))

################################################################################

def SearchResults(sender,query):
    '''Search themoviedb.org for movies using user input, and populate a list with the results'''
    dir = MediaContainer(title2="Search Results", viewGroup="InfoList")
    Log('Search term(s): ' + query)
    
    resultList = XML.ElementFromURL(
        'http://api.themoviedb.org/2.1/Movie.search/en/xml/9b939aee0aaafc12a65bf448e4af9543/' +
        String.Quote(query, usePlus=False))
    
    resultCount = 0
    
    for movie in resultList.xpath('//movie'):
        if resultCount < 10:
            movieTitle = movie.find("name").text
            imdbID = movie.find('imdb_id').text
            releaseDate = movie.find('released').text
            if releaseDate != '1900-01-01':
                try: year = str(Datetime.ParseDate(releaseDate).year)
                except: year = None
            else:
                year = None
            overview = movie.find('overview').text
            try:
                posterUrl = movie.find('images').xpath('image')[0].get('url')
            except:
                posterUrl = 'http://hwcdn.themoviedb.org/images/no-poster.jpg'
            link = movie.find('url').text
            #Log(link)
            try:
                trailerText = HTML.ElementFromURL(link).xpath('//p[@class="trailers"]')[0].text
                if trailerText == "No ":
                    link = ""
            except:
                link = ''    
        
            if year != None:
                Log(movieTitle + ' ('+year+') ' + ' found'),
                dir.Append(Function(PopupDirectoryItem(AddMovieMenu,
                        title=movieTitle, subtitle=year, summary=overview, thumb=Function(GetThumb, url=posterUrl)),
                    id=imdbID, year=year, url=link, provider="TMDB")),
                resultCount = resultCount+1
    return dir
    
################################################################################

def AddMovieMenu(sender, id, year, url="", youtubeID=None, provider=""):
    '''Display an action/context menu for the selected movie'''
    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(AddMovie, title='Add to Wanted list'), id=id, year=year))
    dir.Append(Function(DirectoryItem(QualitySelectMenu, title='Select quality to add'), id=id, year=year))
    if url != "":
        dir.Append(Function(DirectoryItem(TrailerMenu, title='Watch A Trailer'), url=url, provider=provider))
    elif youtubeID:
        dir.Append(Function(DirectoryItem(TrailerMenu, title='Watch A Trailer'), youtubeID=youtubeID, provider=provider))
    else:
        pass
    return dir

################################################################################

def AddMovie(sender, id, year):
    '''Tell CouchPotato to add the selected movie to the wanted list'''
    url = Get_CP_URL() + '/movie/'
    defaultQuality = HTML.ElementFromURL(url, headers=AuthHeader()).xpath('//form[@id="addNew"]/div/select/option')[0].get('value')
    post_values = {'quality' : defaultQuality, 'add' : "Add"}

    # tell CouchPotato to add the given movie
    moviedAdded = HTTP.Request(url+'imdbAdd/?id='+id+'&year='+year, post_values, headers=AuthHeader())
    
    return MessageContainer("CouchPotato", L("Added to Wanted list."))

################################################################################

def ComingSoonMenu(sender):
    dir = MediaContainer(title2="Coming Soon")
    dir.Append(Function(DirectoryItem(ComingToTheatres, title="Coming to Theatres", thumb=R(THEATRE_ICON))))
    dir.Append(Function(DirectoryItem(ComingToBluray, title="Coming to Bluray", thumb=R(BD_ICON))))
    dir.Append(Function(DirectoryItem(NewReleases,"New on DVD/BluRay", thumb=R(ICON))))
    
    return dir

################################################################################

def ComingToTheatres(sender):
    '''Scrape themovieinsider.com for coming soon movies and populate a list'''
    url = 'http://www.themovieinsider.com/movies/coming-soon/'
    dir = MediaContainer(viewGroup="InfoList", title2="Coming Soon", noCache=True)
    comingSoonPage = HTML.ElementFromURL(url, errors='ignore')
    
    for comingMovie in comingSoonPage.xpath('//h3'):
        link = comingMovie.xpath('./a')[0].get('href')
        movieName = comingMovie.xpath('./a')[0].text
        #Log('Found - Coming Soon: '+movieName+' : '+ link)
        try: posterUrl = HTML.ElementFromURL(link,errors='ignore').xpath('//img[@id="poster"]')[0].get('src')
        except: posterUrl = 'http://hwcdn.themoviedb.org/images/no-poster.jpg'
        movieInfoPage = HTML.ElementFromURL(link, errors='ignore')
        movieReleaseDate = movieInfoPage.xpath('//table[@id="profileData"]/tr/td/a')[0].text
        movieYear = movieInfoPage.xpath('//table[@id="profileData"]/tr/td/a')[1].text
        try:
            movieOverview = movieInfoPage.xpath('//div[@id="synopsis"]/span')[0].text
        except:
            movieOverview = ''
        try:
            imdbLink = movieInfoPage.xpath('//div[@id="relatedLinks"]/ul/li/a')[0].get('href')
            imdbID = str(imdbLink)[26:-1]
        except:
            continue
        #Log('imdbID: ' + imdbID)
        dir.Append(Function(PopupDirectoryItem(AddMovieMenu,
                title=(movieName+' ('+movieYear+')'),
                subtitle=('Coming: '+movieReleaseDate+', '+movieYear),
                summary = movieOverview,
                thumb = Function(GetThumb, url=posterUrl)),
            id=imdbID, year=movieYear, url=link, provider="MovieInsider"))
        
    return dir

################################################################################

def ComingToBluray(sender):
    '''Scrape themovieinsider.com for coming soon movies and populate a list'''
    url = 'http://www.themovieinsider.com/blu-rays/coming-soon/'
    dir = MediaContainer(viewGroup="InfoList", title2="Coming Soon", noCache=True)
    comingSoonPage = HTML.ElementFromURL(url, errors='ignore')
    
    for comingMovie in comingSoonPage.xpath('//h3'):
        link = comingMovie.xpath('./a')[0].get('href')
        movieName = comingMovie.xpath('./a')[0].text
        #Log('Found - Coming Soon: '+movieName+' : '+ link)
        try: posterUrl = HTML.ElementFromURL(link,errors='ignore').xpath('//img[@id="poster"]')[0].get('src')
        except: posterUrl = 'http://hwcdn.themoviedb.org/images/no-poster.jpg'
        movieInfoPage = HTML.ElementFromURL(link,errors='ignore')
        try:
            BDReleaseDate = movieInfoPage.xpath('//table[@id="profileData"]/tr[2]/td/a')[0].text
        except:
            BDReleaseDate = ""    
        try:
            BDReleaseYear = movieInfoPage.xpath('//table[@id="profileData"]/tr[2]/td/a')[1].text
        except:
            BDReleaseYear = ""
        movieYear = movieInfoPage.xpath('//table[@id="profileData"]/tr/td/a')[1].text
        try:
            movieOverview = movieInfoPage.xpath('//div[@id="synopsis"]/span')[0].text
        except:
            movieOverview = ""
        try:
            imdbLink = movieInfoPage.xpath('//div[@id="relatedLinks"]/ul/li/a')[0].get('href')
            imdbID = str(imdbLink)[26:-1]
        except:
            continue
        #Log('imdbID: ' + imdbID)
        dir.Append(Function(PopupDirectoryItem(AddMovieMenu,
                title=(movieName+' ('+movieYear+')'),
                subtitle=('Coming: '+BDReleaseDate+', '+BDReleaseYear),
                summary = movieOverview,
                thumb = Function(GetThumb, url=posterUrl)),
            id=imdbID, year=movieYear, url=link, provider="MovieInsider"))
        
    return dir

################################################################################

def NewReleases(sender):
    '''Scrape PopularNewReleases.com for recent BluRay releases'''
    url = 'http://popularnewreleases.com/index.php?sort=release-date'
    dir = MediaContainer(viewGroup="InfoList", title2="New Releases", noCache=True)
    newReleasePage = HTML.ElementFromURL(url, errors='ignore')
    
    for movie in newReleasePage.xpath('//table[@class="movie"]'):
        movieTitle = movie.xpath('.//h1[@class="title"]/a')[0].text
        Log('Found - New Release: '+movieTitle)
        try: posterUrl = movie.xpath('.//img[@class="movieart"]')[0].get('src')
        except: posterUrl = 'http://hwcdn.themoviedb.org/images/no-poster.jpg'
        try:
            youtubetrailer=movie.xpath('.//a[@class="trailer-link internal-action-link"]')[0].get('youtubeid')
        except:
            youtubetrailer=None
        Log('YouTubeID: '+str(youtubetrailer))
        try:
            BDReleaseDate = movie.xpath('.//td[@class="on-video"]')[0].text
        except:
            BDReleaseDate = ""    
        movieYear = movie.xpath('.//span[@class="theatrical-release-year"]')[0].text.split('(')[1].split(')')[0]
        Log('Release year: '+movieYear)
        try:
            movieOverview = movie.xpath('.//p[@class="synopsis"]')[0].text
        except:
            movieOverview = ""
        imdbID = movie.xpath('.//a[@class="external-action-link"]')[0].get('href').split('title/tt')[1]
            
        Log('imdbID: ' + imdbID)
        dir.Append(Function(PopupDirectoryItem(AddMovieMenu,
                title=(movieTitle+' ('+movieYear+')'),
                subtitle=('Release: '+BDReleaseDate),
                summary = movieOverview,
                thumb = Function(GetThumb, url=posterUrl)),
            id=imdbID, year=movieYear, youtubeID=youtubetrailer, provider="MovieInsider"))
        
    return dir

################################################################################

def TrailerMenu(sender, url="", youtubeID=None, provider=""):
    '''Display a list of WebVideoItem trailers for the selected movie (coming soon menu and *maybe search menu)'''
        
    cookies = HTTP.GetCookiesForURL('http://www.youtube.com')

    dir = MediaContainer(ViewGroup="InfoList", title2="Trailers", httpCookies=cookies, noCache=True)
       
    if provider == "MovieInsider":
        for trailer in HTML.ElementFromURL(url).xpath('//div[@id="trailer"]/a'):
            trailerID = str(trailer.xpath('div')[0].get('style'))[44:-14]
            trailerThumb = str(trailer.xpath('div')[0].get('style'))[21:-2]
            trailerTitle = trailer.xpath('div/p/ins[@class="icon play"]/parent::p/text()')[0]
            #Log(trailerTitle)
            dir.Append(Function(WebVideoItem(YtPlayVideo,
                    title=trailerTitle,
                    thumb=trailerThumb),
                video_id=trailerID))
    
    elif provider == "TMDB":
        for trailer in HTML.ElementFromURL(url).xpath('//p[@class="trailers"]/a'):
            trailerID = str(trailer.get('href'))[31:-5]
            #Log('TrailerID: '+trailerID)
            thumbUrl = 'http://i2.ytimg.com/vi/'+trailerID+'/default.jpg'
            trailerTitle = trailer.text
            #Log(trailerTitle)
            dir.Append(Function(WebVideoItem(YtPlayVideo,
                    title=trailerTitle,
                    thumb=Function(GetThumb, url=thumbUrl)),
                video_id=trailerID))
            
    elif provider == "PopularNewReleases":
        thumbUrl = 'http://i2.ytimg.com/vi/%s/default.jpg' % youtubeID
        dir.Append(Function(WebVideoItem(YtPlayVideo, title='Trailer',
            thumb=Function(GetThumb, url=thumbUrl)), video_id=youtubeID))

    else: pass
    
    return dir
    
################################################################################

def YtPlayVideo(sender, video_id):
  yt_page = HTTP.Request(YOUTUBE_VIDEO_PAGE % (video_id), cacheTime=1).content

  fmt_url_map = re.findall('"fmt_url_map".+?"([^"]+)', yt_page)[0]
  fmt_url_map = fmt_url_map.replace('\/', '/').split(',')

  fmts = []
  fmts_info = {}

  for f in fmt_url_map:
    (fmt, url) = f.split('|')
    fmts.append(fmt)
    fmts_info[str(fmt)] = url

  index = YOUTUBE_VIDEO_FORMATS.index(Prefs['ytfmt'])
  if YOUTUBE_FMT[index] in fmts:
    fmt = YOUTUBE_FMT[index]
  else:
    for i in reversed( range(0, index+1) ):
      if str(YOUTUBE_FMT[i]) in fmts:
        fmt = YOUTUBE_FMT[i]
        break
      else:
        fmt = 5

  url = fmts_info[str(fmt)]
  return Redirect(url)

################################################################################

def GetThumb(url):
    '''A function to return thumbs.'''
    try:
        data = HTTP.Request(url, cacheTime=CACHE_1MONTH)
        return DataObject(data, 'image/jpeg')
    except:
        return Redirect(R(ICON))
        
################################################################################

def UpdateAvailable():
    '''Check for updates to CouchPotato using the update flag on the webUI'''
    Log('Running function "UpdateAvailable()"')
    url = Get_CP_URL() + '/movie/'
    
    try:
        cpPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0, headers=AuthHeader())
    except:
        Log('Unable to access CouchPotato webserver. Please check plugin preferences.')
        return False
    try:
        Log(cpPage.xpath('//span[@class="updateAvailable git"]')[0].text)
        if cpPage.xpath('//span[@class="updateAvailable git"]')[0].text == 'Update (':
            cpUpdate = True
        else:
            cpUpdate = False
    except:
        cpUpdate = False
    #Log(cpUpdate)
    
    return cpUpdate
    
################################################################################

def UpdateMenu(sender):
    '''Display the CouchPotato Updater popup menu'''
    
    dir = MediaContainer()
    dir.Append(Function(PopupDirectoryItem(UpdateNow, title='Update CouchPotato Now')))
    
    return dir

################################################################################

def UpdateNow(sender):
    '''Tell CouchPotato to run the updater'''
    url = Get_CP_URL()  + '/config/update/'
    try:
        runUpdate = HTTP.Request(url, errors='ignore', headers=AuthHeader()).content
    except:
        pass
    time.sleep(10)
    return MessageContainer('CouchPotato', L('Update completed successfully'))

################################################################################

def Get_CP_URL():
  return 'http://'+Prefs['cpIP']+':'+Prefs['cpPort']

################################################################################

def QualitySelectMenu(sender, id, year):
    '''provide an option to select a quality other than default before adding a movie'''
    
    dir = MediaContainer()
    
    url = Get_CP_URL() + '/movie/'
    for quality in HTML.ElementFromURL(url, headers=AuthHeader()).xpath('//form[@id="addNew"]/div/select/option'):
        value = quality.get('value')
        name = quality.text
        dir.Append(Function(DirectoryItem(AddWithQuality, title=name,
            subtitle='Add movie with '+name+' quality', thumb=R(ICON)), id=id, year=year,
            quality=value))
    
    return dir

################################################################################

def AddWithQuality(sender, id, year, quality):   
    '''tell CouchPotato to add the given movie with the given quality (rather than
        the defaultQuality)'''
    
    url = Get_CP_URL() + '/movie/'
    post_values = {'quality' : quality, 'add' : "Add"}

    # tell CouchPotato to add the given movie
    moviedAdded = HTTP.Request(url+'imdbAdd/?id='+id+'&year='+year, post_values, headers=AuthHeader())
    
    return MessageContainer("CouchPotato", L("Added to Wanted list."))
    
####################################################################################################

def GetMovieSectionID():
    '''Determine what section(s) are Movies in Plex library'''
    
    dir = MediaContainer(title2='Choose Movie section', noCache=True)
    library = HTML.ElementFromURL(Get_PMS_URL()+'/library/sections', cacheTime=0)
    movieSections = []
    for section in library.xpath('//directory'):
        if section.get('type') == 'movie':
            movieSections.append({'title':section.get('title'), 'key':section.get('key')})
    
    if len(movieSections) > 1:
        Log('There are %d sections which contain "movies"' % len(movieSections))
        for section in movieSections:
            dir.Append(Function(DirectoryItem(ForceMovieSection, title=section['title']), sectionID=section['key']))
        return dir
    elif len(movieSections) == 1:
        Log('There is 1 section which contains movies.')
        Dict['MovieSectionID'] = movieSections[0]['key']
        Log('Movie sectionID saved.')
        return MainMenu()
    else:
        return MessageContainer(NAME, L('Could not identify a section of Movies.'))

    return MainMenu()
    
####################################################################################################

def ForceMovieSection(sender, sectionID):
    Log('Section #%s chosen' % sectionID)
    Dict['MovieSectionID'] = sectionID
    Log('Movie sectionID saved.')
    return MainMenu()

####################################################################################################

def Get_PMS_URL():
    return 'http://'+Prefs['pmsIP']+':32400'
    
####################################################################################################

def RecentlyViewedMenu(sender):
    '''retrieve list of recently viewed movies and allow option to delete the files (on an individual basis)'''
    dir = MediaContainer(viewGroup='InfoList', title2='Delete', noCache=True)
    
    recentlyViewedUrl = Get_PMS_URL() + '/library/sections/' + Dict['MovieSectionID'] + '/recentlyViewed'
    recentlyViewed = XML.ElementFromURL(recentlyViewedUrl, cacheTime=0)
    
    archive = True
    
    for movie in recentlyViewed.xpath('//Video'):
        movieName = movie.get('title')
        #Log(str(movieName))
        summary = movie.get('summary')
        #Log(str(summary))
        movieYear = movie.get('year')
        #Log(str(movieYear))
        file = movie.xpath('.//Part')[0].get('file')
        #Log(str(file))
        thumbUrl = movie.get('thumb')
        dir.Append(Function(PopupDirectoryItem(ConfirmDelete, title=movieName +' (%s)' % movieYear,
                subtitle=file, summary = summary,thumb=Function(GetThumbFromPMS, link=thumbUrl)), file=file))
    
    return dir

####################################################################################################

def GetThumbFromPMS(link):
    try:
        data = HTTP.Request(Get_PMS_URL() + link, cacheTime=CACHE_1MONTH).content
        return DataObject(data, 'image/jpeg')
    except:
        return Redirect(R(ICON))

####################################################################################################

def ConfirmDelete(sender, file):

    dir = MediaContainer()
    dir.Append(Function(DirectoryItem(DeleteFile, title='Delete this movie?'), file=file))
    return dir

####################################################################################################

def DeleteFile(sender, file):
    
    ### delete the given episode ###
    os.remove(file)
    
    return MessageContainer(NAME, L('Episode deleted from system.'+
        ' Changes will be reflected after the next Library Update.'))


