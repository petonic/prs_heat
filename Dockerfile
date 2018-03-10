FROM resin/odroid-xu4-python:3.5
COPY requirements.txt /
RUN pip install -r requirements.txt
ADD . /code
WORKDIR /code
CMD [ "/usr/local/bin/python", "-u", "heat.py" 80 ]
