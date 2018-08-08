import re
from argparse import ArgumentParser, ArgumentTypeError
from dataclasses import dataclass

import requests


@dataclass
class Unauthorized(Exception):
    realm: str
    service: str
    scope: list


@dataclass
class DockerAPIv2:
    username: str
    password: str
    address: str

    def _request(self, uri, **kwargs):
        def request(**kwargs_):
            response_ = requests.get(f'https://{self.address}/v2/{uri}', **kwargs, **kwargs_)

            if response_.status_code == 401:
                entries = response_.headers['www-authenticate'] \
                    .replace('Bearer ', '', 1) \
                    .split(',')
                authentication_details = {entry['key']: entry['value'] for entry in
                                          (re.match('(?P<key>.*?)="(?P<value>.*?)"', entry) for entry in entries)}

                raise Unauthorized(
                    realm=authentication_details['realm'],
                    service=authentication_details['service'],
                    scope=authentication_details['scope'].split(' ')
                )

            return response_

        try:
            return request()
        except Unauthorized as exception:
            response = requests.get(exception.realm, auth=(self.username, self.password), params={
                "service": exception.service,
                "scope": exception.scope
            })
            return request(headers={'Authorization': f'Bearer {response.json()["token"]}'})

    def catalog(self):
        response = self._request('_catalog')
        return response.json()['repositories']

    def tags(self, repository):
        response = self._request(f'{repository}/tags/list')
        return response.json()['tags']


def address_with_credentials(string):
    match = re.match('^(?P<username>.+?):(?P<password>.+?)@(?P<address>.+?)$', string)

    if not match:
        raise ArgumentTypeError(f'"{string}" is not a valid connection string')

    return DockerAPIv2(**match.groupdict())


parser = ArgumentParser(description='Mirror docker repositories')
parser.add_argument('--source', required=True, type=address_with_credentials)
parser.add_argument('--destination', required=True, type=address_with_credentials)


def all_repository_tags(registry):
    return {f'{repository}:{tag}' for repository in registry.catalog() for tag in registry.tags(repository)}


if __name__ == '__main__':
    args = parser.parse_args()
    source = args.source
    destination = args.destination

    source_tags = all_repository_tags(source)
    destination_tags = all_repository_tags(destination)

    # mirror(source, destination, source_tags)
    # delete(destination, destination_tags - source_tags)
