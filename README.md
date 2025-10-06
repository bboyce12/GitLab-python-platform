GitLab DevOps Automation & Analytics ToolA Python-based desktop application designed to simplify and automate key DevOps processes within GitLab, tailored for small organizations and development teams.1. Problem StatementSmall organisations often face significant challenges in adopting DevOps practices due to the complexity, cost, and expertise required to manage traditional, fragmented toolchains (e.g., Jenkins, Docker, Prometheus). This tool aims to lower that barrier by leveraging the integrated GitLab platform and abstracting its powerful API into a user-friendly graphical interface.2. Key FeaturesThe application provides a centralized GUI to manage and analyse the entire DevOps lifecycle within GitLab.Automation & ManagementTeam & Group Onboarding: Create new groups and subgroups to structure teams.User Management: Add, remove, and change the permission levels of users within groups.Automated Project Creation:Provision new projects from a standardized, pre-configured template.Automatically populate new projects with default files (.gitlab-ci.yml, .gitignore, etc.).Apply security rules, such as protected tag policies, from the moment of creation.Permissions Control: Share and unshare projects with different groups to manage access.CI/CD & Release AutomationAutomated Issue Creation: The CI/CD pipeline automatically creates a new issue and assigns it to the commit author upon a test failure.Automated Release Notes: On the creation of a new version tag, the pipeline automatically generates structured release notes based on conventional commit messages with keywords (feat, fix, docs, style, refactor, perf, test, chore, and build). (e.g. commit message: fix: UI bug)Analytics & ReportingProject Summary: Generate a quick, real-time summary of a project’s status, including recent commits and failing pipelines.Quantitative DevOps Metrics:Calculate and display the Pipeline Success Rate.Calculate and display the Average Pipeline Run Time.Calculate and display the Average Time to Close Issues.3. Technology StackBackend: Python 3GitLab API Interaction: python-gitlab libraryGUI: Tkinter (Python's standard library)Environment Management: python-dotenv4. Setup and InstallationTo run this application on your local machine, please follow these steps.PrerequisitesPython 3.8 or newerGit command-line toolsStep 1: Clone the RepositoryOpen your terminal and clone this repository to your local machine:git clone [https://github.com/bboyce12/GitLab-python-platform.git](https://github.com/bboyce12/GitLab-python-platform.git)
cd GitLab-python-platform
Step 2: Set Up the Virtual EnvironmentIt is highly recommended to use a Python virtual environment to manage dependencies.# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS or Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
Step 3: Install DependenciesInstall all the required Python libraries from the requirements.txt file.pip install -r requirements.txt
Step 4: Configure Your CredentialsThis application requires a local .env file to securely store your GitLab credentials.First-Time Use: When you first run the application, you will be prompted to enter your credentials in a setup window.Manual Setup (Alternative): If the automatic setup is not working, you can create a file named .env in the root directory of the project and add the following lines, replacing the placeholder values with your own:# .env file

# Your GitLab Personal Access Token with 'api' scope
GITLAB_PRIVATE_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"

# The URL of your GitLab instance
GITLAB_URL="[https://gitlab.com](https://gitlab.com)"

# The ID of a top-level group where you have Owner permissions.
# This will be used as the default parent for creating new groups/projects.
PARENT_GROUP_ID="12345678"
Note: This .env file is included in .gitignore and should never be committed to version control.5. UsageOnce the setup is complete, you can run the application with the following command:python frontend.py
