# Build, test and publish

Only .github/workflows/ci.yml remains. Every branch push, pull request and manual run builds and tests the application. Docker Hub publication is limited to the repository default branch after both native linux/amd64 and linux/arm64 jobs pass.

The version comes from __version__ in app/__init__.py (currently 0.9.0), not the Xray core version. The Docker tag is exactly that value, for example kajoosh/xmarzban:0.9.0; no latest or development tags are published.

For a push, the version is compared with the commit before the entire push (including multi-commit pushes). For a manual run, it is compared with HEAD^; a manual run does not override the version gate. A first addition of the version file counts as a change. An unchanged version still runs the build and tests but skips publication. An already existing Docker Hub tag is skipped, so reruns and rollbacks cannot overwrite a published version. Registry authentication or network errors fail the job rather than being treated as a missing tag.

Set the repository Actions secret DOCKERHUB_TOKEN for the kajoosh account, with push access to kajoosh/xmarzban. The workflow derives the login username from the image namespace (kajoosh); no DOCKERHUB_USERNAME secret is required. To publish the next release, change app/__init__.py to the next version and push it to the default branch.

Checks include TypeScript/Vite compilation in the Docker build, version-gate unit tests, real isolated TCP/UDP protocol/transport connections, API/database/user lifecycle, browser subscription output, Xray config validation and exact advanced-field transfer for all 354 fixture profiles. Temporary CI users, private certificates and configs stay inside disposable containers. Test failures prevent publication. No live local server or user data is mounted in CI.

Action references follow the official [checkout](https://github.com/actions/checkout) and [Docker build/push](https://github.com/docker/build-push-action) documentation. Native runner labels are documented by [GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

Local verification covered the amd64 build, release unit tests, live transport matrix, API fixture, advanced profile checks and actionlint. Native arm64 execution and actual registry publication require the GitHub run; local validation does not claim those have occurred.
