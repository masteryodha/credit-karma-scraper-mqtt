import time
import os
import re
import pytz
import datetime
import argparse
import schedule
import paho.mqtt.client as mqttClient
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

client = mqttClient.Client()

#Se connecter sur MQTT
def on_connect_mqtt(client, userdata, flags, rc):
    print('MQTT CONNECT - CONNACK received with code %d.' % (rc))

def connectToMQTT (mqtt_address, mqtt_port, mqtt_user, mqtt_password):
    
    client.username_pw_set(mqtt_user, password=str(mqtt_password))
    client.on_connect = on_connect_mqtt
    client.connect(mqtt_address, mqtt_port)
    client.loop_start()

def _login(driver, username: str, password: str):
    print('login...')
    url = "https://www.creditkarma.ca/credit"

    driver.get(url)
    
    #Attendre que le site load complètement.
    print('Waiting 5 seconds for the website to load')
    time.sleep(5)

    #Pour une raison weird, le site change entre username et emailAddress parfois.  On le gère donc avec une exception
    try:
        elem=driver.find_element(By.NAME, "emailAddress")
        elem.send_keys(username)
    except:
        elem=driver.find_element(By.NAME, "username")
        elem.send_keys(username)
       
    elem = driver.find_element(By.NAME, "password")
    elem.send_keys(password)
    
    elem.send_keys(Keys.RETURN)

    #Wait for the login to happen
    print('Waiting 15 seconds for the login to complete')
    time.sleep(15)
    print('**** Login successful')

def _getCredit(driver):
    url = "https://www.creditkarma.ca/credit"
    print('Get credit from {}'.format(url))

    driver.get(url)
    
    #Attendre que le site load complètement.
    time.sleep(10)
    
    #data-testid="credit-score-card-score"
    elem=driver.find_element(By.XPATH, "//p[@data-testid='credit-score-card-score']")
    credit_score = elem.get_attribute("innerHTML")
    print('Credit Score from Transunion : {} / 900'. format(credit_score))
    client.publish('creditkarma/credit_score', credit_score, retain=True)
    client.publish('creditkarma/date_maj', str(datetime.datetime.now(tz=pytz.timezone(args.MYTIMEZONE))), retain=True)

    attributes = ['on-time-payment-history', 'credit-utilisation',
                   'derogatory-marks', 'hard-inquiries',
                   'age-of-credit-extended', 'total-accounts']
    
    for attr in attributes:
        elem=driver.find_element(By.XPATH, "//p[@data-testid='credit-factor-card-{}-name']".format(attr))
        name = _clean_html_from_text(elem.get_attribute("innerHTML"))
        elem=driver.find_element(By.XPATH, "//p[@data-testid='credit-factor-card-{}-value']".format(attr))
        value = _clean_html_from_text(elem.get_attribute("innerHTML"))
        elem=driver.find_element(By.XPATH, "//p[@data-testid='credit-factor-card-{}-description']".format(attr))
        description = _clean_html_from_text(elem.get_attribute("innerHTML"))
    
        print('{} : {}. {}'. format(name, value, description))
        client.publish('creditkarma/factors/{}'.format(name), value, retain=True)
        client.publish('creditkarma/factors/{}_desc'.format(name), description, retain=True)


def _getOpenedAccountsFromReport (driver):
    url = "https://www.creditkarma.ca/report"
    print('Get accounts from {}'.format(url))

    driver.get(url)
    
    #Attendre que le site load complètement.
    time.sleep(10)
    
    #Kill the popup
    print('Killing the popup if one')
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()

    #data-testid="credit-score-card-score"
    elems=driver.find_elements(By.TAG_NAME, "section")
    
    for index, elem in enumerate(elems):
        #print(elem.get_attribute("innerHTML"))
        
        try: 
            title_elem = elem.find_element(By.TAG_NAME, "h1")
            title = _clean_html_from_text(title_elem.get_attribute("innerHTML"))
            print('***** Section : {} *****'.format(title))

            all_hrefs = elem.find_elements(By.TAG_NAME, "a")
            for index2, href in enumerate(all_hrefs):

                account = _clean_html_from_text(href.get_attribute("innerHTML"))
                if (account == "") :
                    account = title

                parent = _findFirstParentThatIsADiv(href)
                elem_montant = parent.find_element(By.TAG_NAME, "span")
                montant = _clean_html_from_text(elem_montant.get_attribute("innerHTML"))
                print('Account : {}_{}{}.  Montant : {}$'.format(account, index, index2, montant))
                client.publish('creditkarma/accounts/{}_{}{}'.format(account, index, index2), montant, retain=True)

        except:
            #Nothing to do, it's a section we don't need
            print('invalid section')


def _findFirstParentThatIsADiv (element):
    found = False;
    i = 0;

    while not found:
        #Find parent
        parent = element.find_element(By.XPATH, '..')
        
        if (parent.tag_name == 'div'):
            found = True

        element = parent
    
        i = i+1
        if (i == 4):
            found = True
    
    return element;
    
    
def _clean_html_from_text(text: str):
    CLEANR = re.compile('<.*?>') 

    cleanText = re.sub(CLEANR, '', text)
    
    #Remove &nbsp; and $
    cleanText = cleanText.replace('&nbsp;', '')
    cleanText = cleanText.replace('$', '')
    
    return cleanText;

def _getDataFromWebsite (username: str, password: str, headless: bool):
    options = Options()
    
    if (os.environ.get('PLATFORM')) == "docker":
        options.binary_location = r'/opt/firefox/firefox'
    else :
        options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'


    if (headless) :
        #options.headless = True  #deprecated
        options.add_argument('-headless')

    driver = webdriver.Firefox(options=options)

    _login(driver, username, password)
    
    print('Connecting to MQTT')
    connectToMQTT(args.MQTT_URL, int(args.MQTT_PORT), args.MQTT_USER, args.MQTT_PASSWORD)

    _getCredit(driver)
    _getOpenedAccountsFromReport(driver)

    driver.close()
    client.disconnect()


def printHearbeat():
    print("The cron in {} is still alive and python is working...".format(os.environ.get('PLATFORM')))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape Borrowell website to get credit scores and factor')
    parser.add_argument('--MQTT_URL', dest='MQTT_URL', default=os.environ.get('MQTT_URL'))
    parser.add_argument('--MQTT_PORT', dest='MQTT_PORT', default=os.environ.get('MQTT_PORT'))
    parser.add_argument('--MQTT_USER', dest='MQTT_USER', default=os.environ.get('MQTT_USER'))
    parser.add_argument('--MQTT_PASSWORD', dest='MQTT_PASSWORD', default=os.environ.get('MQTT_PASSWORD'))
    parser.add_argument('--WEB_USER', dest='WEB_USER', default=os.environ.get('WEB_USER'))
    parser.add_argument('--WEB_PASSWORD', dest='WEB_PASSWORD', default=os.environ.get('WEB_PASSWORD'))
    parser.add_argument('--MYTIMEZONE', dest='MYTIMEZONE', default=os.environ.get('MYTIMEZONE'))

    args = parser.parse_args()

    print('***** ARGUMENTS CREDIT-KARMA *****')
    print('* MQTT_URL      : {}'.format(args.MQTT_URL))
    print('* MQTT_PORT     : {}'.format(args.MQTT_PORT))
    print('* MQTT_USER     : {}'.format(args.MQTT_USER))
    print('* MQTT_PASSWORD : {}'.format(args.MQTT_PASSWORD))
    print('* WEB_USER      : {}'.format(args.WEB_USER))
    print('* WEB_PASSWORD  : {}*********'.format(args.WEB_PASSWORD[0:3]))
    print('* MYTIMEZONE    : {}'.format(args.MYTIMEZONE))
    print('**********************************')
    print('')

    print("Run the CREDIT KARMA scraper now")
    _getDataFromWebsite(username = args.WEB_USER, password = args.WEB_PASSWORD, headless = True)

    print("")
    print("")
    print("------------------------------------------------------------------------------------------")
    schedule.every(71).hours.do(_getDataFromWebsite, username = args.WEB_USER, password = args.WEB_PASSWORD, headless = True)
    print("Scheduled the CREDIT KARMA scraper every 71 hours from now")
    schedule.every(1).hours.do(printHearbeat)
    print("Scheduled Heartbeat every 1 hour from now")
    print("------------------------------------------------------------------------------------------")
    print("")

    while True:
        schedule.run_pending()
        time.sleep(1) #seconds

