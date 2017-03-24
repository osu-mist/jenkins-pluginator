FROM python:2-onbuild

ENTRYPOINT [ "python", "./download_plugins.py", "/usr/src/app/jenkins_plugins.yaml", "/usr/src/app/jenkins_plugins" ]