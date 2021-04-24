# PACE 2021 S1 - Portant

## Overview

Companies are constantly moving data between employees, teams, departments and even different organisations. Portant aims to become a communication layer that defines the way businesses communicate. One of the biggest challenges in regards to managing data is privacy and we are excited to explore the ways in which “End to End (E2E) Encryption” can be used to allow data to flow securely from one source to another.

## Requirements

Live project requirements will be kept in and added to [this document](https://docs.google.com/document/d/1kGDZQyUg5dHPoDwXbGEYHb0bNSOqUfES0BdOVNG0Vp0).

## Setup

1. **Create a Virtual Environment**

If you have not used virtualenv or similar tools before you can take a look here: [virtual environment](https://virtualenv.pypa.io/en/latest/). You should use a distribution of python 3 already installed on your machine (this template has been tested with version 3.7).

        $ virtualenv venv --python=python3.7

2. **Activate your Virtual Environment**

Windows:

        $ venv\Scripts\activate

MacOs/Linux:

        $ source venv/bin/activate

Once your environment is activated you will notice the environment's name `(venv)` in the command prompt.

3. **Install Requirements**

In the virtual environment, install dependencies from the requirements file.

        (venv) $ pip install -r requirements.txt

<!-- 4. **Create Database**

Create database tables. Before running the app for the first time or after making changes to the `model.py` file you will need to make the necessary tables in your database using the following command.

        (venv) $ python src/create_db.py -->

4. **Run**

In the virtual environment, run the application.

        (venv) $ python src/app.py
