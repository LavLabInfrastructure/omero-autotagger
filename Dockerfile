FROM python:3.10

ENV OMERO_USER fkyereme
ENV OMERO_PASS Medical2023
ENV OMERO_SERVER 
ENV OMERO_PORT

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "omero_tagger.py"]