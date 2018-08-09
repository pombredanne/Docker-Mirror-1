import re
from argparse import ArgumentParser, ArgumentTypeError

from dxf import DXF, DXFBase
from requests import HTTPError


# TODO: Token support instead of username/password
def address_with_credentials(string):
    match = re.match('(?:^(?P<username>.+?):(?P<password>.+?)@)?(?P<address>.+?)$', string)

    if match:
        if match['username'] and match['password']:
            def auth(dxf, response_):
                dxf.authenticate(username=match['username'], password=match['password'], response=response_)
        elif match['username'] or match['password']:
            raise ArgumentTypeError(f'"{string}" is not a valid connection string')
        else:
            auth = None

        return DXFBase(match['address'], auth=auth, tlsverify=False)  # TODO: Get tlsverify from arguments instead
    else:
        raise ArgumentTypeError(f'"{string}" is not a valid connection string')


parser = ArgumentParser(description='Mirror docker repositories')
parser.add_argument('-f', '--from', required=True, type=address_with_credentials, dest='source')
parser.add_argument('-t', '--to', required=True, type=address_with_credentials, dest='destination')
args = parser.parse_args()
source = args.source
destination = args.destination

# TODO: Delete missing source repositories
for repository in source.list_repos():
    source_repository = DXF.from_base(source, repository)
    destination_repository = DXF.from_base(destination, repository)

    for tag in source_repository.list_aliases():
        manifest_string, response = source_repository.get_manifest_and_response(tag)
        manifest = response.json()
        source_layers = [manifest["config"], *manifest['layers']]

        try:
            _, response = destination_repository.get_manifest_and_response(tag)
            manifest = response.json()
            destination_layers = [manifest["config"], *manifest['layers']]
        except HTTPError:
            missing_layers = source_layers
            print(f'Creating {repository}:{tag}')
        else:
            missing_layers = [source_layer for source_layer in source_layers
                              if not any(source_layer['digest'] == destination_layer['digest']
                                         for destination_layer in destination_layers)]

            if missing_layers:
                print(f'Updating {repository}:{tag} with missing layers')
            else:
                print(f'{repository}:{tag} is already up to date')

        if missing_layers:
            for layer in missing_layers:
                print(f'Mirroring layer {layer["digest"]}')

                destination_repository.push_blob(
                    digest=layer['digest'],
                    data=source_repository.pull_blob(layer['digest']))

            print(f'Updating manifest for {repository}:{tag}')
            destination_repository.set_manifest(tag, manifest_string)
