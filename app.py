import os, time, requests
from flask import Flask, json
from init import get_driver
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False

def return_json(obj):
    response = app.response_class(json.dumps(obj, sort_keys=False), mimetype=app.config['JSONIFY_MIMETYPE'])
    return response

driver = get_driver()
@app.route('/video/<string:id>/<int:chapter>')
def getVideoByAnimeId(id, chapter):
    start_time = time.time()
    driver.get('https://jkanime.net/{}/{}'.format(id, chapter))
    player_url = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[3]/div[1]/div[2]/div[1]/center/div/div/iframe').get_attribute('src')
    driver.get(player_url)
    video = driver.find_element_by_xpath('/html/body/div[1]/video/source').get_attribute('src')
    print("--- %s seconds ---" % (time.time() - start_time))
    return return_json({'video':video})

@app.route('/info/<string:id>')
def getAnimeInfoById(id):
    start_time = time.time()
    page = requests.get('https://jkanime.net/{}'.format(id))
    body = BeautifulSoup(page.content, 'html.parser')
    info = body.findAll('div', {'class':'info-field'})
    anime = {}
    anime['name'] = body.find('div', {'class':'info-content'}).find('h2').getText()
    anime['poster'] = body.findAll('img')[1].get('src')
    anime['type'] = info[0].find('span', {'class':'info-value'}).getText()
    anime['synopsis'] = info[7].find('p').getText()[10:]
    anime['genre'] = info[1].find('span', {'class':'info-value'}).find('a').getText()
    anime['episodes'] = info[3].find('span', {'class':'info-value'}).getText()
    anime['duration'] = info[4].find('span', {'class':'info-value'}).getText()
    date =  info[5].find('span', {'class':'info-value'}).getText().replace('  ', '').replace('\n','')
    anime['startDate'] = date
    if date.find(' a '):
        anime['startDate'] = date[:date.find(' a ')]
        anime['finishDate'] = date[date.find(' a ')+3:]
    anime['state'] = info[6].find('span', {'class':'info-value'}).find('b').getText()
    print("--- %s seconds ---" % (time.time() - start_time))
    return return_json(anime)

@app.route("/")
def index():
    default_dict = {"message" : "🏴‍☠️🦜"}
    return return_json(default_dict)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000, debug=True)