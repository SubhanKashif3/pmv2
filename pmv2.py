import os
import sqlite3
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
from typing import Optional


class ProjectManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.create_database()

    def create_database(self):
        """Creates a database to store the base directory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_directory TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    def get_base_directory(self):
        """Fetches the base directory from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT base_directory FROM settings LIMIT 1;")
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        return None

    def set_base_directory(self, base_dir: str):
        """Sets the base directory in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM settings;")  # Clear existing entry
        cursor.execute("INSERT INTO settings (base_directory) VALUES (?);", (base_dir,))
        conn.commit()
        conn.close()

    def run_command(self, command: str, cwd: Optional[str] = None):
        """Runs a shell command in the specified directory."""
        try:
            subprocess.run(command, shell=True, check=True, cwd=cwd)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running command: {command}")
            print(e)

    def create_project(self, project_name: str, project_type: str):
        """Creates a new project of the specified type."""
        base_dir = self.get_base_directory()
        if not base_dir:
            messagebox.showerror("Error", "Base directory is not set.")
            return

        project_path = os.path.join(base_dir, project_name)

        if os.path.exists(project_path):
            messagebox.showerror("Error", f"Project directory {project_path} already exists.")
            return

        os.makedirs(project_path)
        messagebox.showinfo("Success", f"Created project directory at {project_path}.")

        if project_type == "expo":
            self.setup_expo_project(project_path)
        elif project_type == "vite":
            self.setup_vite_project(project_path)
        elif project_type == "python":
            self.setup_python_project(project_path)
        elif project_type == "node":
            self.setup_node_project(project_path)
        else:
            messagebox.showerror("Error", f"Unknown or unsupported project type: {project_type}")

    def setup_expo_project(self, project_path: str):
        """Sets up a new Expo React Native project."""
        self.run_command("npx create-expo-app .", cwd=project_path)
        messagebox.showinfo("Success", "Expo project setup complete.")

    def setup_vite_project(self, project_path: str):
        """Sets up a new Vite React project with TypeScript or JavaScript."""
        tech_stack = simpledialog.askstring("Vite Project", "Choose stack (js or ts):").strip().lower()
        
        if tech_stack == "ts":
            template = "react-ts"
        elif tech_stack == "js":
            template = "react"
        else:
            messagebox.showerror("Error", "Invalid choice. Please enter 'js' or 'ts'.")
            return

        self.run_command(f"npm create vite@latest . -- --template {template} --no-git", cwd=project_path)
        self.run_command("npm install", cwd=project_path)
        messagebox.showinfo("Success", f"Vite project ({tech_stack}) setup complete.")

    def setup_python_project(self, project_path: str):
        """Sets up a new Python project."""
        venv_path = os.path.join(project_path, "venv")
        self.run_command(f"python -m venv {venv_path}")
        messagebox.showinfo("Success", "Python virtual environment created.")
        messagebox.showinfo("Success", "Python project setup complete.")

    def setup_node_project(self, project_path: str):
        """Sets up a new Node.js project."""
        self.run_command("npm init -y", cwd=project_path)
        messagebox.showinfo("Success", "Node.js project setup complete.")

    def execute_command(self, project_name: str, command: str):
        """Executes a command in the specified project directory and opens a terminal."""
        base_dir = self.get_base_directory()
        if not base_dir:
            messagebox.showerror("Error", "Base directory is not set.")
            return

        project_path = os.path.join(base_dir, project_name)

        if not os.path.exists(project_path):
            messagebox.showerror("Error", f"Project directory {project_path} does not exist.")
            return

        # Open terminal in the directory and run the command
        if os.name == 'nt':  # Windows
            os.system(f'start cmd /k "cd /d {project_path} && {command}"')
        else:  # Linux or Mac
            os.system(f'gnome-terminal -- bash -c "cd {project_path} && {command}; exec bash"')

    def list_projects(self):
        """Lists all existing projects."""
        base_dir = self.get_base_directory()
        if not base_dir:
            messagebox.showerror("Error", "Base directory is not set.")
            return []

        projects = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        return projects

    def open_project_in_code(self, project_name: str):
        """Opens the project in Visual Studio Code."""
        base_dir = self.get_base_directory()
        if not base_dir:
            messagebox.showerror("Error", "Base directory is not set.")
            return

        project_path = os.path.join(base_dir, project_name)
        if os.path.exists(project_path):
            subprocess.run(f"code {project_path}", shell=True)
        else:
            messagebox.showerror("Error", f"Project {project_name} does not exist in {base_dir}.")

def main():
    db_path = "project_manager.db"  # SQLite database file for storing the base directory
    manager = ProjectManager(db_path)

    base_dir = manager.get_base_directory()

    if not base_dir:
        new_base_dir = simpledialog.askstring("Set Base Directory", "Enter the base directory:").strip()
        if os.path.exists(new_base_dir):
            manager.set_base_directory(new_base_dir)
            messagebox.showinfo("Success", f"Base directory set to {new_base_dir}")
        else:
            messagebox.showerror("Error", f"The directory {new_base_dir} does not exist.")
            return

    def create_project_ui():
        project_name = simpledialog.askstring("Create Project", "Enter project name:").strip()
        project_type = simpledialog.askstring("Create Project", "Enter project type (expo, vite, python, node):").strip()
        manager.create_project(project_name, project_type)

    def run_command_ui():
        projects = manager.list_projects()
        project_name = simpledialog.askstring("Select Project", f"Select project ({', '.join(projects)}):").strip()
        command = simpledialog.askstring("Run Command", "Enter the command to run:").strip()
        manager.execute_command(project_name, command)

    def open_in_vscode_ui():
        projects = manager.list_projects()
        project_name = simpledialog.askstring("Select Project", f"Select project ({', '.join(projects)}):").strip()
        manager.open_project_in_code(project_name)

    root = tk.Tk()
    root.title("Project Manager")
    root.geometry("400x300")

    frame = tk.Frame(root)
    frame.pack(padx=20, pady=20, expand=True)

    tk.Button(frame, text="Create New Project", command=create_project_ui).pack(pady=10)
    tk.Button(frame, text="Run Command in Project", command=run_command_ui).pack(pady=10)
    tk.Button(frame, text="Open Project in VS Code", command=open_in_vscode_ui).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()

