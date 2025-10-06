import os
import gitlab
import sys
import time
import functools
from dotenv import load_dotenv
from datetime import datetime, timedelta

# --- Configuration ---
# Project's actual ID
access_levels = {
        "GUEST": gitlab.const.AccessLevel.GUEST,
        "REPORTER": gitlab.const.AccessLevel.REPORTER,
        "DEVELOPER": gitlab.const.AccessLevel.DEVELOPER,
        "MAINTAINER": gitlab.const.AccessLevel.MAINTAINER
    }

# --- Timer decorator ---
def time_it(func):
    """
    A decorator that times the execution of a function.
    It returns origianl result of the function and prints the time taken to execute it.
    """
    # functools.wraps preserves the original function's metadata (name, docstring, etc.)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 1. Start the timer using a high-precision counter
        start_time = time.perf_counter()
        
        # 2. Run the original function and store its result
        result = func(*args, **kwargs)
        
        # 3. Stop the timer
        end_time = time.perf_counter()
        
        # 4. Calculate the duration
        duration = end_time - start_time
        
        # 5. Printing the time used
        print(f"--- Task '{func.__name__}' completed in {duration:.2f} seconds. ---")
        
        # Return ONLY the original result
        return result
        
    return wrapper


### 1. Connection and initial setup
@time_it
def connect_to_gitlab():
    load_dotenv()
    private_token = os.environ.get("GITLAB_PRIVATE_TOKEN")
    gitlab_url = os.environ.get("GITLAB_URL")

    """Connects to GitLab and runs the report."""
    try:
        # This just creates the object; no API call is made yet.
        gl = gitlab.Gitlab(gitlab_url, private_token=private_token)

        # This is the line that makes the API call to verify the token.
        # It will throw a GitlabError if the token is invalid or lacks permissions.
        gl.auth()
        print("Authentication successful! ✅")
        return gl
    except gitlab.exceptions.GitlabError as e:
        print(f"Authentication failed: {e}")

@time_it
def variable_setup(gl, namespace_id, token):
    try:
        group = gl.groups.get(namespace_id)
        # Set up private token as a group variable
        token_var = group.variables.create({'key': 'GITLAB_PRIVATE_TOKEN', 'value': token})
        if token_var:
            return True
        else:
            return False
    except gitlab.exceptions.GitlabError as e:
        print(f"Failed to create token variable in gitlab: {e}")


### 2. Template load
@time_it
def load_project_template(gl, project_id):
    try:
        project = gl.projects.get(project_id)
    except gitlab.exceptions.GitlabError as e:
        print(f"Error loading template project: {e}")
    if not project:
        print("❌ Project not found.")
        return
    # Add default files to the template project
    # 1. Define the files to be added and their local paths
    default_files = {
        '.gitlab-ci.yml': 'template/template.yml',
        '.gitignore': 'template/gitignore.txt',
        'cliff.toml': 'template/cliff.toml',
        'public/index.html': 'template/index.html',
        'create_failure_issue.py': 'template/create_failure_issue.py',
    }
    # 2. Read the content of the local file
    try:
        for repo_path, local_path in default_files.items():
            print(f"Reading content from {local_path}...")
            with open(local_path, "r") as f:
                file_content = f.read()
            file_data = {
            'file_path': repo_path,
            'branch': 'main',   
            'content': file_content,
            'commit_message': f'Add default CI/CD file {repo_path}'
        }

            # 3. Create the file using the API
            new_file = project.files.create(file_data)
            print(f"Successfully uploaded {local_path} to the template project {repo_path}...")

        print(f"✅ Successfully added all default files to the project {project.name_with_namespace}.")

    except FileNotFoundError:
        print(f"❌ Error: The {local_path} file was not found in the same directory as the script.")
    except gitlab.exceptions.GitlabError as e:
        print(f"❌ An error occurred while creating the file: {e.error_message}")


### 3. Project member management
@time_it
def list_members_in_project(project):
    # Get a list of all members in the project
        members = project.members.list(all=True)
        for member in members:
            print(f"  - User ID: {member.id}, Username: {member.username}, Access Level: {member.access_level}")

@time_it
def add_member_to_project(project, user_id, access_level):
    # Add a member to the project
    try:
        project.members.create({'user_id': user_id, 'access_level': access_level})
        print(f"Member with ID {user_id} added with access level {access_level}.")
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"Error adding member: {e}")

@time_it
def remove_member_from_project(project, user_id):
    # Remove a member from the project
    try:
        member = project.members.get(user_id)
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Error in retrieving user: {e}")
    try:
        member.delete()
        print(f"Member with ID {user_id} removed successfully.")
    except gitlab.exceptions.GitlabDeleteError as e:
        print(f"Error removing member: {e}")

# Change member access level in a project
@time_it
def change_member_access_level(project, user_id, new_access_level):
    try:
        member = project.members.get(user_id)
        try:
            member.access_level = access_levels[new_access_level]
            member.save()
            print(f"Access level for user ID {user_id} in project ID {project.id} changed to {new_access_level}.")
            return True
        except gitlab.exceptions.GitlabUpdateError as e:
            print(f"Error changing access level: {e}")
            return False
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Error in retrieving user: {e}")

# Change member access level in a group
@time_it
def change_member_access_level_in_group(gl, user_id, group_id, new_access_level):
    try:
        group = gl.groups.get(group_id)
        member = group.members.get(user_id)
        try:
            member.access_level = access_levels[new_access_level]
            member.save()
            print(f"Access level for user ID {user_id} in group ID {group_id} changed to {new_access_level}.")
            return True
        except gitlab.exceptions.GitlabUpdateError as e:
            print(f"Error changing access level: {e}")
            return False
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Error in retrieving user: {e}")


# Create a new group (subgroup only as gitlab blocked the creation of top-level groups via api)
@time_it
def create_group(gl, group_name, parent_id):
    try:
        group_path = f"test-subgroup-{os.urandom(4).hex()}" # Unique path to avoid errors
        group = gl.groups.create({'name': group_name, 'path': group_path, 'parent_id': parent_id})
        print(f"Group created successfully: {group.name}")
        return group
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"Error creating group: {e}")
        return None
    
# List groups
@time_it
def list_groups(gl):
    try:
        groups = gl.groups.list(owned=True, all=True)
        return groups
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Error retrieving groups: {e}")

# List members in a group
@time_it
def list_user_in_group(gl, group_id):
    try:
        group = gl.groups.get(group_id)
        members = group.members.list(all=True)
        for member in members:
            print(f"  - User ID: {member.id}, Username: {member.username}, Access Level: {member.access_level}")
    except gitlab.exceptions.GitlabGetError as e:
        print(f"Error retrieving group members: {e}")

# Checker function for user in a specific group
@time_it
def checker_user_in_group(gl, group_id, user_id):
    try:
        group = gl.groups.get(group_id)
        return group.members.get(user_id)
    except gitlab.exceptions.GitlabError as e:
        print(f"Error in checking user status in group: {e}/ User not found")

# Adding user to existing group
@time_it
def add_user_to_group(gl, user_id, group_id, access_level):
    try:
        group = gl.groups.get(group_id)
        member = group.members.create({'user_id': user_id, 'access_level': access_level})
        print(f"User with ID {user_id} added to group {group.name} with access level {access_level}.")
    except gitlab.exceptions.GitlabError as e:
        print(f"Error adding user to group: {e}")

# Removing user from existing group
@time_it
def remove_user_from_group(gl, user_id, group_id):
    try:
        group = gl.groups.get(group_id)
        group.members.delete(user_id)
        print(f"User with ID {user_id} removed from group {group.name}.")
    except gitlab.exceptions.GitlabError as e:
        print(f"Error removing user from group: {e}")


### 4. Project creation
@time_it
def create_project(gl, project_name, namespace_id):
    try:
        project = gl.projects.create({'name': project_name, 'namespace_id': namespace_id, 'initialize_with_readme': True})
        print(f"Project created successfully: {project.name_with_namespace}")
        # Create default project protected tag rule
        protected_tag = project.protectedtags.create({'name': 'v*', 'create_access_level': gitlab.const.AccessLevel.MAINTAINER})
        # Create default project tag
        tag = project.tags.create({
            'tag_name': 'v1.0.0',
            'ref': 'main'
        })
        load_project_template(gl, project.id)
        return project
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"Error creating project: {e}")
        return None


### 5. Project listing
@time_it
def list_projects(gl):
    # list all the projects that are owned by the account
    projects = gl.projects.list(owned=True, all=True)
    return projects
    for project in projects:
        print(f"Name: {project.name_with_namespace}")
    
@time_it
def get_project_by_id(gl, project_id):
    project = gl.projects.get(project_id)
    return project

@time_it
def get_project_summary(project):
    """Fetches and prints the summary for a given project."""
    print(f"\n--- Summary for {project.name_with_namespace} ---")

    # Fetch and print failing pipelines
    print("\n🚨 Failing Pipelines:")
    failing_pipelines = project.pipelines.list(status='failed', all=True)
    if failing_pipelines:
        for pipeline in failing_pipelines:
            print(f"  - ID: {pipeline.id} on branch '{pipeline.ref}'")
    else:
        print("  No failing pipelines found.")

    # Fetch and print open issues
    print("\n📝 Open Issues:")
    open_issues = project.issues.list(state='opened', all=True)
    if open_issues:
        for issue in open_issues:
            print(f"  - #{issue.iid}: {issue.title}")
    else:
        print("  No open issues found.")

    # Fetch and print recent commits
    print("\n💬 Recent Commits:")
    commits = project.commits.list(all=True, query_parameters={'per_page': 5})
    if commits:
        for commit in commits:
            print(f"  - {commit.short_id} by {commit.author_name}: {commit.title}")
    else:
        print(" No commits found.")

### 6. Project sharing
# Obtaining project group data
@time_it
def fetch_project_group_data(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        all_groups = gl.groups.list(owned=True, get_all=True)
        shared_groups = project.shared_with_groups
        return project, all_groups, shared_groups

    except gitlab.exceptions.GitlabError as e:
        print(f"Error retrieving project or groups: {e}")
        return None, None, None

# Share project with a group (Default to be maintainer)
@time_it
def share_project_with_group(gl, project_id, group_id):
    try:
        project = gl.projects.get(project_id)
        group = gl.groups.get(group_id)
        project.share(group.id, gitlab.const.AccessLevel.MAINTAINER)
        print(f"Project {project.name_with_namespace} shared with group {group.name}.")
    except gitlab.exceptions.GitlabError as e:
        print(f"Error sharing project with group: {e}")

# Unshare project with a  group
@time_it
def unshare_project_with_group(gl, project_id, group_id):
    try:
        project = gl.projects.get(project_id)
        group = gl.groups.get(group_id)
        project.unshare(group.id)
        print(f"Project {project.name_with_namespace} unshared from group {group.name}.")
    except gitlab.exceptions.GitlabError as e:
        print(f"Error unsharing project with group: {e}")

### 7. Analytics
@time_it
def issue_completion_report(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        closed_issues = project.issues.list(state='closed', all=True)

        # Calculate total number of closed issues
        total_closed_issues = len(closed_issues)
        print(total_closed_issues)

        total_duration = timedelta(days=0, hours=0)
        # Calculate total duration for closed issues iteratively
        for closed_issue in closed_issues:
            closed_time = closed_issue.closed_at
            created_time = closed_issue.created_at
            created_time_no_z = created_time.removesuffix('Z')
            closed_time_no_z = closed_time.removesuffix('Z')
            created_time_obj = datetime.fromisoformat(created_time_no_z)
            closed_time_obj = datetime.fromisoformat(closed_time_no_z)
            duration = closed_time_obj - created_time_obj
            print(f"  - #{closed_issue.iid}: {closed_issue.title} created at {closed_issue.created_at} and closed at {closed_issue.closed_at}, duration: {duration}")
            total_duration += duration
        print(f"Average duration to close a issue: {total_duration / total_closed_issues if total_closed_issues > 0 else 0}")
    except gitlab.exceptions.GitlabError as e:
        print(f"Error generating issue completion report: {e}")
        return None

@time_it
def pipeline_successful_report(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        pipelines = project.pipelines.list(get_all=True)
        total_pipeline_run = len(pipelines)
        total_successful_pipelines = 0

        for pipeline in pipelines:
            if pipeline.status == 'success':
                total_successful_pipelines += 1

        print(f"Pipeline run summary:")
        print(f"Total pipelines: {total_pipeline_run}")
        print(f"Successful pipelines: {total_successful_pipelines}")
        print(f"Successful rate: {round(total_successful_pipelines/ total_pipeline_run * 100 if total_pipeline_run > 0 else 0, 1)}%")
    except gitlab.exceptions.GitlabError as e:
        print(f"Error generating pipeline successful report: {e}")
@time_it
def pipeline_run_time_report(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        pipelines = project.pipelines.list(get_all=True)
        total_pipeline_run = len(pipelines)
        duration = timedelta(days=0, hours=0)
        for partial_pipeline in pipelines:
            full_pipeline = project.pipelines.get(partial_pipeline.id)
            started_time_obj = full_pipeline.started_at
            finished_time_obj = full_pipeline.finished_at
            if started_time_obj and finished_time_obj:
                started_time_no_z = started_time_obj.removesuffix('Z')
                finished_time_no_z = finished_time_obj.removesuffix('Z')
                started_time = datetime.fromisoformat(started_time_no_z)
                finished_time = datetime.fromisoformat(finished_time_no_z)
                duration += finished_time - started_time
                print(f"Pipeline starts at {started_time} and ends at {finished_time}")
        print(f"Average pipeline run time: {duration / total_pipeline_run if total_pipeline_run > 0 else 0}")
    except gitlab.exceptions.GitlabError as e:
        print(f"Error generating pipeline run time report: {e}")

def main():
    """Obtaining token from local env"""
    load_dotenv()
    private_token = os.environ.get("GITLAB_PRIVATE_TOKEN")
    gitlab_url = os.environ.get("GITLAB_URL")

    """Connects to GitLab and runs the report."""
    try:
        # This just creates the object; no API call is made yet.
        gl = gitlab.Gitlab(gitlab_url, private_token=private_token)

        # This is the line that makes the API call to verify the token.
        # It will throw a GitlabError if the token is invalid or lacks permissions.
        gl.auth()
        
        print("Authentication successful! ✅")

    except gitlab.exceptions.GitlabError as e:
        print(f"Authentication failed: {e}")
        # The script should exit here if authentication fails.
        exit(1)

    list_projects(gl)
    project = get_project_by_id(gl, PROJECT_ID)

    list_members_in_project(project)

    # Test Group Creation
    #create_group(gl, "Test Group", PARENT_GROUP_ID)

    # Test User Addition
    #add_user_to_group(gl, extra_member_user_id, 114130346, gitlab.const.AccessLevel.MAINTAINER)
    #print(f"✅ User with ID {extra_member_user_id} added to group 114130346.")


    # Test User Removal
    #remove_user_from_group(gl, extra_member_user_id, 114130346)
    #print(f"✅ User with ID {extra_member_user_id} removed from group 114130346.")

    # Test User Listing
    #list_user_in_group(gl, 114130346)

    # Test Project Listing
    #ist_projects(gl)

    #Test sharing project with group
    try:
        share_project_with_group(gl, PROJECT_ID, SUB_GROUP_ID)
        print(f"✅ Project {PROJECT_ID} shared with group {SUB_GROUP_ID}.")
    except Exception as e:
        print(f"Error sharing project with group: {e}")

    # Test unsharing project with group
    # unshare_project_with_group(gl, PROJECT_ID, SUB_GROUP_ID)
    
    # Test Project Retrieval
    # project = get_project_by_id(gl, PROJECT_ID)
    # if project:
    #     get_project_summary(project)

    #pipeline_run_time_report(gl, PROJECT_ID)
    create_project(gl, "Frontend_project5", FRONTEND_GROUP_ID)


    # Standard Python entry point
if __name__ == "__main__":
    main()