# Description
Intuit Credit Karma offers free credit scores, reports and insights
The information seems to come from TransUnion

The website is accessible from https://www.creditkarma.ca


This project is juste a scraper for the website to get the credit scores, the different factors and the opened accounts.  These informations get published on a MQTT server to add them in Home Assistant.

it srapes https://www.creditkarma.ca/credit and https://www.creditkarma.ca/report to get the different information


Upon start up, the script will get the information a first time and then create 2 schedule (Defined in getCreditData.py) :
The first one is to print a heartbeat every 10 minutes.
The second one is the actual scraper and will run every 72 hours from the time the docker is started


# Pre-requisite
Go to https://www.creditkarma.ca/ and create an account.


# Executing
You can either execute it manually with python or run it in a docker


## Command line
pip install -r requirements.txt
You also need to install firefox and GeckoDriver.
The version of firefox and GeckoDriver needs to match.  Check the docker ENV variables to see which version it uses


```
python .\getCreditData.py --MQTT_URL localhost --MQTT_PORT 1883 --MQTT_USER my_mqtt_user --MQTT_PASSWORD my_mqtt_password --WEB_USER my_creditkarma_user --WEB_PASSWORD my_creditkarma_password  --MYTIMEZONE America/Montreal
```


## Docker
Build the docker from the clone repository
```
docker build -t credit-karma .
```

or you can user the one already build on dockerhub : https://hub.docker.com/repository/docker/mikamap/credit-karma

Parameters : 
| Parameters | Mandatory |  Description |
|:-----|:--------:|:--------:|
| MQTT_URL   | Yes | IP of the MQTT server.  Example : 192.178.0.20|
| MQTT_PORT   | Yes |  Port of the MQTT server.  Example : 1883  |
| MQTT_USER   | Yes | User of MQTT |
| MQTT_PASSWORD | Yes  | Password of MQTT |
| WEB_USER   | Yes | User on credit Karma |
| WEB_PASSWORD | Yes  | Password on credit Karma |
| MYTIMEZONE | No  | The timezone for formatting the dates.  Default value : America/Montreal |
| GECKODRIVER_VER | No  | Version of geckoDriver.  Default value : 0.33.0.  This needs to match the value of Firefox |
| FIREFOX_VER | No  | Version of firefox to use for selenium.  Default value : 116.0 |



Run with the necessary parameters : 
```
docker run -d --rm --name credit-creditkarma -e "MQTT_URL=localhost" -e "MQTT_PORT=1883" -e "MQTT_USER=my_mqtt_user" -e "MQTT_PASSWORD=my_mqtt_password" -e "WEB_USER=my_creditkarma_user" -e "WEB_PASSWORD=my_creditkarma_password" credit-creditkarma
```



# Home Assistant

All my mqtt sensor config is in a mqtt.yaml file.

configuration.yaml
```
...
mqtt: !include mqtt.yaml
...
```


And my mqtt.yaml file : 
```
########################################################
##
##  C R E D I T 
##
##  creditkarma
##
########################################################

## creditkarma
  - name: creditkarma_credit_score
    state_topic: "creditkarma/credit_score"
    unique_id: "creditkarma_credit_score"

  - name: creditkarma_credit_score_maj
    state_topic: "creditkarma/date_maj"
    unique_id: "creditkarma_credit_score_maj"


### Factors
  - name: creditkarma_factor_missed_payments
    state_topic: "creditkarma/factors/Missed payments"
    unique_id: "creditkarma_factor_missed_payments"

  - name: creditkarma_factor_credit_utilization
    state_topic: "creditkarma/factors/Credit utilization"
    unique_id: "creditkarma_factor_credit_utilization"
    
  - name: creditkarma_factor_derogatory_marks
    state_topic: "creditkarma/factors/Derogatory marks"
    unique_id: "creditkarma_factor_derogatory_marks"

  - name: creditkarma_factor_credit_age
    state_topic: "creditkarma/factors/Avg. credit age"
    unique_id: "creditkarma_factor_credit_age"

  - name: creditkarma_factor_total_accounts
    state_topic: "creditkarma/factors/Total accounts"
    unique_id: "creditkarma_factor_total_accounts"

  - name: creditkarma_factor_hard_inquiries
    state_topic: "creditkarma/factors/Hard inquiries"
    unique_id: "creditkarma_factor_hard_inquiries"

### Accounts
  - name: creditkarma_account_tangerine
    state_topic: "creditkarma/accounts/TANGERINE_0"
    unique_id: "creditkarma_account_tangerine"

  - name: creditkarma_account_pc_optimum
    state_topic: "creditkarma/accounts/PRESIDENTS CHOICE MC_1"
    unique_id: "creditkarma_account_pc_optimum"

  - name: creditkarma_account_bmo_auto
    state_topic: "creditkarma/accounts/BMO 1111_2"
    unique_id: "creditkarma_account_bmo_auto"

  - name: creditkarma_account_mortgage
    state_topic: "creditkarma/accounts/Undisclosed Mortgage Provider_10"
    unique_id: "creditkarma_account_mortgage"
```
