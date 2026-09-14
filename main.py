import cmd

class ChessCLI(cmd.Cmd):
    intro = "Welcome to Chess CLI! Type help or ? to list commands."
    prompt = "chess> "

    def do_clear(self, arg):
        """Clear the screen."""
        import os
        os.system("cls" if os.name == "nt" else "clear")

    def do_exit(self, arg):
        """Exit the shell."""
        return True


if __name__ == "__main__":
    ChessCLI().cmdloop()
