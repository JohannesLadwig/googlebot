import os
import json


class SeleniumDocker:
    # docker run -p 4445:4444 -d --shm-size=3g  --name bot_2 selenium/standalone-firefox
    def __init__(self, port, name, timezone='UTC', proxy_domain=None,
                 proxy_user=None,
                 proxy_password=None, memory='3g',
                 image='selenium/standalone-firefox',
                 bind_config=None,
                 vol_config=None):

        self._port = port
        self._name = name
        self.timezone = timezone
        self._proxy = proxy_domain is not None
        self._proxy_domain = proxy_domain
        self._proxy_user = proxy_user
        self._proxy_password = proxy_password
        self._memory = memory
        self._image = image
        self._mount_1 = self.bind_mount(bind_config)
        self.generate_proxy_config()
        self._run_command = f'docker run -p {self._port}:4444 -d --shm-size={self._memory} {self.generate_proxy_config()} {self._mount_1} --env TZ={self.timezone} --name {self._name} {self._image}'
        self.create_container()


    @property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, zone_name):
        with open('Data/diverse/timezones.json', 'r') as tz_file:
            valid_tz = json.load(tz_file)
        if zone_name not in valid_tz:
            raise ValueError(
                f'{zone_name} is not a valid timezone. See Data/diverse/timezones.json')
        else:
            self._timezone = zone_name

    def __str__(self):
        return str(self._run_command)

    def vol_mount(self, directories):
        os.system(f'docker volume rm {directories[0]}')
        return f'--mount source={directories[0]},target={directories[1]}'

    def bind_mount(self, directories):
        if not os.path.isdir(directories[0]):
            os.makedirs(directories[0])
        return f'--mount type=bind,source={directories[0]},target={directories[1]}'

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
        http_request = '--env http_proxy=\'http://' + request + '\''
        https_request = '--env https_proxy=\'https://' + request + '\''
        a = '--env HTTP_PROXY=\'http://' + request+'\''
        b = '--env HTTPS_PROXY=\'https://' + request + '\''

        return f'{http_request} {https_request} {a} {b}'

    def create_container(self):
        os.system(f'docker stop {self._name}')
        os.system(f'docker rm {self._name}')
        os.system(self._run_command)
