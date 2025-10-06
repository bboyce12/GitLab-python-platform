# GitLab DevOps Automation & Analytics Tool

A Python-based desktop application designed to simplify and automate key DevOps processes within GitLab, tailored for small organizations and development teams.



# 1. Problem Statement

Small organisations often face significant challenges in adopting DevOps practices due to the complexity, cost, and expertise required to manage traditional, fragmented toolchains (e.g., Jenkins, Docker, Prometheus). This tool aims to lower that barrier by leveraging the integrated GitLab platform and abstracting its powerful API into a user-friendly graphical interface.



# 2. Key Features

The application provides a centralized GUI to manage and analyse the entire DevOps lifecycle within GitLab.



Automation & Management

Team & Group Onboarding: Create new groups and subgroups to structure teams.



User Management: Add, remove, and change the permission levels of users within groups.



Automated Project Creation:



Provision new projects from a standardized, pre-configured template.



Automatically populate new projects with default files (.gitlab-ci.yml, .gitignore, etc.).



Apply security rules, such as protected tag policies, from the moment of creation.



Permissions Control: Share and unshare projects with different groups to manage access.



CI/CD & Release Automation

Automated Issue Creation: The CI/CD pipeline automatically creates a new issue and assigns it to the commit author upon a test failure.



Automated Release Notes: On the creation of a new version tag, the pipeline automatically generates structured release notes based on conventional commit messages with key words (feat, fix, docs, style, refactor, perf, test, chore and build).

(e.g. commit message: fix: UI bug)



Analytics & Reporting

Project Summary: Generate a quick, real-time summary of a project’s status, including recent commits and failing pipelines.



Quantitative DevOps Metrics:



Calculate and display the Pipeline Success Rate.



Calculate and display the Average Pipeline Run Time.



Calculate and display the Average Time to Close Issues.



# 3. Technology Stack

Backend: Python 3



GitLab API Interaction: python-gitlab library



GUI: Tkinter (Python's standard library)



Environment Management: python-dotenv



# 4. Setup and Installation

To run this application on your local machine, please follow these steps.



Prerequisites

Python 3.8 or newer



Git command-line tools



Step 1: Clone the Repository

Open your terminal and clone this repository to your local machine:



git clone https://github.com/bboyce12/GitLab-python-platform.git

Step 2: Set Up the Virtual Environment

It is highly recommended to use a Python virtual environment to manage dependencies.



Create the virtual environment

python3 -m venv venv



Activate the virtual environment

On macOS or Linux:

source venv/bin/activate

On Windows:

.\venv\Scripts\activate

Step 3: Install Dependencies

Install all the required Python libraries from the requirements.txt file.



pip install -r requirements.txt

Step 4: Configure Your Credentials

This application requires a local .env file to securely store your GitLab credentials.



Create the file: In the root directory of the project, create a new file named .env.



When first using the application, environment variables are prompted for input.

If it is not wokring, add your details: Open the .env file and add the following lines, replacing the placeholder values with your own:



.env file



Your GitLab Personal Access Token with 'api' scope

GITLAB_PRIVATE_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"


The URL of your GitLab instance

GITLAB_URL="https://gitlab.com"


The ID of a top-level group where you have Owner permissions.

This will be used as the default parent for creating new groups/projects.

PARENT_GROUP_ID="12345678"

Note: This .env file is included in .gitignore and should never be committed to version control.



# 5. Usage

Once the setup is complete, you can run the application with the following command:



Bash



python frontend.py

This will launch the Tkinter GUI, which will attempt to connect to GitLab using the credentials you provided.



# 6. License

This project is licensed under the MIT License. See the LICENSE file for details.
