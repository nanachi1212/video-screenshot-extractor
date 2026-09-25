# Code signing policy

Video Screenshot Extractor is maintained as an open-source project by the individual maintainer **nanachi1212**.

> Free code signing provided by SignPath.io, certificate by SignPath Foundation

The project is applying to the SignPath Foundation open-source program so that future official Windows releases can be signed from the project's automated GitHub Actions build pipeline. Releases published before SignPath approval may remain unsigned.

## Team roles

Because this is a single-maintainer project, the same maintainer currently holds the required project roles:

- **Committer / author:** [nanachi1212](https://github.com/nanachi1212)
- **Reviewer:** [nanachi1212](https://github.com/nanachi1212)
- **Signing approver:** [nanachi1212](https://github.com/nanachi1212)

Changes from external contributors must be reviewed before merge. Signing approval is performed only for official project releases built from this repository.

## Signing scope

Only release artifacts produced from this repository's source code and automated build configuration may be submitted for signing.

The project does not use its SignPath Foundation signing access to sign unrelated projects, third-party proprietary software, or arbitrary binaries.

Bundled upstream open-source binaries remain subject to their own licenses and signing status. They are not re-signed as if they were authored by this project.

## Build provenance

Official Windows artifacts are built by GitHub Actions from the repository source and release workflow. Release artifacts include SHA-256 checksums.

Repository:

https://github.com/nanachi1212/video-screenshot-extractor

Releases:

https://github.com/nanachi1212/video-screenshot-extractor/releases

## Privacy

See the project's [Privacy Policy](PRIVACY.md).
