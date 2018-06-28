FROM python:3

WORKDIR /usr/src/app

COPY . .
RUN pip3 install -r requirements.txt

LABEL maintainer="Jared Kosanovic"
LABEL description="Run script to download Jenkins plugins and dependencies."

USER nobody:nogroup

ENTRYPOINT ["python3"]
CMD ["./download_plugins.py", "/usr/src/app/jenkins_plugins.yaml", "/usr/src/app/jenkins_plugins" ]
