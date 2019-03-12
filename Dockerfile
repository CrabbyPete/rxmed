FROM ubuntu:18.04

# This simply identifies the maintainer of the container
MAINTAINER pete.douma@gmail.com

# each `RUN` statement applies a change to the container by executing
# the command in the container. Here we first update the package manager
# Then install a few external dependencies (python, pip, git and the
# mock library).
RUN apt-get update
RUN apt-get install -y \
	python3.6 \
	python3-pip\
	python3-dev \
	libevent-dev \
	build-essential \
	python-psycopg2 \
	uwsgi


ADD ./requirements.txt /app/requirements.txt
ADD ./wsgi.ini /app/wsgi.ini

# Run all commands from this folder. This is where the service will be
# located after the last step copies the files in.
EXPOSE 5000
WORKDIR /app
RUN mkdir files/
RUN pip3 install -r requirements.txt

ADD . /app


# the default command to run when running this container. This should
# be the command to run the service as it will be what runs when the
# operations platform deploys the service.
#CMD uwsgi -i wsgi.ini
CMD python3 main.py 