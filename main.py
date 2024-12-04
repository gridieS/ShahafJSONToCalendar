import cmd
import shahaf_helper


class MainCli(cmd.Cmd):
    prompt = ">> "
    intro = """Type "help" for a list of the available commands.
    To get started:

    Enter 'url <shahaf-timetable-url>' to choose your url
    Enter 'list' to get the list of the available classes
    Enter 'class <class-name>' to choose one of the classes
    Enter 'insert' to insert the chosen class timetable into your calendar"""

    def __init__(self):
        super().__init__()
        self.chosen_url: str = ""
        self.class_str: str = ""
        self.cur_class: str = ""
        self._class_to_code: dict[str, int] = {}

    def precmd(self, line):
        if (
            line.split()[0] == "class"
            or line.split()[0] == "list"
            or line.split()[0] == "insert"
        ) and self.chosen_url == "":
            print("You must set a url before entering other commands!")
            return ""
        return line

    def do_quit(self, line):
        """Exit the command loop."""
        return True

    def do_exit(self, line):
        """Exit the command loop."""
        return True

    def do_url(self, line):
        """Choose a Shahaf url."""
        if line == "":
            print(self.chosen_url)
            return
        self.chosen_url = line
        self.class_str = ""
        for class_dict in shahaf_helper.get_classes(self.chosen_url):
            self._class_to_code[class_dict["className"]] = class_dict["classNum"]
            self.class_str += class_dict["className"] + ", "

    def do_list(self, line):
        """List the available classes."""
        print(self.class_str)

    def do_class(self, line):
        """Choose a class from the list command."""
        if line == "":
            print(self.cur_class)
            return
        if self._class_to_code.get(line):
            self.cur_class = line
            return

        print(
            f"'{line}' was not found in the class list. Enter 'list' again to see the available classes"
        )

    def do_insert(self, line):
        """Insert the chosen class timetable into your calendar."""
        if self.cur_class == "":
            print(
                "You have to select a class using 'class <class-name>' before using this command"
            )
            return

        shahaf_helper.insert_timetable_to_calendar(
            self.chosen_url, self._class_to_code[self.cur_class]
        )


def main():
    # Execute main function for command line friendly interface
    MainCli().cmdloop()


if __name__ == "__main__":
    main()
