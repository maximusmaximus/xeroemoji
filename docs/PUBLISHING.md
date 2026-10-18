# Publishing the packages to npm and PyPI

Both packages are ready but **not published**. The package version is 1.0.1. The art has not changed since v1.0.0, so both packages still pin their image URLs to the `v1.0.0` tag. Version 1.0.1 only changes metadata: the SPDX license `CC-BY-NC-4.0`, COMMERCIAL-LICENSE.md is included, the READMEs are written for the registries, the Python package gets an sdist, and the image tag is kept separate from the package version.

Build (about 5 s; skips the art zips):

```sh
python3 -m pip install build twine
python3 tools/build_release.py --packages-only     # dist/xeroemoji-1.0.1.tgz, -py3-none-any.whl, .tar.gz
twine check --strict dist/xeroemoji-1.0.1*.whl dist/xeroemoji-1.0.1.tar.gz
(cd packages/npm && npm publish --dry-run --access public)
```

Publish (needs logins, see below):

```sh
npm publish dist/xeroemoji-1.0.1.tgz --access public
twine upload dist/xeroemoji-1.0.1-py3-none-any.whl dist/xeroemoji-1.0.1.tar.gz
git tag -a v1.0.1 -m "xeroemoji 1.0.1 packages" && git push origin v1.0.1   # then attach the same three files to a v1.0.1 release
```

Logins:
- **npm:** run `npm login` (web sign-in), or set a granular access token with read and write permission. Put it in `~/.npmrc` as `//registry.npmjs.org/:_authToken=...`, or pass it as `NODE_AUTH_TOKEN` in CI. If the account has 2FA, a granular token with "bypass 2FA" set lets you publish without a code prompt.
- **PyPI:** an API token (`pypi-...`) used as `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=pypi-...`. A token scoped to one project can only be created after that project exists, so the first upload needs an account-wide token. Once the project exists, replace it with a token scoped to `xeroemoji`, or set up Trusted Publishing.

Check after publishing: `npm view xeroemoji`, `curl https://pypi.org/pypi/xeroemoji/json`, then install each package fresh in a temporary folder and run `xeroemoji get 🚀`.
