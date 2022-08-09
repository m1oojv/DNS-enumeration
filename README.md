# Automated Reconnaissance Pipeline for DNS Enumeration and Scanning (Amass and Shodan)

## Installation
Ensure Amass and Shodan are installed.

1. run `apt install pipenv` as the virtual environment for python
2. run `pipenv install` to install luigi
3. run `pipenv shell` to enter and use the virtual environment!

Refer to [this](https://epi052.gitlab.io/notes-to-self/blog/2019-09-01-how-to-build-an-automated-recon-pipeline-with-python-and-luigi/) for more installation help.

## Command Execution

### Luigi command structure

With the `PYTHONPATH` setup, luigi commands take on the following structure (prepend `PYTHONPATH` if not exported from `.bashrc`):

`luigi --module PACKAGENAME.MODULENAME CLASSNAME *args`

You can get options for each module by running `luigi --module PACKAGENAME.MODULENAME CLASSNAME --help`

example help statement
`luigi --module recon.targets TargetList --help`

```text
usage: luigi [--local-scheduler] [--module CORE_MODULE] [--help] [--help-all]
             [--TargetList-target-file TARGETLIST_TARGET_FILE]
             [--target-file TARGET_FILE]
             [Required root task]

positional arguments:
  Required root task    Task family to run. Is not optional.

optional arguments:
  --local-scheduler     Use an in-memory central scheduler. Useful for
                        testing.
  --module CORE_MODULE  Used for dynamic loading of modules
  --help                Show most common flags and all task-specific flags
  --help-all            Show all command line flags
  --TargetList-target-file TARGETLIST_TARGET_FILE
  --target-file TARGET_FILE
```

An example scope file command, where `www.example.com` is the domain to be queried. 

`PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.shodan ShodanQuery --target-file www.example.com`

### Additional information

#### PYTHONPATH
To run the pipelines, you need to set your `PYTHONPATH` environment variable to the path of this project on disk.  This can be accomplished in a few ways; two solutions are offered.  

1. Prepend `PYTHONPATH=/path/to/recon-pipeline` to any luigi pipeline command being run.
2. Add `export PYTHONPATH=/path/to/recon-pipeline` to your `.bashrc`   

#### Scheduler

Either add `--local-scheduler` to your `luigi` command on the command line or run `systemctl start luigid` before attempting to run any `luigi` commands.

##### Systemd service file for luigid
``` 
cat >> /lib/systemd/system/luigid.service << EOF 
[Unit]
Description=Spotify Luigi server
Documentation=https://luigi.readthedocs.io/en/stable/
Requires=network.target remote-fs.target
After=network.target remote-fs.target
[Service]
Type=simple
ExecStart=/usr/local/bin/luigid --background --pidfile /var/run/luigid.pid --logdir /var/log/luigi
[Install]
WantedBy=multi-user.target
EOF
```
