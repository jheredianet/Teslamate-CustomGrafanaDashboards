#!/bin/bash

# The following command will clone the source files from this repository. 
# This should be run in an appropriate directory within which you would like to keep it.
# To keep it easy, you may run this your home path (~/) or modify it accordingly

# In case git is not installed
sudo apt update
sudo apt install git

# Clone the repository
git clone https://github.com/jheredianet/Teslamate-CustomGrafanaDashboards.git


# Update the repository
# If you want to be sure that you are using the latest version of the Dashboards
git -C ~/Teslamate-CustomGrafanaDashboards pull
