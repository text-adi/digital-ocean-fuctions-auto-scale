# DIgital Ocean Function: Auto Scale utils

## Introduction

This repository contains a sample joke API function written in Python. You can deploy it on DigitalOcean's App Platform as a Serverless Function component.
Documentation is available at https://docs.digitalocean.com/products/functions.

### Requirements

* You need a DigitalOcean account. If you don't already have one, you can sign up at [https://cloud.digitalocean.com/registrations/new](https://cloud.digitalocean.com/registrations/new).
* To deploy from the command line, you will need the [DigitalOcean `doctl` CLI](https://github.com/digitalocean/doctl/releases).

## Deploying the Function

```
# clone this repo
git clone git@github.com:text-adi/digital-ocean-fuctions-auto-scale.git
```

```
# deploy the project, using "remote-build" so that the build and runtime environments match
> doctl serverless deploy . --remote-build
Deploying './auto-scale/main'
  to namespace 'fn-...'
  on host 'https://faas-...'
Submitted action 'auto-scale/main' for remote building and deployment in runtime python:default
Processing of 'auto-scale/main' is still running remotely ...
...
Deployed functions ('doctl sbx fn get <funcName> --url' for URL):
  - auto-scale/main
```

```
# execute the function
> doctl serverless functions invoke auto-scale/main
```

Note the CLI command can be abbreviated as `doctl sls fn invoke auto-scale/main`.

### Params



### Learn More

You can learn more about Functions and App Platform integration in [the official App Platform Documentation](https://www.digitalocean.com/docs/app-platform/).