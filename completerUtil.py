from prompt_toolkit.completion import Completer, Completion


class CustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        words = word.split()

        # Check if the user is providing options for "server"
        if document.text.startswith("server"):
            if document.text.endswith("-p "):
                options = ["aws", "digitalocean", "azure", "google", "linode"]
                options.sort()
                for option in options:
                    yield Completion(option, start_position=-len(word))
                return
            if document.text.endswith("-t "):
                options = [
                    "bare",
                    "categorize",
                    "teamserver",
                    "lighthouse",
                    "redirector",
                    "mailserver",
                ]
                options.sort()
                for option in options:
                    yield Completion(option, start_position=-len(word))
                return
            if document.text.endswith("-r "):
                options = ["http", "https", "dns", "custom"]
                options.sort()
                for option in options:
                    yield Completion(option, start_position=-len(word))
                return

        # Check if the user is providing options for "domain"
        elif document.text.startswith("domain"):
            if document.text.endswith("-p "):
                options = [
                    "aws",
                    "azure",
                    "google",
                    "linode",
                    "namecheap",
                    "cloudflare",
                    "godaddy",
                ]
                options.sort()
                for option in options:
                    yield Completion(option, start_position=-len(word))
                return

        elif word.startswith("server") or word.startswith("domain"):
            pass
        else:
            options = ["server", "domain"]
            for option in options:
                yield Completion(option, start_position=-len(word))
            return
