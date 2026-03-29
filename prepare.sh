#!/bin/bash

# prepare venv
/usr/bin/python3 -m venv venv && cd venv && source bin/activate
# install python dependencies
/usr/bin/pip install flask playwright && bin/playwright install