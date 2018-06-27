import requests, yaml, sys
from distutils.version import LooseVersion

# Get dependencies for a plugin, or get depedencies for a dependency.
def get_dependencies(plugin):
    print "Finding dependencies for:", plugin
    print "*****************************************"
    print plugin, "has these dependencies:"

    try:
        dependencies = plugins_list['plugins'][plugin]['dependencies']
    except KeyError:
        print "Unable to find dependencies for %s." % plugin
        global exit_code
        exit_code = 1
        return None
    
    for dependency in dependencies:
        print "Processing dependency: " + dependency['name']

        if dependency['optional']:
                print dependency['name'] + " is optional"
        elif ((dependency['name'] in stored_plugins)
        and (LooseVersion(dependency['version']) <= LooseVersion(stored_plugins[dependency['name']]))):
            print "Dependency already found"
        else:
            print "Adding dependency " + dependency['name']
            stored_plugins[dependency['name']] = dependency['version']

# Download plugin from jenkins update server. If no version is specified, latest plugin is downloaded.
def download_plugin(plugin, version = None):
    download_url = ""
    
    if version is None:
        download_url = plugin_base_url + "/latest/%s.hpi" % plugin
    else:
        download_url = plugin_base_url + "/download/plugins/%(plugin)s/%(version)s/%(plugin)s.hpi" % {'plugin': plugin, 'version': version}

    plugin_download = requests.get(download_url, stream=True)

    if plugin_download.status_code is 200:
        destination_path = download_directory + "/" + plugin + ".hpi"

        with open(destination_path, 'wb') as data:
            for chunk in plugin_download.iter_content(chunk_size=128):
                data.write(chunk)

        print "Downloaded", plugin
        
    else:
        print "Error downloading %s. Response:" % plugin
        print plugin_download.text
        global exit_code
        exit_code = 1

# Install each plugin in the supplied json file along with dependencies.
def install_plugins():
    for plugin, version in plugins.items():
        print "**** Install Plugin: %s ****" % plugin
        download_plugin(plugin, version)
        get_dependencies(plugin)

    for plugin, version in stored_plugins.items():
        print "Installing " + plugin
        download_plugin(plugin, version)


plugins_file_path = str(sys.argv[1])
download_directory = str(sys.argv[2])

try:
    with open(plugins_file_path, 'r') as file:
        plugins = yaml.load(file)['plugins']
except (IOError, ValueError):
    print "Unable to load plugin yaml file"
    sys.exit(1)

plugin_base_url = "https://updates.jenkins.io"
stored_plugins = {}

plugins_list_request = requests.get(plugin_base_url + "/current/update-center.actual.json")

if plugins_list_request.status_code is not 200:
    print "Unable to get plugin data. Response:"
    print plugins_list_request.text
    sys.exit(1)

plugins_list = plugins_list_request.json()
exit_code = 0

install_plugins()
sys.exit(exit_code)
