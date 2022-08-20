FROM nvidia/cuda:10.2-devel-ubuntu18.04

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update && apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y libx264-dev
RUN apt-get update && apt install -y python3.8 ffmpeg libsm6 libxext6 libgl1-mesa-glx
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.8 10
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 10
RUN apt-get update && apt install -y python3-pip
RUN apt-get update && apt install -y python3-opencv
RUN pip3 install --upgrade pip
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn
RUN mkdir /app/video
RUN mkdir /app/tmp
COPY src /app/src
RUN chmod -R 777 /app/src
COPY data_ /app/data_
COPY models /app/models
EXPOSE 5000 15672 5672

# RUN apt-get install -y curl
# COPY ./entrypoint.sh /usr/bin/entrypoint.sh
# ENTRYPOINT [ "entrypoint.sh" ]
CMD python3 src/main.py
#  --worker-class 'gthread'
# WORKDIR /app/src
# CMD gunicorn -b :8282 --timeout 120 -k gevent  --workers 1 --access-logfile - --error-logfile - main:app
