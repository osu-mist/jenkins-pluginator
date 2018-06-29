import requests
import yaml
import sys
from textwrap import dedent
from distutils.version import LooseVersion


# Get dependencies for a plugin, or get depedencies for a dependency.
def get_dependencies(plugin):
    print(dedent("""
    Finding dependencies for: {0}
    ******************************************
    {0} has these dependencies:""".format(plugin)))

    try:
        dependencies = plugins_list["plugins"][plugin]["dependencies"]
    except KeyError:
        print("Unable to find dependencies for {}.".format(plugin))
        global exit_code
        exit_code = 1
        return None

    for dependency in dependencies:
        print("Processing dependency: {}".format(dependency["name"]))

        if dependency["optional"]:
            print("{} is optional".format(dependency["name"]))
            continue

        elif dependency["name"] in stored_plugins:
            if (LooseVersion(dependency["version"]) <=
                    LooseVersion(stored_plugins[dependency["name"]])):
                print("Newer or same version of dependency already added")
            else:
                print("Adding new version of dependency")
                stored_plugins[dependency["name"]] = dependency["version"]
                get_dependencies(dependency["name"])
            if not (any(p.get(dependency["version"], None) == plugin for p in
                    dependencies_info[dependency["name"]]["parents"])):
                version_sorted_insert(dependency, plugin)

        else:
            print("Adding dependency: {}".format(dependency["name"]))
            stored_plugins[dependency["name"]] = dependency["version"]
            dependencies_info[dependency["name"]] = {
                "duplicate": False,
                "parents": []
            }
            dependencies_info[dependency["name"]]["parents"].append(
                {dependency["version"]: plugin}
            )
            get_dependencies(dependency["name"])


# Download plugin from jenkins update server.
# If no version is specified, latest plugin is downloaded.
def download_plugin(plugin, version=None):
    download_url = ""

    if version is None:
        download_url = "{url}/latest/{plugin}.hpi".format(
            url=plugin_base_url, plugin=plugin
        )
    else:
        download_url = (plugin_base_url +
                        "/download/plugins/" +
                        "{plugin}/{version}/{plugin}.hpi".format(
                            plugin=plugin, version=version
                        ))

    plugin_download = requests.get(download_url, stream=True)

    if plugin_download.status_code == 200:
        destination_path = "{dir}/{plugin}.hpi".format(
            dir=download_directory, plugin=plugin
        )

        with open(destination_path, "wb") as data:
            for chunk in plugin_download.iter_content(chunk_size=128):
                data.write(chunk)

        print("Downloaded {}".format(plugin))

    else:
        print("Error downloading {plugin}. Response:\n{response}".format(
            plugin=plugin, response=plugin_download.text
        ))
        global exit_code
        exit_code = 1


# Install each plugin in the supplied json file along with dependencies.
def install_plugins():
    for plugin, version in plugins.items():
        print("\n**** Install Plugin: {} *****".format(plugin))
        download_plugin(plugin, version)
        get_dependencies(plugin)

    print("\nDownloading all dependencies")
    print("*****************************************")
    for plugin, version in stored_plugins.items():
        download_plugin(plugin, version)

    for dependency, info in dependencies_info.items():
        if not (info["duplicate"]):
            continue
        print(dedent("""\
        Warning: Multiple versions of {} found in dependencies.\
        """.format(dependency)))
        for parent in info["parents"]:
            for version, plugin in parent.items():
                print("    Version {version} required by {plugin}".format(
                    version=version, plugin=plugin
                ))
        print("    Downloaded version {}".format(stored_plugins[dependency]))


# Insert a new dependency parent sorted by version
def version_sorted_insert(dependency, plugin):
    for idx, elem in enumerate(
            dependencies_info[dependency["name"]]["parents"]):
        for version, parent in elem.items():
            if (LooseVersion(dependency["version"]) <=
                    LooseVersion(version)):
                dependencies_info[dependency["name"]]["parents"].insert(
                    idx, {dependency["version"]: plugin}
                )
                if (LooseVersion(dependency["version"]) <
                        LooseVersion(version)):
                    dependencies_info[dependency["name"]]["duplicate"] = True
                return
    dependencies_info[dependency["name"]]["parents"].append(
        {dependency["version"]: plugin}
    )
    dependencies_info[dependency["name"]]["duplicate"] = True


plugins_file_path = str(sys.argv[1])
download_directory = str(sys.argv[2])

try:
    with open(plugins_file_path, "r") as file:
        plugins = yaml.load(file)["plugins"]
except (IOError, ValueError):
    sys.exit("Unable to load plugin yaml file")

plugin_base_url = "https://updates.jenkins.io"
stored_plugins = {}
dependencies_info = {}

plugins_list_request = requests.get(plugin_base_url +
                                    "/current/update-center.actual.json")

if plugins_list_request.status_code != 200:
    sys.exit("Unable to get plugin data. Response:\n{}".format(
        plugins_list_request.text
    ))

plugins_list = plugins_list_request.json()
exit_code = 0

install_plugins()
sys.exit(exit_code)
