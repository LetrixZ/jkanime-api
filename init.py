import os
from selenium import webdriver

def get_driver():
    options = webdriver.ChromeOptions()
    prefs = {'profile.default_content_setting_values': {'cookies': 2, 'images': 2, 'javascript': 1, 
                                'plugins': 2, 'popups': 2, 'geolocation': 2, 
                                'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2, 
                                'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 
                                'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 
                                'ppapi_broker': 2, 'automatic_downloads': 2, 'midi_sysex': 2, 
                                'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2, 
                                'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 
                                'durable_storage': 2}}
    options.add_experimental_option('prefs', prefs)
    #options.add_argument("--headless")
    #options.add_extension("ublock.crx")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=480,640")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),chrome_options=options)
    #driver = webdriver.Chrome(chrome_options=options)
    #driver.minimize_window()
    return driver

driver = get_driver()