#!/bin/bash

find . -name "*.pyc" -exec git rm {} \;
git commit -m "Removed compiled python files in distribution left after last commit"
