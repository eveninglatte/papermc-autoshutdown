## PaperMC auto-shutdown script
This is a small Python script I've written to be able to automate deallocating my PaperMC virtual machine if there was no one playing at the moment.
Along with it there is a startup shellscript (`startup.sh`) meant to be executed as a cronjob and an Ansible playbook (`mc_playbook.yaml`) to set it all up.

### How it works
- `startup.sh` spawns a new tmux session with PaperMC on the left side, and `stopper.py` on the right side. It redirects the output of PaperMC to `stopper.py` via `tmux pipe-pane` command piping to a named pipe, which in turn gets redirected to `stopper.py`. It also redirects the stdout and stderr of `stopper.py` to a logfile (whose location is defined in `vars.yaml`).
- `stopper.py` reads from standard input and counts the number of active players. If that number drops to 0, it starts a timer. If the timer is not cancelled by a player join and it finishes, it starts a deallocation procedure (dealloc_vm). Since I've hosted my virtual machine on Azure, I've set up a small Azure Logic App that deallocates the virtual machine on a HTTP GET request (hence `dealloc_url` in `vars.yaml`).

### How to use it (if you want to)
I will assume you know how to use Ansible. If you don't, Ansible docs are one of the best I've come across: https://docs.ansible.com/

Just change the necessary variables in `vars.yaml` and `mc_playbook.yaml`. All of them start with *your_*.
I would also advise to skim through the rest of the variables, not all of the default values are guaranteed to be fitting for your usecase.

### Known issues
- PaperMC's console log timestamp doesn't match system time (and therefore scripts' logfiles timestamps, which can lead to confusion reviewing those)
