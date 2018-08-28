# Docker Mirror

Use this script to mirror one or more Docker registries from a sentral registry.
In cases where firewalls or network topology gets in your way of mirroring
repositories using Docker's pull through cache this simple script can do the job
by downloading and uploading images from an external machine.

## Usage

Running the script will copy all repositories/tags from the source registry
to the destination registry and delete all repositories/tags from the
destination registry which does not exist in the source registry.

Invoke the mirroring script with the arguments `--from <SOURCE>` and
`--to <DESTINATION>` to initiate the mirroring process. An optional argument
`--insecure` can also be given to bypass TLS certificate validation for the
registries in case of self signed certificates.

Addesses to the source and destination registries can optionally include a
username and password as separated by `:` and `@`, eg.
`username:password@my.registry.com:5000`.

## Authors

* **Andreas Hagen** - [hagen93](https://github.com/hagen93)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details