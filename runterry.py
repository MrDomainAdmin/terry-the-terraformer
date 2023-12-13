#!/usr/bin/env python3

import os
import sys
from prompt_toolkit import PromptSession, completion, prompt
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
from prompt_toolkit.completion.base import Completer
from prompt_toolkit.document import Document
from prompt_toolkit.shortcuts import print_formatted_text
from completerUtil import ServerCompleter, DomainCompleter
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
type_completer = WordCompleter(["server", "domain"])


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
            command = f"./terry.py -f -o {project_name} {action} "
            while True:
                server_type = session.prompt(
                    f"Create a server or a domain? ",
                    completer=completion.FuzzyCompleter(type_completer),
                )
                match server_type:
                    case "server":
                        print(
                            """
  -p, --provider [aws|digitalocean|azure|google|linode]
                                  The cloud provider to use when creating the
                                  server  [required]
  -t, --type [bare|categorize|teamserver|lighthouse|redirector|mailserver]
                                  The type of server to create  [required]
  -sN, --name TEXT                Name of the server (used for creating
                                  corresponding DNS records if you use the
                                  "domain" command)
  -cT, --container TEXT           Containers to install onto the server (must
                                  be defined in container_mappings.yml to be
                                  used)
  -rT, --redirector_type [http|https|dns|custom]
                                  Type redirector to build (options are
                                  ['http', 'https', 'dns', 'custom'])
  -r2, --redirect_to TEXT         Name / UUID of server to redirect to (or
                                  just a FQDN / IP address for static
                                  redirection)
  -dI, --domain_to_impersonate TEXT
                                  FQDN of the domain to impersonate when
                                  traffic that doesn't match your C2
                                  redirection rules hits a redirector (or just
                                  domain to impersonate for categorization
                                  server)
  -d, --fqdn TEXT                 Domain and registrar to use in creation of
                                  an A record for the resource formatted as
                                  "<domain>:<registrar>" (Example: domain
                                  example.com with registrar aws should be
                                  "example.com:aws)"
"""
                        )
                        server_options = session.prompt(
                            f"Enter options for server ",
                            completer=completion.FuzzyCompleter(ServerCompleter()),
                        )
                    case "domain":
                        print(
                            """
  -p, --provider [aws|digitalocean|azure|google|linode|namecheap|cloudflare|godaddy]
                                  The cloud/infrastructure provider to use
                                  when creating the server  [required]
  -d, --domain TEXT               FQDN to use in creation of an record type
                                  "<type>" (if no subdomain provided, the root
                                  will be used)  [required]
  -t, --type TEXT                 The type of record to create
  -v, --value TEXT                Value of the record (use this if you have a
                                  STATIC DNS record that does not depend on
                                  dynamic data returned from Terraform)
  -sN, --server_name TEXT         Name / UUID of the server resource whose
                                  public IP that you want to populate the
                                  value of the record (a resource with this
                                  name / uuid must exist in the build)
                              """
                        )
                        server_options = session.prompt(
                            f"Enter options for domain ",
                            completer=completion.FuzzyCompleter(DomainCompleter()),
                        )
                command += f"{server_type} {server_options} "
                response = prompt("Do you want to add more servers/domains? yes/no: ")
                if response.lower() == "yes" or response.lower() == "y":
                    continue
                elif response.lower() == "no" or response.lower() == "n":
                    break
                else:
                    print("Please provide a valid response: y/yes/n/no")
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
