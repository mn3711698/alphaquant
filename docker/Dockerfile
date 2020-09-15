FROM python:3.7.4

RUN mkdir /app
RUN apt-get update
RUN apt-get -y install vim
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt
WORKDIR /alphaquant

CMD ["/bin/bash"]
