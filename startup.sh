#!/bin/bash

# BEGIN ANSIBLE MANAGED VARIABLES
# the ansible managed variables will be pasted here!
# END ANSIBLE MANAGED VARIABLES

MC_START="sudo -u $MC_USER java -Xmx$RAM_AMT -Xms$RAM_AMT -jar $MC_EXEC --nogui"

# for logging purposes
PS4="[\$(date '+%F %T')]"
set -x

# these checks are necessary since tmux send-keys just sends whatever its told to send
# and reports success even if the command sent fails

## check for $MC_USER and java installed
grep -F $MC_USER /etc/passwd || (echo "E: no user $MC_USER found" > /dev/stderr && exit 1)
which java || (echo "E: no java installed" > /dev/stderr && exit 1)
## check for $SCRIPT_HOME, $MC_EXEC, $SCRIPT_EXEC, $PIPE_PATH
if [ ! -d $SCRIPT_HOME ] || [ ! -f $MC_EXEC ] || [ ! -x $SCRIPT_EXEC ] || [ ! -p $PIPE_PATH ] || [ ! -w $PIPE_PATH ]; then
	echo "E: one or more of the following files/directories are missing: \
	$SCRIPT_HOME \
	$MC_EXEC \
	$SCRIPT_EXEC \
	$PIPE_PATH (must be a named pipe with rw access)" > /dev/stderr
	exit 1
fi

# activate new session and split it horizontally
tmux new-session -c $MC_HOME -s $SESSION_NAME -d
tmux split-window -h -t $SESSION_NAME:0 -c $MC_HOME -d

# start the script with tmux session name as an argument and with pipe output being redirected to it
tmux send-keys -t $SESSION_NAME:0.1 "python3 -u $SCRIPT_EXEC < $PIPE_PATH 2>&1 | tee -a $SCRIPT_LOGFILE" Enter

# pipe-pane should be bef starting mc_serv cuz otherwise the python script may miss "Done "
# either pipe-pane or script works
# but script needs to be manually exited whereas pipe-pane closes along with the tmux session
tmux pipe-pane -t $SESSION_NAME:0.0 "cat > $PIPE_PATH"
#tmux send-keys -t $SESSION_NAME:0.0 "script -qf $PIPE_PATH" Enter
tmux send-keys -t $SESSION_NAME:0.0 "$MC_START" Enter
