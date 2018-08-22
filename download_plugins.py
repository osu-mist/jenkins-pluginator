import sys
from logging import debug

import requests
import yaml

import utils


# Get dependencies for a plugin, or get dependencies for a dependency.
def get_dependencies(plugin):
    debug(f"Finding dependencies for {plugin}\n"
          f"******************************************\n"
          f"{plugin} has these dependencies:\n"
          )
    try:
        dependencies = plugins_list["plugins"][plugin]["dependencies"]
    except KeyError:
        debug(f"Unable to find dependencies for {plugin}.")
        global exit_code
        exit_code = 1
        return None

    for dependency in dependencies:
        dep_name = dependency["name"]
        debug(f"Processing dependency: {dep_name}")
        if dependency["optional"]:
            debug(f"{dep_name} is optional")
            continue
        download_plugin(dep_name)
        get_dependencies(dep_name)


# Download latest version of plugin from jenkins update server.
def download_plugin(plugin):
    if plugin in stored_plugins.keys():
        return
    download_url = f"{plugin_base_url}/latest/{plugin}.hpi"

    plugin_download = requests.get(download_url, stream=True)

    if plugin_download.status_code == 200:
        destination_path = f"{download_directory}/{plugin}.hpi"
        with open(destination_path, "wb") as data:
            for chunk in plugin_download.iter_content(chunk_size=128):
                data.write(chunk)

        version = plugins_list["plugins"][plugin]["version"]
        stored_plugins[plugin] = version

        status = "top-level" if plugin in plugins else "dependency"
        print(f"Downloaded {status} plugin {plugin}: {version}")

    else:
        print(f"Error downloading {plugin}. Response:\n{plugin_download.text}")
        global exit_code
        exit_code = 1


# Install each plugin in the supplied json file along with dependencies.
def install_plugins():
    for plugin in plugins.keys():
        debug(f"\n**** Add Plugin: {plugin} *****")
        download_plugin(plugin)
        get_dependencies(plugin)


# Write top-level plugin information to plugins file
def update_file():
    top_level_plugins = {}
    for plugin, version in stored_plugins.items():
        if plugin in plugins:
            top_level_plugins[plugin] = version
    data = {"plugins": top_level_plugins}

    with open(plugins_file_path, "w") as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
    print(f"File {plugins_file_path} updated")


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

    plugins_list_request = requests.get(
        f"{plugin_base_url}/current/update-center.actual.json"
    )

    if plugins_list_request.status_code != 200:
        sys.exit(
            f"Unable to get plugin data. Response:\n"
            f"{plugins_list_request.text}"
        )

    plugins_list = plugins_list_request.json()
    exit_code = 0

    stored_plugins = {}
    install_plugins()
    update_file()
    sys.exit(exit_code)
