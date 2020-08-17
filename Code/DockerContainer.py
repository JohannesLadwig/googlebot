import os


class DockerContainer:
    # docker run -p 4445:4444 -d --shm-size=2g  --name bot_2 selenium/standalone-firefox
    def __init__(self, port, name, proxy_domain=None, proxy_user=None,
                 proxy_password=None, memory='2g',
                 image='selenium/standalone-firefox'):
        self._port = port
        self._name = name
        self._proxy = proxy_domain is not None
        self._proxy_domain = proxy_domain
        self._proxy_user = proxy_user
        self._proxy_password = proxy_password
        self._memory = memory
        self._image = image
        self.generate_proxy_config()
        self._run_command = f'docker run -p {self._port}:4444 -d --shm-size={self._memory} {self.generate_proxy_config()} --name {self._name} {self._image}'
        self.create_container()

    def __str__(self):
        return str(self._run_command)

    def generate_proxy_config(self):
        if not self._proxy:
            return ''
        if self._proxy_user is not None:
            if self._proxy_password is not None:
                request = self._proxy_user + ':' + self._proxy_password + '@' + self._proxy_domain
            else:
                request = self._proxy_user + '@' + self._proxy_domain
        else:
            request = self._proxy_domain
        http_request = '-e HTTP_PROXY=http://' + request
        https_reuqest = '-e HTTPS_PROXY=http://' + request
        return f'{http_request} {https_reuqest}'

    def create_container(self):
        os.system(f'docker stop {self._name}')
        os.system(f'docker rm {self._name}')
        os.system(self._run_command)

