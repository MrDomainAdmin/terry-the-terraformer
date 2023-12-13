from prompt_toolkit.completion import Completer, Completion, FuzzyCompleter


class ServerCompleter(Completer):
    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()

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


class DomainCompleter(Completer):
    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        words = word.split()
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
