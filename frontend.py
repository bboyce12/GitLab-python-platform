import tkinter as tk
from tkinter import scrolledtext, ttk, Listbox, messagebox
import gitlab
import os, sys
from dotenv import load_dotenv
import backend
    
def gl_connection():
    gl = backend.connect_to_gitlab()
    if gl:
        print("Connection successful.")
        return gl
    else:
        print("Connection failed.")
        return None

def generate_report(project_id):
    """Placeholder for your report generation logic."""
    if not project_id.isdigit():
        return "Error: Project ID must be a number."
    return f"--- Report for Project {project_id} ---\n\nPipeline Success Rate: 95.2%\nAverage Deploy Time: 0:05:32\nOpen Issues: 12"

# --- Set up env variables window ---
class SettingsWindow(tk.Toplevel):
    """A Toplevel window for the user to enter their configuration."""
    def __init__(self, parent, on_success_callback):
        super().__init__(parent)
        self.on_success_callback = on_success_callback
        self.title("First-Time Setup")
        self.geometry("400x200")
        self.transient(parent) # Keep this window on top of the main one
        self.grab_set() # Modal behavior: user must interact with this window

        self.token = tk.StringVar()
        self.group_id = tk.StringVar()

        tk.Label(self, text="Please enter your GitLab details:").pack(pady=10)
        tk.Label(self, text="Personal Access Token:").pack()
        
        token_entry = tk.Entry(self, textvariable=self.token, width=50, show="*")
        token_entry.pack(pady=5)
        
        tk.Label(self, text="Parent Group ID:").pack()
        group_id_entry = tk.Entry(self, textvariable=self.group_id, width=50)
        group_id_entry.pack(pady=5)
        
        save_button = tk.Button(self, text="Save and Connect", command=self.save_and_close)
        save_button.pack(pady=10)
        
        self.wait_window() # Wait until this window is closed

    def save_and_close(self):
        token = self.token.get()
        group_id = self.group_id.get()
        if not token or not group_id:
            messagebox.showerror("Error", "Please fill in both fields.")
            return

        # Write the details to the .env file
        with open(".env", "w") as f:
            f.write(f"GITLAB_PRIVATE_TOKEN={token}\n")
            f.write(f"PARENT_GROUP_ID={group_id}\n")
            f.write("GITLAB_URL=https://gitlab.com")


        print("✅ Configuration saved to .env file.")
        self.on_success_callback()
        self.destroy()

# --- Terminal panel ---
class TerminalPanel(tk.Frame):
    class TextRedirector:
        def __init__(self, text_widget):
            self.text_widget = text_widget

        def write(self, text):
            self.text_widget.insert(tk.END, text)
            self.text_widget.see(tk.END)
            self.text_widget.update_idletasks()

        def flush(self):
            pass

    def __init__(self, parent):
        super().__init__(parent)
       # Create the ScrolledText widget
        self.text_widget = scrolledtext.ScrolledText(
            self, 
            wrap=tk.WORD, 
            bg="black", 
            fg="lightgreen", 
            font=("Consolas", 11)
        )
        self.text_widget.pack(expand=True, fill='both')

        # --- Redirect stdout ---
        self.redirector = self.TextRedirector(self.text_widget)
        sys.stdout = self.redirector
    
    def on_closing(self):
        """Restores stdout when the application is closing."""
        sys.stdout = sys.__stdout__

# --- Project Selection Panel ---
class ProjectSelectionPanel(tk.Frame):
    def __init__(self, parent, project_data, submit_callback):
        super().__init__(parent)
        self.projects = project_data
        self.submit_callback = submit_callback

        # --- Create the widgets inside this frame ---
        self.project_list_frame = tk.Frame(self)
        self.project_list_frame.pack(pady=5)
        self.current_project_option = tk.StringVar()
        tk.Label(self.project_list_frame, text="Project list:").pack()
        self.project_listbox = tk.Listbox(self.project_list_frame, width=50, height=5)
        self.project_listbox.pack(pady=(5, 20))
        for key, value in self.projects.items():
            self.project_listbox.insert(tk.END, f" {value} ({key})")
        

        # Extract Project ID from string and convert into int for handler function
        submit_button = tk.Button(self, text="Select this project", command=self.on_submit)
        submit_button.pack()

        self.current_project_label = tk.Label(self, text="Current project selection:", width=50, height=5)
        self.current_project_label.pack()

    def on_submit(self):
        project_id = int(self.project_listbox.get(tk.ACTIVE).split("(")[1].strip(")"))
        if self.submit_callback:
            self.submit_callback(project_id)
            self.current_project_label.config(text=f"Current project selection: {project_id}")

    def update_options(self, new_project_data):
        # Destroy all old widgets inside the frame
        for widget in self.project_list_frame.winfo_children():
            widget.destroy()
            print("destroyed old widgets")

        # Create the new list of display strings
        project_display_options = list(f"{details}({project_id})"
                                       for project_id, details in new_project_data.items())

        if not project_display_options:
            tk.Label(self.project_list_frame, text="No projects found.").pack()
            return
        
        # Create a new Listbox with the new options
        tk.Label(self.project_list_frame, text="Project list:").pack()
        self.project_listbox = tk.Listbox(self.project_list_frame, width=50, height=5)
        self.project_listbox.pack(pady=(5, 20))
        for key, value in new_project_data.items():
            self.project_listbox.insert(tk.END, f" {value} ({key})")
        #print("PANEL: Dropdown has been updated with new data.")

# --- Group Selection Panel ---
class GroupSelectionPanel(tk.Frame):
    def __init__(self, parent, group_data, submit_callback):
        super().__init__(parent)
        self.groups = group_data
        self.submit_callback = submit_callback

        # --- Create the widgets inside this frame ---
        self.dropdown_frame = tk.Frame(self)
        self.dropdown_frame.pack(pady=5)
        tk.Label(self.dropdown_frame, text="Group list:").pack()
        self.group_options = list(f"{group_detail['name']} ({group_id})" for group_id, group_detail in self.groups.items())
        self.current_group_option = tk.StringVar(value=self.group_options[0])
        dropdown = tk.OptionMenu(self.dropdown_frame, self.current_group_option, *self.group_options)
        dropdown.pack()
        self.current_group_id = self.current_group_option.get().split('(')[1].strip(')')
        self.current_group_label = tk.Label(self, text="Current group selection:", width=50, height=5)
        self.current_group_label.pack()
        submit_button = tk.Button(self, text="Select this group", command=self.on_submit)
        submit_button.pack(pady=20)

    def on_submit(self):
        if self.submit_callback:
            self.submit_callback(self.current_group_id)
            self.current_group_label.config(text=f"Current group selection: {self.current_group_id}")

    def update_options(self, new_group_data):
        # Destroy all old widgets inside the frame
        for widget in self.dropdown_frame.winfo_children():
            widget.destroy()

        # Create the new list of display strings
        group_display_options = list(f"{details['name']} ({group_id})" 
                                     for group_id, details in new_group_data.items())

        if not group_display_options:
            tk.Label(self.dropdown_frame, text="No groups found.").pack()
            return

        # Set a default value for the StringVar
        self.current_group_option.set(group_display_options[0])
        
        # Create a new OptionMenu with the new options
        new_dropdown = tk.OptionMenu(self.dropdown_frame, self.current_group_option, *group_display_options)
        new_dropdown.pack()
        print("PANEL: Dropdown has been updated with new data.")

# --- GUI Application ---
class GitLabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GitLab Analytics Dashboard")
        self.root.geometry("1000x800")

        # Connect to gitlab instance
        self.gl = gl_connection()

        # Close the app if connection fails and open settings windo
        if not self.gl:
            print("Opening settings window...")
            SettingsWindow(root, on_success_callback=self.finish_setup)

        # Load env variables
        self.parent_group_id = os.environ.get("PARENT_GROUP_ID")

        # Set up necessary variables in GitLab
        self.variable_setup()

        # Retrieving Group data
        self.groups = {}
        self.fetch_group_data()

        # Current selected group ID
        self.current_group_id = None

        # Retrieving Projects data
        self.projects = {}
        self.fetch_project_data()

         # Current selected project ID
        self.current_project_id = tk.StringVar()

        # --- Load project group data ---
        self.current_project_id.trace_add('write', self.handler_fetch_project_group_data)

        # Create and place tabs window
        self.notebook = ttk.Notebook(self.root)

        # Create tabs
        self.create_group_tab = tk.Frame(self.notebook)
        self.user_management_tab = tk.Frame(self.notebook)
        self.create_project_tab = tk.Frame(self.notebook)
        self.analytics_tab = tk.Frame(self.notebook)
        self.project_list_tab = tk.Frame(self.notebook)
        self.notebook.add(self.create_group_tab, text='Create Group')
        self.notebook.add(self.user_management_tab,text='User Management')
        self.notebook.add(self.create_project_tab, text='Create Project')
        self.notebook.add(self.project_list_tab, text='Project List')
        self.notebook.add(self.analytics_tab, text='Analytics')

     # --- Populate each tab with its specific widgets ---
        self.populate_create_group_tab()
        self.populate_create_project_tab()
        self.populate_analytics_tab()
        self.populate_project_list_tab()
        self.populate_user_management_tab()

        # Add event listener for tab changes
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Create central terminal panel
        TerminalPanel(self.root).pack(expand=True, fill='both', padx=10, pady=10)\
        
    def on_tab_changed(self, event):
        select_tab =   event.widget.tab('current')['text']
        if select_tab == "User Management":
            self.fetch_group_data()
            self.user_management_group_selection.update_options(self.groups)
            print("User Management tab selected, group data refreshed.")
        elif select_tab == "Create Project":
            self.fetch_group_data()
            self.create_project_group_selection.update_options(self.groups)
            print("Create Project tab selected, group data refreshed.")
        elif select_tab == "Project List":
            self.fetch_project_data()
            self.project_list_project_selection.update_options(self.projects)
            print("Project List tab selected, project data refreshed.")
        elif select_tab == "Analytics":
            self.fetch_project_data()
            self.analytics_project_selection.update_options(self.projects)
            print("Analytics tab selected, project data refreshed.")


    def fetch_group_data(self):
        self.groups = {}
        project_list = []
        groups = backend.list_groups(gl=self.gl)
        for group in groups:
            projects = group.projects.list(get_all=True)
            if projects:
                for project in projects:
                    project_list.append({project.id: project.name})
            self.groups[group.id] = {"name": group.name, "projects": project_list}

    def fetch_project_data(self):
        self.projects = {}
        projects = backend.list_projects(gl=self.gl)
        for project in projects:
            self.projects[project.id] = project.name_with_namespace

    def finish_setup(self):
        print("In finish setup function...")
        self.gl = gl_connection()
        if self.gl:
            self.root.deiconify()
        else:
            # If it still fails, show an error and close for real
            messagebox.showerror("Failed", "Connection still failed. Exiting.")
            self.root.destroy()

    def variable_setup(self):
        token = os.environ.get("GITLAB_PRIVATE_TOKEN")
        if backend.variable_setup(self.gl, self.parent_group_id, token):
            print("✅ Variables set up successfully.")
        else:
            print("❌ Failed to set up variables/ variables already exist.")

    def populate_create_group_tab(self):
        tk.Label(self.create_group_tab, text="Group Name:").pack(pady=(20, 5))
        name_entry = tk.Entry(self.create_group_tab, width=50)
        name_entry.pack()
        submit_button = tk.Button(self.create_group_tab, text="Create Group" , command=lambda: backend.create_group(self.gl, name_entry.get(), self.parent_group_id))
        submit_button.pack(pady=20)

    def populate_user_management_tab(self):
        self.ACCESS_LEVEL_MAP = {
            "GUEST": gitlab.const.AccessLevel.GUEST,
            "REPORTER": gitlab.const.AccessLevel.REPORTER,
            "DEVELOPER": gitlab.const.AccessLevel.DEVELOPER,
            "MAINTAINER": gitlab.const.AccessLevel.MAINTAINER
        }
        tk.Label(self.user_management_tab, text="User Management Panel").pack(pady=10)
        self.user_management_group_selection = GroupSelectionPanel(self.user_management_tab,
                            group_data=self.groups,
                            submit_callback=self.handler_group_selection)
        self.user_management_group_selection.pack(expand=True, fill="both", padx=10, pady=5)
        submit_button = tk.Button(self.user_management_tab, text="List users in group", command=lambda: backend.list_user_in_group(self.gl, self.current_group_id))
        submit_button.pack(padx=20)
        tk.Label(self.user_management_tab, text="User ID:").pack(pady=10)
        name_entry = tk.Entry(self.user_management_tab, width=50)
        name_entry.pack()
        options = list(self.ACCESS_LEVEL_MAP.keys())
        self.user_access_level = tk.StringVar(value=options[0])
        dropdown = tk.OptionMenu(self.user_management_tab, self.user_access_level, *options)
        dropdown.pack()
        submit_button = tk.Button(self.user_management_tab, text="Add/ remove user", command=lambda: self.handler_user_add_remove(group_id=self.current_group_id, user_id=name_entry.get(), access_level=self.ACCESS_LEVEL_MAP[self.user_access_level.get()]))
        submit_button.pack(pady=20)        
        submit_button = tk.Button(self.user_management_tab, text="Change user role", command=lambda: self.handler_change_user_role(group_id=self.current_group_id, user_id=name_entry.get(), new_access_level=self.user_access_level.get()))
        submit_button.pack(pady=20)
    
    def populate_project_list_tab(self):
        self.project_list_project_selection = ProjectSelectionPanel(
            self.project_list_tab,
            project_data=self.projects, 
            submit_callback=self.handler_project_selection)
        self.project_list_project_selection.pack(expand=True, fill='both', padx=10, pady=5)
        submit_button = tk.Button(self.project_list_tab, text="See project summary", command=lambda: backend.get_project_summary(backend.get_project_by_id(self.gl, self.current_project_id.get())))
        submit_button.pack(pady=0)

         # --- Main content frame for the listboxes ---
        content_frame = tk.Frame(self.project_list_tab, padx=10, pady=10)
        content_frame.pack(expand=True, fill='both')

        # --- Left Frame: Not Shared ---
        left_frame = tk.Frame(content_frame)
        left_frame.pack(side='left', expand=True, fill='both', padx=5)
        tk.Label(left_frame, text="Available to Share").pack()
        self.unshared_listbox = Listbox(left_frame, selectmode='single', exportselection=False)
        self.unshared_listbox.pack(expand=True, fill='both')

        # --- Middle Frame: Control Buttons ---
        middle_frame = tk.Frame(content_frame, padx=10)
        middle_frame.pack(side='left', fill='y', anchor='center')
        tk.Button(middle_frame, text="Share ->", command=self.handler_share_selected_group).pack(pady=5)
        tk.Button(middle_frame, text="<- Unshare", command=self.handler_unshare_selected_group).pack(pady=5)

        # --- Right Frame: Already Shared ---
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side='left', expand=True, fill='both', padx=5)
        tk.Label(right_frame, text="Already Shared With").pack()
        self.shared_listbox = Listbox(right_frame, selectmode='single', exportselection=False)
        self.shared_listbox.pack(expand=True, fill='both')


    def populate_create_project_tab(self):
        """Adds widgets to the 'Create Project' tab."""
        tk.Label(self.create_project_tab, text="Project Name:").pack(pady=(20, 5))
        name_entry = tk.Entry(self.create_project_tab, width=50)
        name_entry.pack()

        self.create_project_group_selection = GroupSelectionPanel(self.create_project_tab,
                            group_data=self.groups,
                            submit_callback=self.handler_group_selection)
        self.create_project_group_selection.pack(expand=True, fill="both", padx=10, pady=5)

        submit_button = tk.Button(self.create_project_tab, text="Create Project", command=lambda: backend.create_project(self.gl, name_entry.get(), self.current_group_id))
        submit_button.pack(pady=20)

    def populate_analytics_tab(self):
        """Adds widgets to the 'Analytics' tab."""
        self.analytics_project_selection = ProjectSelectionPanel(self.analytics_tab, 
                              project_data=self.projects,
                              submit_callback=self.handler_project_selection)
        self.analytics_project_selection.pack(expand=True, fill='both', padx=10, pady=5)
        tk.Label(self.analytics_tab, text="Select Report Type:").pack(pady=(20, 5))
        options = ["Pipeline Success Rate", "Pipeline Run Time", "Issue Completion"]
        self.analytics_report_type = tk.StringVar(value=options[0])
        dropdown = tk.OptionMenu(self.analytics_tab, self.analytics_report_type, *options)
        dropdown.pack()

        submit_button = tk.Button(self.analytics_tab, text="Generate Report", command = self.run_analytics)
        submit_button.pack(pady=20)

    def create_widgets(self):
        # Frame for input
        input_frame = tk.Frame(self.root, pady=10)
        input_frame.pack()

        # Label for the entry field
        self.label = tk.Label(input_frame, text="Enter Project ID:")
        self.label.pack(side=tk.LEFT, padx=5)

        # Entry field for the user to type the project ID
        self.project_id_entry = tk.Entry(input_frame, width=20)
        self.project_id_entry.pack(side=tk.LEFT, padx=5)

        # Button to trigger the report
        self.generate_button = tk.Button(input_frame, text="Generate Report", command=self.run_report)
        self.generate_button.pack(side=tk.LEFT, padx=5)

        # Scrolled text box to display the output
        self.output_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=20)
        self.output_text.pack(pady=10, padx=10)

    def run_analytics(self):
        report_type = self.analytics_report_type.get()
        print(f"Generating {report_type} report...")
        if report_type == "Pipeline Success Rate":
            data = backend.pipeline_successful_report(self.gl, self.current_project_id.get())
        elif report_type == "Pipeline Run Time":
            data = backend.pipeline_run_time_report(self.gl, self.current_project_id.get())
        elif report_type == "Issue Completion":
            data = backend.issue_completion_report(self.gl, self.current_project_id.get())

    def run_report(self):
        # Get the project ID from the entry field
        project_id = self.project_id_entry.get()
        
        # Clear the old output
        self.output_text.delete('1.0', tk.END)
        
        if not project_id:
            self.output_text.insert(tk.END, "Please enter a Project ID.")
            return

        # Show a "loading" message
        self.output_text.insert(tk.END, f"Generating report for project {project_id}...")
        self.root.update_idletasks() # Update the GUI to show the message

        # Run your actual report-generating function
        report_data = gl_connection()
        gl = backend.connect_to_gitlab()

        projects = backend.list_projects(gl=gl)


        # Display the final report
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert(tk.END, report_data)
        for project in projects:
            self.output_text.insert(tk.END, f"Project: {project.name_with_namespace}\n")
            self.output_text.insert(tk.END, f"ID: {project.id}\n")
            self.output_text.insert(tk.END, f"Description: {project.description}\n")
            self.output_text.insert(tk.END, "-" * 40 + "\n")

    def handler_project_selection(self, project_id):
        print(f"Main app received project ID: {project_id}")
        self.current_project_id.set(project_id)
        print(f"Current project ID updated to: {self.current_project_id.get()}")
    
    def handler_group_selection(self, group_id):
        print(f"Now chosen group {group_id}")
        self.current_group_id = group_id
    
    def handler_user_add_remove(self, group_id, user_id, access_level):
        print(f"Now adding/ removing user {user_id} to group {group_id} with access level {access_level}")
        if backend.checker_user_in_group(self.gl, group_id, user_id):
            backend.remove_user_from_group(self.gl, user_id, group_id)
        else:
            backend.add_user_to_group(self.gl, user_id, group_id, access_level)

    def handler_fetch_project_group_data(self, *args):
        print("Fetching project group data...")
        # Clear existing listboxes
        self.unshared_listbox.delete(0, tk.END)
        self.shared_listbox.delete(0, tk.END)
        # Fetch and populate listboxes
        project_id = self.current_project_id.get()
        project, all_groups, shared_groups = backend.fetch_project_group_data(self.gl, project_id)
        print(shared_groups)
        # Create a set of shared group IDs for quick lookup
        shared_groups_id = {group['group_id'] for group in shared_groups}
        for group in all_groups:
            if group.id not in shared_groups_id:
                self.unshared_listbox.insert(tk.END, f"{group.name} ({group.id})")
        for group in shared_groups:
            self.shared_listbox.insert(tk.END, f"{group['group_name']} ({group['group_id']})")

    def handler_share_selected_group(self):
        selection = self.unshared_listbox.curselection()
        print(f"Selected indices in unshared listbox: {selection}")
        if not selection:
            messagebox.showwarning("No Selection", "Please select a group to share.")
            return
        selected_group_id = self.unshared_listbox.get(selection[0]).split('(')[1].strip(')')
        print(f"Sharing project {self.current_project_id.get()} with group {selected_group_id}")
        backend.share_project_with_group(self.gl, self.current_project_id.get(), selected_group_id)

        # Refresh the listboxes
        self.handler_fetch_project_group_data()

    def handler_unshare_selected_group(self):
        selection = self.shared_listbox.curselection()
        print(f"Selected indices in shared listbox: {selection}")
        if not selection:
            messagebox.showwarning("No Selection", "Please select a group to unshare.")
            return
        selected_group_id = self.shared_listbox.get(selection[0]).split('(')[1].strip(')')
        print(f"Unsharing project {self.current_project_id.get()} from group {selected_group_id}")
        backend.unshare_project_with_group(self.gl, self.current_project_id.get(), selected_group_id)

        # Refresh the listboxes
        self.handler_fetch_project_group_data()

    def handler_change_user_role(self, group_id, user_id, new_access_level):
        print(f"Now changing user {user_id} role in group {group_id} to access level {new_access_level}")
        if backend.change_member_access_level_in_group(self.gl, user_id, group_id, new_access_level):
            print(f"User {user_id} role changed successfully.")
        else:
            print(f"Failed to change user {user_id} role.")

# --- Main execution block ---
if __name__ == "__main__":
    # Set up the main window
    root = tk.Tk()
    # Create an instance of the app
    app = GitLabApp(root)
    # Start the GUI event loop
    root.mainloop()