# Security Policy

## Supported Versions

VideoStrap is developed on a single rolling `master` branch. Security fixes
are applied there; please always run the latest commit.

| Version | Supported |
|---|---|
| latest (`master`) | ✅ |

## Scope and intended use

VideoStrap is designed to run **locally**, bound to your own machine, for
personal or team use. It has **no authentication and no rate limiting**, and
is not hardened for exposure to the public internet. Running it on a
publicly reachable host without your own auth/network controls in front of
it is a misuse of the tool, not a supported deployment.

## Reporting a Vulnerability

If you find a security issue (e.g. path traversal, arbitrary file access,
command injection via crafted filenames/video metadata), please report it
privately rather than opening a public issue:

1. Open a [GitHub Security Advisory](https://github.com/hirdav/videostrap/security/advisories/new) for this repository, or
2. If that isn't available to you, open a regular issue with minimal detail asking a maintainer to reach out for a private channel.

Please include:

- A description of the issue and its potential impact
- Steps to reproduce (a sample video/request is helpful if relevant)
- Any suggested fix, if you have one

We'll acknowledge reports as soon as possible and keep you updated as the
issue is triaged and fixed.
