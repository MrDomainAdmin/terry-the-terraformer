import os
import sys
from prompt_toolkit import PromptSession, completion, prompt
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion.base import Completer
from prompt_toolkit.document import Document
from prompt_toolkit.shortcuts import print_formatted_text
from completerUtil import CustomCompleter
import subprocess
import threading
import selectors
import termios


class TimeoutOccurred(Exception):
    pass


def inputimeout(prompt="", timeout=5):
    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ)
    events = sel.select(timeout)

    if events:
        key, _ = events[0]
        input_text = key.fileobj.readline()
        return input_text
    else:
        raise TimeoutOccurred


def runprocess(command):
    proc = subprocess.Popen(
        command,
        text=True,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
    )
    # Create and start the threads
    output_thread = threading.Thread(target=read_output, args=(proc,))
    input_thread = threading.Thread(target=send_input, args=(proc,))
    output_thread.start()
    input_thread.start()
    # Wait for the command to finish (optional)
    proc.wait()
    output_thread.join()
    input_thread.join()


# Function to read and print the program's output
def read_output(proc):
    while proc.poll() is None:
        # line = proc.stdout.readline()
        line = proc.stdout.read(1)
        if line == "" and proc.poll() != None:
            break
        sys.stdout.write(line)
        sys.stdout.flush()
    return


# Function to send user input to the program
def send_input(proc):
    while proc.poll() is None:
        try:
            user_input = inputimeout(prompt="", timeout=1)
        except TimeoutOccurred:
            continue
        if user_input:
            proc.stdin.write(user_input)
            proc.stdin.flush()
    return


# Custom completer for the projectname option.
class ProjectNameCompleter(Completer):
    def get_completions(self, document, complete_event):
        deployments_dir = (
            "deployments"  # Specify the path to your deployments directory
        )
        projects = [
            entry
            for entry in os.listdir(deployments_dir)
            if os.path.isdir(os.path.join(deployments_dir, entry))
        ]

        word_completer = WordCompleter([project for project in projects])
        return word_completer.get_completions(document, complete_event)


# Custom completer for 'add', 'create', 'destroy', and other options.
action_completer = WordCompleter(["add", "create", "destroy"])


def main():
    os.environ["PYTHONUNBUFFERED"] = "1"
    session = PromptSession(
        completer=completion.FuzzyCompleter(ProjectNameCompleter()),
        complete_while_typing=True,
        enable_system_prompt=True,
    )
    while True:
        try:
            project_name = session.prompt("Enter project name (projectname): ")
            project_name = project_name.strip()  # Remove leading/trailing whitespace

            if not project_name:
                print(
                    "Project name cannot be empty. Please enter a valid project name."
                )
                continue  # Ask for project name again if it's empty

            while True:  # Inner loop for action input
                action = session.prompt(
                    f"Enter action (add/create/destroy) for {project_name}: ",
                    completer=action_completer,
                )
                action = action.strip()  # Remove leading/trailing whitespace

                if not action:
                    print("Action cannot be empty. Please enter a valid action.")
                    continue  # Ask for action again if it's empty

                # Continue processing with the project name and action as needed
                break  # Exit the inner loop when both project name and action are valid

        except EOFError:
            break  # Handle EOFError to exit the loop gracefully

        formatted_output = f"You selected project: {project_name} and action: {action}"
        print_formatted_text(ANSI(formatted_output))

        # Check if the user selected "create" or add and provide server options accordingly.
        if action == "create" or action == "add":
            server_options = session.prompt(
                f"Enter options starting with server or domain: ",
                completer=completion.FuzzyCompleter(CustomCompleter()),
            )
            while True:
                response = prompt("Do you want to add more servers/domains? yes/no: ")
                if response.lower() == "yes" or response.lower() == "y":
                    server_options += " " + session.prompt(
                        f"Enter options starting with server or domain: ",
                        completer=completion.FuzzyCompleter(CustomCompleter()),
                    )
                elif response.lower() == "no" or response.lower() == "n":
                    break
                else:
                    print("Please provide a valid response: y/yes/n/no")
            command = f"./terry.py -f -o {project_name} {action} {server_options}"
            runprocess(command)
            sys.exit(0)

        if action == "destroy":
            response = prompt(
                f"Do you want to recursively destroy all files in {project_name}? yes/no: "
            )
            command = f"./terry.py -o {project_name} destroy"
            if response.lower() == "yes" or response.lower() == "y":
                command += " -r"
            runprocess(command)
            sys.exit(0)


if __name__ == "__main__":
    main()
