import os, time, requests, asyncio, aiohttp, re, concurrent.futures
from flask import Flask, json
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False

def returnJson(obj):
    response = app.response_class(json.dumps(obj, sort_keys=False), mimetype=app.config['JSONIFY_MIMETYPE'])
    return response

"""
def getBodies(urlList):
    bodies = []
    async def get(url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url) as response:
                    resp = await response.read()
                    #print("Successfully got url {} with response of length {}.".format(url, len(resp)))
                    if len(resp) > 1000:
                        bodies.append(resp)
        except Exception as e:
            print("Unable to get url {} due to {}.".format(url, e.__class__))
    async def main(urls, amount):
        ret = await asyncio.gather(*[get(url) for url in urls])
        print("Finalized all. ret is a list of len {} outputs.".format(len(ret)))
    urls = urlList
    amount = len(urls)
    start = time.time()
    asyncio.run(main(urls, amount))
    end = time.time()
    print("Took {} seconds to pull {} websites.".format(end - start, amount))
    return bodies
"""

def getBodies(urlList):
    def load_url(url, timeout):
        return requests.get(url, timeout = timeout)
    bodies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {executor.submit(load_url, url, 60): url for url in urlList}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            data = future.result()
            bodies.append(data.content)
    return bodies

def getEpisodeVideo(id, chapter):
    from init import driver
    page = requests.get('https://jkanime.net/{}/{}'.format(id, chapter))
    soup = BeautifulSoup(page.content, 'html.parser')
    scripts = soup.findAll('script')
    vid_script = ''
    for script in scripts:
        if 'var video = [];' in str(script):
            vid_script = str(script)
    vid_script = vid_script.replace('  ', '')
    vid_script = vid_script[23:vid_script.find('var video_data = video')].split('video')
    try:
        src = vid_script[1]
    except IndexError:
        return None
    player_url = src[src.find('src=')+5:src.find(' width')-1]
    driver.get(player_url)
    video = driver.find_element_by_xpath('/html/body/div[1]/video/source').get_attribute('src')
    return video

def getAnimeInfo(body):
    info = body.findAll('div', {'class':'info-field'})
    if body.find('div', {'class':'info-content'}) is None:
        print(body)
    name = body.find('div', {'class':'info-content'}).find('h2').getText()
    poster = body.findAll('img')[1].get('src')
    id = body.find('meta', {'property':'og:url'}).get('content')[20:-1]
    type = info[0].find('span', {'class':'info-value'}).getText()
    synopsis = info[7].find('p').getText()[10:-1]
    genres = info[1].find('span', {'class':'info-value'}).findAll('a')
    tmpList = []
    for genre in genres:
        tmpList.append(genre.getText())
    try:
        episodeText = body.find('div', {'class':'navigation'}).findAll('a')[-1].getText()
        episodes = episodeText[episodeText.find("- ")+2:]
    except IndexError:
        episodes = "0"
    unique = None
    if body.find('div', {'class':'lista_title_uniq'}):
        try:
            unique = body.find('div', {'class':'listbox'}).get('a').get('href')[20:-1].replace(id+'/','')
        except AttributeError:
            unique = None
    duration = info[4].find('span', {'class':'info-value'}).getText().replace('.','')
    if ' p' in duration:
        duration = duration[:duration.find(' p')]
    date =  info[5].find('span', {'class':'info-value'}).getText().replace('  ', '').replace('\n','')
    startDate = date
    finishDate = None
    state = info[6].find('span', {'class':'info-value'}).find('b').getText()
    if 'Concluido' in state:
        startDate = date[:date.find(' a ')]
        finishDate = date[date.find(' a ')+3:]
    return (name, poster, type, synopsis, tmpList, episodes, duration, startDate, finishDate, state, id, unique)

def getBody(id):
    page = requests.get('https://jkanime.net/{}'.format(id))
    body = BeautifulSoup(page.content, 'html.parser')
    return body

@app.route('/letter/<string:letter>/<int:pageNumber>/')
def getAnimeLetters(letter, pageNumber):
    page = requests.get('https://jkanime.net/letra/{}/{}/'.format(letter, pageNumber))
    body = BeautifulSoup(page.content, 'html.parser')
    div = body.findAll('div', {'class':'portada-box'})
    links = []
    for anime in div:
        links.append(anime.find('a', {'class':'let-link'}).get('href'))
    bodies = getBodies(links)
    print('DIV: {} - LINKS: {} - BODIES: {}'.format(len(div),len(links),len(bodies)))
    animes = []
    for bod in bodies:
        soup = BeautifulSoup(bod, 'html.parser')
        info = getAnimeInfo(soup)
        episodeList = []
        #for i in range(int(info[5])):
        #    video = getEpisodeVideo(info[10], i+1)
        #    episodeList.append({'episode':i+1,'video':video})
        anime = {'name':info[0],'poster':info[1],'type':info[2],'synopsis':info[3],'genres':info[4],'episodes':info[5],'episodeList':episodeList,'duration':info[6],'startDate':info[7],'finishDate':info[8],'state':info[9]}
        obj = {'id':info[10]}
        insert = lambda _dict, obj, pos: {k: v for k, v in (list(_dict.items())[:pos] + list(obj.items()) + list(_dict.items())[pos:])}
        anime = insert(anime, obj, 0)
        animes.append(anime)
    return returnJson(animes)

@app.route('/video/<string:id>/all/')
def getVideosByAnimeId(id):
    start_time = time.time()
    info = getAnimeInfo(id)
    episodes = int(info[5])
    videos = []
    if not info[11]:
        for i in range(episodes):
            videoDict = {}
            video = getEpisodeVideo(id, i+1)
            videoDict['episode'] = str(i+1)
            videoDict['url'] = video
            videos.append(videoDict)
    else:
        videoDict = {}
        video = getEpisodeVideo(id, info[11])
        videoDict['episode'] = str(i+1)
        videoDict['url'] = video
        videos.append(videoDict)
    print("--- %s seconds ---" % (time.time() - start_time))
    return returnJson({'videos':videos})

@app.route('/video/<string:id>/<string:chapter>/')
def getVideoByAnimeId(id, chapter):
    start_time = time.time()
    video = getEpisodeVideo(id, chapter)
    print("--- %s seconds ---" % (time.time() - start_time))
    return returnJson({'video':video})

@app.route('/info/<string:id>/')
def getAnimeInfoById(id):
    start_time = time.time()
    info = getAnimeInfo(getBody(id))
    anime = {'name':info[0],'poster':info[1],'type':info[2],'synopsis':info[3],'genres':info[4],'episodes':info[5],'duration':info[6],'startDate':info[7],'finishDate':info[8],'state':info[9]}
    print("--- %s seconds ---" % (time.time() - start_time))
    return returnJson(anime)

def search(name, page):
    page = requests.get('https://jkanime.net/buscar/{}/{}'.format(name, page))
    soup = BeautifulSoup(page.content, 'html.parser')
    entries = soup.findAll('div', {'class':'portada-box'})
    if soup.find('a', {'class':'nav-next'}):
        number = soup.find('a', {'class':'nav-next'}).get('href')
        number = int(number[number[27:].find('/')+28:-1])
        entries += search(name, number)
    return entries

def getData(entry):
    title = entry.find('h2', {'class':'portada-title'}).find('a').get('title')
    id = entry.find('h2', {'class':'portada-title'}).find('a').get('href')[20:-1]
    poster = entry.find('img').get('src')
    typeText = entry.find('span', {'class':'eps-num'}).getText()
    type = typeText[:typeText.find('/')-1]
    episodes = typeText[typeText.find('/')+2:]
    state = 'Concluido'
    if 'Desc' in episodes:
        episodes = getAnimeInfo(getBody(id))[5]
        state = 'En emision'
    else:
        episodes = re.findall('\d+', typeText)
        episodes = int(episodes[0])
    synopsis = entry.find('div', {'id':'ainfo'}).find('p').getText()
    return (id, title, poster, type, synopsis, episodes, state)

@app.route('/search/<string:name>/')
def searchAnime(name):
    animes = []
    entries = search(name, 1)
    for entry in entries:
        info = getData(entry)
        anime = {'id':info[0], 'name':info[1],'poster':info[2],'type':info[3],'synopsis':info[4],'episodes':info[5],'state':info[6]}
        animes.append(anime)
    return returnJson(animes)

def getSchedule(day):
    page = requests.get('https://jkanime.net/horario/')
    body = BeautifulSoup(page.content, 'html.parser')
    animes = body.find('div', {'class':'app-layout'}).findAll('div', {'class':'semana'})[day-1].findAll('div')
    links = []
    for anime in animes:
        links.append(anime.find('a').get('href'))
    bodies = getBodies(links)
    schedule = []
    for body in bodies:
        soup =  BeautifulSoup(body, 'html.parser')
        info = getAnimeInfo(soup)
        anime = {'id':info[10],'name':info[0],'poster':info[1],'type':info[2],'synopsis':info[3],'genres':info[4],'episodes':info[5],
        'duration':info[6],'startDate':info[7],'finishDate':info[8],'state':info[9]}
        schedule.append(anime)
    return schedule

@app.route('/schedule/<int:day>/')
def getScheduleByDay(day):
    if day > 7 or day < 1:
        return returnJson({'schedule':''})
    return returnJson(getSchedule(day))

@app.errorhandler(404)
def page_not_found(e):
    return returnJson({'message':'404 - page not found'})

@app.route("/")
def index():
    default_dict = {"message" : "🏴‍☠️🦜"}
    return returnJson(default_dict)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000, debug=False)