FROM python:2-onbuild

LABEL maintainer="Jared Kosanovic"
LABEL description="Run script to download Jenkins plugins and dependencies."

USER nobody:nogroup

ENTRYPOINT [ "python", "./download_plugins.py", "/usr/src/app/jenkins_plugins.yaml", "/usr/src/app/jenkins_plugins" ]