import platform
import subprocess
import time
import os


def get_terminal_command():
    system = platform.system().lower()
    if system == "windows":
        return ["start", "cmd", "/k"]
    elif system == "darwin":  # macOS
        return ["osascript", "-e", 'tell app "Terminal" to do script']
    elif system == "linux":
        # Try different terminal emulators
        if subprocess.run(["which", "gnome-terminal"], capture_output=True).returncode == 0:
            return ["gnome-terminal", "--"]
        elif subprocess.run(["which", "xterm"], capture_output=True).returncode == 0:
            return ["xterm", "-e"]
        elif subprocess.run(["which", "konsole"], capture_output=True).returncode == 0:
            return ["konsole", "-e"]
    raise OSError(f"Unsupported operating system or no terminal emulator found: {system}")


def launch_api(api_path):
    system = platform.system().lower()
    python_cmd = f"python {api_path}"

    try:
        if system == "windows":
            # For Windows, we need to use shell=True and the complete command
            full_command = f"start cmd /k {python_cmd}"
            subprocess.Popen(full_command, shell=True)

        elif system == "darwin":  # macOS
            # For macOS, we need to escape the command for AppleScript
            apple_script = f'tell app "Terminal" to do script "{python_cmd}"'
            subprocess.Popen(["osascript", "-e", apple_script])

        else:  # Linux
            # Get the appropriate terminal command
            terminal_cmd = get_terminal_command()
            # Combine the terminal command with the Python command
            full_command = terminal_cmd + [python_cmd]
            subprocess.Popen(full_command)

    except Exception as e:
        print(f"Error launching {api_path}: {e}")


def main():
    # List of API paths in order
    api_paths = [
        ".\\apiApplications\\AddressAPI.py",
        ".\\apiApplications\\AuthAPI.py",
        ".\\apiApplications\\GameManagerAPI.py",
        ".\\apiApplications\\QueueAPI.py",
        ".\\apiApplications\\GameAPI.py"
    ]

    if platform.system().lower() != "windows":
        api_paths = [path.replace("\\", "/") for path in api_paths]

    for api_path in api_paths:
        print(f"Launching {api_path}...")
        launch_api(api_path)
        time.sleep(2)

    print("All APIs have been launched in separate terminals.")
    print("Press Ctrl+C in each terminal window to stop the individual APIs.")


if __name__ == "__main__":
    main()

    import subprocess

    subprocess.run(["start", "cmd", "/k", "python .\service\ClientService.py"], shell=True)
    subprocess.run(["start", "cmd", "/k", "python .\service\ClientService.py"], shell=True)
    subprocess.run(["start", "cmd", "/k", "python .\service\ClientService.py"], shell=True)
    # subprocess.run(["start", "cmd", "/k", "python .\service\ClientService.py"], shell=True)
