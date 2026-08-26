import subprocess
from datetime import datetime


def git_save():
    # Change this if the script isn't sitting inside your git folder
    repo_path = "."

    commands = [
        ["git", "add", "-A"],
        ["git", "commit", "-m", f"update {datetime.now():%Y-%m-%d %H:%M}"],
        ["git", "push"],
    ]

    for cmd in commands:
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        print(f"$ {' '.join(cmd)}")
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            # "nothing to commit" isn't a real failure - just stop there quietly
            if "nothing to commit" in result.stderr:
                continue
            print("Stopped - something went wrong above.")
            return

    print("Done - pushed to GitHub.")


if __name__ == "__main__":
    git_save()
