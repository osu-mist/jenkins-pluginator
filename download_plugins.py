import utils
import requests
import yaml
import sys
from logging import debug
from textwrap import dedent
from distutils.version import LooseVersion


# Get dependencies for a plugin, or get depedencies for a dependency.
def get_dependencies(plugin):
    debug(dedent("""
    Finding dependencies for: {0}
    ******************************************
    {0} has these dependencies:""".format(plugin)))

    try:
        dependencies = plugins_list["plugins"][plugin]["dependencies"]
    except KeyError:
        debug("Unable to find dependencies for {}.".format(plugin))
        global exit_code
        exit_code = 1
        return None

    for dependency in dependencies:
        dep_version = dependency["version"]
        dep_name = dependency["name"]
        debug("Processing dependency: {}".format(dep_name))

        if dependency["optional"]:
            debug("{} is optional".format(dep_name))
            continue
        else:
            add_dep(dep_name, dep_version, plugin)


def add_dep(dep_name, dep_version, parent):
    if dep_name in stored_plugins:
        if (utils.not_newer(dep_version, stored_plugins[dep_name])):
            debug("Newer or same version of dependency already added")
        else:
            debug("Adding new version of dependency")
            stored_plugins[dep_name] = dep_version
            get_dependencies(dep_name)
        # Insert dependency entry if not already in dep_info
        if not (any(p.get(dep_version, None) == parent for p in
                dep_info[dep_name]["parents"])):
            version_sorted_insert(dep_name, dep_version, parent)

    else:
        debug("Adding dependency: {}".format(dep_name))
        stored_plugins[dep_name] = dep_version
        dep_info[dep_name] = {"duplicate": False, "parents": []}
        dep_info[dep_name]["parents"].append({dep_version: parent})
        get_dependencies(dep_name)


# Download plugin from jenkins update server.
# If no version is specified, latest plugin is downloaded.
def download_plugin(plugin, version=None):
    download_url = ""

    download_url = ("{url}/download/plugins/"
                    "{plugin}/{version}/{plugin}.hpi".format(
                        url=plugin_base_url, plugin=plugin,
                        version=version
                    ))

    plugin_download = requests.get(download_url, stream=True)

    if plugin_download.status_code == 200:
        destination_path = "{dir}/{plugin}.hpi".format(
            dir=download_directory, plugin=plugin
        )

        with open(destination_path, "wb") as data:
            for chunk in plugin_download.iter_content(chunk_size=128):
                data.write(chunk)
        if plugin in plugins:
            print("Downloaded {plugin}: {version} [TOP-LEVEL]".format(
                plugin=plugin, version=stored_plugins[plugin]
            ))
        else:
            print("Downloaded {plugin}: {version}".format(
                plugin=plugin, version=stored_plugins[plugin]
            ))

    else:
        print("Error downloading {plugin}. Response:\n{response}".format(
            plugin=plugin, response=plugin_download.text
        ))
        global exit_code
        exit_code = 1


# Install each plugin in the supplied json file along with dependencies.
def install_plugins():
    for plugin, version in plugins.items():
        debug("\n**** Add Plugin: {} *****".format(plugin))
        if version is None:
            version = plugins_list["plugins"][plugin]["version"]
        add_dep(plugin, version, plugin)
        get_dependencies(plugin)

    debug("\nDownloading all dependencies")
    debug("*****************************************")
    for plugin, version in stored_plugins.items():
        download_plugin(plugin, version)

    for dependency, info in dep_info.items():
        if not (info["duplicate"]):
            continue
        print(dedent("""\
        Warning: Multiple versions of {} found in dependencies.\
        """.format(dependency)))
        for parent in info["parents"]:
            for version, plugin in parent.items():
                if dependency == plugin:
                    print("    !! TOP-LEVEL version: {} !!".format(version))
                else:
                    print("    Version {version} required by {plugin}".format(
                        version=version, plugin=plugin
                    ))
        print("    Downloaded version {}".format(stored_plugins[dependency]))

    # Print warning for plugin if downloaded version != specified version
    for plugin, version in plugins.items():
        if version != stored_plugins[plugin]:
            print("Warning: TOP-LEVEL version of {plugin} ({spec_ver}) "
                  "not same as downloaded ({real_ver})".format(
                    plugin=plugin, spec_ver=version,
                    real_ver=stored_plugins[plugin]
                    ))


# Insert a new dependency parent sorted by version
def version_sorted_insert(dep_name, dep_version, plugin):
    for idx, elem in enumerate(dep_info[dep_name]["parents"]):
        for version, parent in elem.items():
            if(utils.not_newer(dep_version, version)):
                dep_info[dep_name]["parents"].insert(
                    idx, {dep_version: plugin}
                )
                if utils.is_older(dep_version, version):
                    dep_info[dep_name]["duplicate"] = True
                return
    dep_info[dep_name]["parents"].append({dep_version: plugin})
    dep_info[dep_name]["duplicate"] = True


if __name__ == "__main__":
    args = utils.parse_args()
    plugins_file_path = args.jenkins_plugins_config
    download_directory = args.download_dir

    try:
        with open(plugins_file_path, "r") as file:
            plugins = yaml.load(file)["plugins"]
    except (IOError, ValueError):
        sys.exit("Unable to load plugin yaml file")

    plugin_base_url = "https://updates.jenkins.io"
    stored_plugins = {}
    dep_info = {}

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
