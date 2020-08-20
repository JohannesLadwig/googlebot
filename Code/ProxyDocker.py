import os
import json


class ProxyDocker:
    def __init__(self, name, proxy_host_port, proxy_user, proxy_password, port=8080):

        self._port = port
        self._name = '\"' + name + '\"'
        self._proxy_host_port = proxy_host_port
        self._proxy_user = proxy_user
        self._proxy_password = proxy_password
        self._image = 'mitmproxy/mitmproxy mitmdump'
        self._run_command = f'docker run --rm -i -d -p {self._port}:{self._port} --name {self._name} {self._image} {self.set_options()}'
        self.create_container()

    def __str__(self):
        return str(self._run_command)

    def create_container(self):
        os.system(f'docker stop {self._name}')
        os.system(self._run_command)

    def set_options(self):
        mode = f"--set mode=\"upstream:https://{self._proxy_host_port}\""
        authentication = f" --set upstream_auth=\"{self._proxy_user}:{self._proxy_password}\""
        return mode + authentication
