import sys              # stderr, argv
import fileinput        # stdin iterable
import subprocess       # bash commands
import threading        # timer for stopping the server
import requests         # deallocating the vm via a logic app
import time             # time for debug log
from os import _exit    # a hacky way to exit the entire process when a thing in a thread fails


# you can make do without using using a class, i just find that a bit tidier
class InputWorker:
    def __init__(self, session_name, time_to_stop, dealloc_url, verbosity_lvl="warning"):
        self.session_name = session_name
        self.time_to_stop = time_to_stop
        self.dealloc_url = dealloc_url

        self.allowed_levels = ["error", "warning", "debug"]
        if verbosity_lvl not in self.allowed_levels:
            print("bad verbosity passed")
            _exit(1)
        else:
            self.verbosity_lvl = self.allowed_levels.index(verbosity_lvl)

        self.stdin = fileinput.input()
        self.players = []
        self.server_stopping = False
        self.stopping_timer = threading.Timer(300.0, self.server_stop_error)
        self.str_joined = " joined the game"
        self.str_left = " left the game"
        self.last_mess = ""

    def redefine_timer(self):
        self.timer = threading.Timer(self.time_to_stop, self.server_stop_flag)

    def process_line(self, line, str_replace):
        line_replaced = line[line.find("]: ") + 2:].replace(str_replace, "").replace(" \x1b[38;5;11m", "").replace("\x1b[0m\n", "")
        return line_replaced

    def print_players(self):
        self.print_mess(f"PLAYERS: \t {self.players}", 2)

    def print_mess(self, mess, lvl):
        # save last message before printing it
        self.last_mess = mess
        localtime = time.strftime("%H:%M:%S", time.localtime())
        if lvl <= self.verbosity_lvl:
            print(f"[{localtime}] {self.allowed_levels[lvl].upper()}: \t", mess, file=sys.stderr)
        if lvl == 0:
            # not a clean way to stop but its a CLI tool so whatever
            _exit(1)

    def dealloc_vm(self):
        self.print_mess("vm deallocation started", 1)
        r = requests.get(self.dealloc_url)
        if r.status_code != 200:
            self.print_mess("deallocation url can't be reached", 0)

    def server_stop_flag(self):
        self.server_stopping = True
        self.server_stop()

    def server_stop_error(self):
        self.print_mess("error while trying to stop an inactive server", 0)

    def server_stop(self):
        self.print_mess("server stopping started", 2)
        try:
            # stop the server
            subprocess.run(["tmux", "send-keys",
            "-t", self.session_name,
            "save-all", "Enter", "stop", "Enter"],
            check=True)
        except subprocess.CalledProcessError:
            self.server_stop_error()

    def start(self):
        self.print_vars()
        self.wait_for_start()
        self.log()

    def print_vars(self):
        self.print_mess(f"tmux session name is {self.session_name}", 2)
        self.print_mess(f"time to stop is {self.time_to_stop}", 2)
        self.print_mess(f"Dealloc url is {self.dealloc_url}", 2)

    def wait_for_start(self):
        self.print_mess("waiting for server start", 2)
        for line in self.stdin:
            if "Done" in line:
                self.print_mess("server start detected", 1)
                break

    def log(self):
        # define the timer for the 1st time
        self.redefine_timer()

        for line in self.stdin:
            if self.server_stopping:
                # if the server doesnt stop after 300.0s we can assume smth is wrong
                if not self.stopping_timer.is_alive():
                    self.stopping_timer.start()
                if "Closing Server" in line:
                    self.stopping_timer.cancel()
                    self.dealloc_vm()
                    break
                else:
                    continue

            # if the server_stopping flag is not set, then it must be a manual stop
            if "Closing Server" in line:
                self.print_mess("manual server stop detected, stopping script", 1)
                _exit(1)

            if self.str_joined in line:
                player_name = self.process_line(line, self.str_joined)
                self.players.append(player_name)
                self.print_mess("player join detected", 2)
                self.print_players()
                if self.timer.is_alive():
                    self.timer.cancel()
                    self.print_mess("sleep counter cancelled", 1)
                    self.redefine_timer();

            if self.str_left in line:
                player_name = self.process_line(line, self.str_left)
                self.players.remove(player_name)
                self.print_mess("player leave detected", 2)
                self.print_players()

            if not self.players:
                mess = "no players active detected"
                if self.last_mess != mess:
                    self.print_mess(mess, 2)
                if not self.timer.is_alive():
                    self.timer.start()
                    self.print_mess(f"sleep counter started, server stop in {self.time_to_stop}s", 1)


# BEGIN ANSIBLE MANAGED VARIABLES
# the ansible managed variables will be pasted here!
# END ANSIBLE MANAGED VARIABLES

logging = InputWorker(session_name, time_to_stop, dealloc_url, verbosity_lvl=verbosity_lvl)
logging.start()
