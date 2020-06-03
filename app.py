import os, time
from flask import Flask, json
from init import get_driver

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False

def return_json(obj):
    response = app.response_class(json.dumps(obj, sort_keys=False), mimetype=app.config['JSONIFY_MIMETYPE'])
    return response

driver = get_driver()
@app.route('/getVideo/<string:id>/<int:chapter>')
def getVideoByAnimeId(id, chapter):
    start_time = time.time()
    driver.get('https://jkanime.net/{}/{}'.format(id, chapter))
    player_url = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[3]/div[1]/div[2]/div[1]/center/div/div/iframe').get_attribute('src')
    driver.get(player_url)
    video = driver.find_element_by_xpath('/html/body/div[1]/video/source').get_attribute('src')
    print("--- %s seconds ---" % (time.time() - start_time))
    return return_json({'video':video,'time':(time.time() - start_time)})

@app.route("/")
def index():
    default_dict = {"message" : "🏴‍☠️🦜"}
    return return_json(default_dict)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000, debug=True)