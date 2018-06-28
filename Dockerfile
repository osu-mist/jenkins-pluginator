FROM python:3

WORKDIR /usr/src/app

COPY . .
RUN pip3 install -r requirements.txt

USER nobody:nogroup

ENTRYPOINT ["python3"]
CMD ["./download_plugins.py", "/usr/src/app/jenkins_plugins.yaml", "/usr/src/app/jenkins_plugins"]
