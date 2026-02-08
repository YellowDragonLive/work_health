import subprocess
import os

def run_git_archive():
    cwd = r"x:\work_code\work_health"
    try:
        # Check if it's a git repo
        if not os.path.exists(os.path.join(cwd, ".git")):
            subprocess.run(['git', 'init'], cwd=cwd, check=True)
            
        subprocess.run(['git', 'add', '.'], cwd=cwd, check=True)
        # Using a generic commit message for the archive
        subprocess.run(['git', 'commit', '-m', "archive: save current state before weight_tracker integration"], cwd=cwd, check=True)
        
        # Check remote
        remote_check = subprocess.run(['git', 'remote'], cwd=cwd, capture_output=True, text=True)
        if "origin" in remote_check.stdout:
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=cwd, check=True)
            print("Successfully archived to remote.")
        else:
            print("Successfully archived locally (no remote configured).")
            
    except subprocess.CalledProcessError as e:
        print(f"Git execution failed: {e}")

if __name__ == "__main__":
    run_git_archive()
