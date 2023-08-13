FROM python:3.11

ENV MQTT_URL localhost
ENV MQTT_PORT 1883
ENV MQTT_USER mqtt_user
ENV MQTT_PASSWORD mqtt_password
ENV WEB_USER web_user
ENV WEB_PASSWORD web_password

ENV DEBIAN_FRONTEND noninteractive
ENV GECKODRIVER_VER v0.33.0
ENV FIREFOX_VER 116.0
ENV MYTIMEZONE America/Montreal

ENV PLATFORM docker
 
#Selenium Firefox https://takac.dev/example-of-selenium-with-python-on-docker-with-latest-firefox/
RUN set -x \
   && apt update \
   && apt upgrade -y \
   && apt install -y \
       firefox-esr \
   && pip install  \
       requests \
       selenium
 
# Add latest FireFox
RUN set -x \
   && apt install -y \
       libx11-xcb1 \
       libdbus-glib-1-2 \
   && curl -sSLO https://download-installer.cdn.mozilla.net/pub/firefox/releases/${FIREFOX_VER}/linux-x86_64/en-US/firefox-${FIREFOX_VER}.tar.bz2 \
   && tar -jxf firefox-* \
   && mv firefox /opt/ \
   && chmod 755 /opt/firefox \
   && chmod 755 /opt/firefox/firefox
  
# Add geckodriver
RUN set -x \
   && curl -sSLO https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VER}/geckodriver-${GECKODRIVER_VER}-linux64.tar.gz \
   && tar zxf geckodriver-*.tar.gz \
   && mv geckodriver /usr/bin/

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r ./requirements.txt

COPY . .

#-u is necessary to get logs of the python script in docker logs
CMD  ["python3", "-u", "./getCreditData.py"]
