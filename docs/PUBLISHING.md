# Publishing the packages to npm and PyPI

Both packages are published by `.github/workflows/publish.yml` when a `vX.Y.Z` tag is pushed (repo secrets `NPM_TOKEN` and `PYPI_TOKEN`). The current version is 1.0.2, the first CC BY 4.0 release (SPDX `CC-BY-4.0`; 1.0.2 and earlier were CC BY-NC 4.0). The art has not changed since v1.0.0; since 1.0.2 the packages pin their image URLs to the `v1.0.2` tag, which carries the CC BY 4.0 `LICENSE`. The image tag (`ART_TAG`) is kept separate from the package version.

Build (about 5 s; skips the art zips):

```sh
python3 -m pip install build twine
python3 tools/build_release.py --packages-only     # dist/xeroemoji-1.0.2.tgz, -py3-none-any.whl, .tar.gz
twine check --strict dist/xeroemoji-1.0.2*.whl dist/xeroemoji-1.0.2.tar.gz
(cd packages/npm && npm publish --dry-run --access public)
```

Publish (needs logins, see below):

```sh
npm publish dist/xeroemoji-1.0.2.tgz --access public
twine upload dist/xeroemoji-1.0.2-py3-none-any.whl dist/xeroemoji-1.0.2.tar.gz
git tag -a v1.0.2 -m "xeroemoji 1.0.2 packages" && git push origin v1.0.2   # then attach the same three files to a v1.0.2 release
```

Logins:
- **npm:** run `npm login` (web sign-in), or set a granular access token with read and write permission. Put it in `~/.npmrc` as `//registry.npmjs.org/:_authToken=...`, or pass it as `NODE_AUTH_TOKEN` in CI. If the account has 2FA, a granular token with "bypass 2FA" set lets you publish without a code prompt.
- **PyPI:** an API token (`pypi-...`) used as `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=pypi-...`. A token scoped to one project can only be created after that project exists, so the first upload needs an account-wide token. Once the project exists, replace it with a token scoped to `xeroemoji`, or set up Trusted Publishing.

Check after publishing: `npm view xeroemoji`, `curl https://pypi.org/pypi/xeroemoji/json`, then install each package fresh in a temporary folder and run `xeroemoji get 🚀`.
