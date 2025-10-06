import os
import gitlab

# Obatin env
private_token = os.environ.get("GITLAB_PRIVATE_TOKEN")
gitlab_url = os.environ.get("GITLAB_URL")
project_name = os.environ.get("CI_PROJECT_NAME")
project_id = os.environ.get("CI_PROJECT_ID")
project_url = os.environ.get("CI_PROJECT_URL")
commit_sha = os.environ.get("CI_COMMIT_SHA")
commit_short_sha = os.environ.get("CI_COMMIT_SHORT_SHA")
commit_author_id = os.environ.get("GITLAB_USER_ID")

# Connect to the gitlab instance
try:
    gl = gitlab.Gitlab(gitlab_url, private_token)
    gl.auth()
    print("authenticated")
    project = gl.projects.get(project_id)
    commit_url = f"{project_url}/-/commit/{commit_sha}"
    issue = project.issues.create({'title': f"Commit ({commit_short_sha}) in {project_name} ({project_id}) failed",
                               'description': f"Pipeline failed. Please review commit in {commit_url}",
                               'labels': ['bug', 'workflow::to-do']})
    print("issue created succesfully")
    # Assign to commit author
    issue.assignee_ids = [commit_author_id]
    issue.save()
    print("issue assigned to bboyce12")
except gitlab.exceptions.GitlabError as e:
    print(f"Error: {e}")
    exit(1)
