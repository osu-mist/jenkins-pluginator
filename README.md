# Download Jenkins Plugins
This repository contains a [script](download_plugins.py) that downloads Jenkins plugin (.hpi files). This script downloads
plugins and required dependencies. This script doesn't install optional dependencies.

## Usage
Modify the [example yaml file](jenkins_plugins_example.yaml) to list the desired plugins to be downloaded.

### Regular Method
Install the required libraries given in [requirements.txt](requirements.txt).

Run the script:
```
python3 download_plugins.py jenkins_plugins.yaml /path/to/download/directory
```

### Docker Method
Build an image and run the container:
```
docker build -t jenkins-pluginator .
docker run --rm \
    -v "$PWD"/jenkins_plugins.yaml:/usr/src/app/jenkins_plugins.yaml:ro \
    -v /path/to/download/directory:/usr/src/app/jenkins_plugins \
    jenkins-pluginator
```
