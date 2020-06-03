import os, time, requests, asyncio, aiohttp
from flask import Flask, json
#from init import driver
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False

def return_json(obj):
    response = app.response_class(json.dumps(obj, sort_keys=False), mimetype=app.config['JSONIFY_MIMETYPE'])
    return response

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
    src = vid_script[1]
    player_url = src[src.find('src=')+5:src.find(' width')-1]
    #driver.get('https://jkanime.net/{}/{}'.format(id, chapter))
    #player_url = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[3]/div[1]/div[2]/div[1]/center/div/div/iframe').get_attribute('src')
    driver.get(player_url)
    video = driver.find_element_by_xpath('/html/body/div[1]/video/source').get_attribute('src')
    return video

def getAnimeInfo(id):
    page = requests.get('https://jkanime.net/{}'.format(id))
    body = BeautifulSoup(page.content, 'html.parser')
    info = body.findAll('div', {'class':'info-field'})
    name = body.find('div', {'class':'info-content'}).find('h2').getText()
    poster = body.findAll('img')[1].get('src')
    type = info[0].find('span', {'class':'info-value'}).getText()
    synopsis = info[7].find('p').getText()[10:-1]
    genres = info[1].find('span', {'class':'info-value'}).findAll('a')
    tmpList = []
    for genre in genres:
        tmpList.append(genre.getText())
    #episodes = info[3].find('span', {'class':'info-value'}).getText()
    episodeText = body.find('div', {'class':'navigation'}).findAll('a')[-1].getText()
    episodes = episodeText[episodeText.find("- ")+2:]
    duration = info[4].find('span', {'class':'info-value'}).getText()[:info[4].find('span', {'class':'info-value'}).getText().find(' p')]
    date =  info[5].find('span', {'class':'info-value'}).getText().replace('  ', '').replace('\n','')
    startDate = date
    finishDate = None
    state = info[6].find('span', {'class':'info-value'}).find('b').getText()
    if 'Concluido' in state:
        startDate = date[:date.find(' a ')]
        finishDate = date[date.find(' a ')+3:]
    return (name, poster, type, synopsis, tmpList, episodes, duration, startDate, finishDate, state)

@app.route('/video/<string:id>/all')
def getVideosByAnimeId(id):
    start_time = time.time()
    episodes = int(getAnimeInfo(id)[5])
    videos = []
    for i in range(episodes):
        videoDict = {}
        video = getEpisodeVideo(id, i+1)
        videoDict['episode'] = str(i+1)
        videoDict['url'] = video
        videos.append(videoDict)
    print("--- %s seconds ---" % (time.time() - start_time))
    return return_json({'videos':videos})

@app.route('/video/<string:id>/<int:chapter>')
def getVideoByAnimeId(id, chapter):
    start_time = time.time()
    video = getEpisodeVideo(id, chapter)
    print("--- %s seconds ---" % (time.time() - start_time))
    return return_json({'video':video})

@app.route('/info/<string:id>')
def getAnimeInfoById(id):
    start_time = time.time()
    info = getAnimeInfo(id)
    anime = {'name':info[0],'poster':info[1],'type':info[2],'synopsis':info[3],'genres':info[4],'episodes':info[5],'duration':info[6],'startDate':info[7],'finishDate':info[8],'state':info[9]}
    print("--- %s seconds ---" % (time.time() - start_time))
    return return_json(anime)

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
        episodes = getAnimeInfo(id)[5]
        state = 'En emision'
    synopsis = entry.find('div', {'id':'ainfo'}).find('p').getText()
    return (id, title, poster, type, synopsis, episodes, state)

@app.route('/search/<string:name>')
def searchAnime(name):
    animes = []
    entries = search(name, 1)
    for entry in entries:
        info = getData(entry)
        anime = {'id':info[0], 'name':info[1],'poster':info[2],'type':info[3],'synopsis':info[4],'episodes':info[5],'state':info[6]}
        animes.append(anime)
    return return_json(animes)

@app.route("/")
def index():
    default_dict = {"message" : "🏴‍☠️🦜"}
    return return_json(default_dict)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000, debug=True)