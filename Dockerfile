FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV DOCKER_CONTAINER 1

WORKDIR /
COPY requirements.txt /requirements.txt
RUN pip install --no-cache -r /requirements.txt

COPY . /climada_calc_api
RUN chmod -R 755 /climada_calc_api
WORKDIR /climada_calc_api
CMD ["python", "manage.py", "runserver"]
