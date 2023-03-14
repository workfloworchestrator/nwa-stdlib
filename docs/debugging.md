## Debugging in a k8s dev environment

How to attach a debugger to a remote server in Kubernetes/Okteto and debug from your IDE.

Below examples are written for IMS but should apply to any other gitlab project.

### VSCODE

Initial setup:
* Add configuration from `okteto/launch.json` to `.vscode/launch.json` 

Steps to take every time you want to debug:
* In your `.env` set `DEBUG_VSCODE=true`
* Choose how you want to debug:
  * To run IMS in debugging mode: `okteto up`
  * To run unit tests in debugging mode: `okteto up ims --command=pytest  --command="tests/unit_tests" --command="-v"`
  * (note: you cannot debug acceptance tests this way, unless you run them against an IMS instance) 
* Wait until you see this log statement `[info     ] Waiting for debug client to connect`
* In VScode go to `Run & Debug` and run configuration "Attach to IMS okteto"

You should see the log statement `[info     ] Debug client connected` after which you can debug as normal.


### PyCharm

**Option 1: remote interpreter**

Requires PyCharm Professional and `okteto up` should be running.

Initial setup (as of PyCharm 2022.3) from the Settings menu:
* Go to [`Deployment > Options`](https://www.jetbrains.com/help/pycharm/settings-deployment-options.html)
  * To "Exclude items by name" append `;.*cache;*venv*;.code;.vscode` (extend as needed per project; the more you exclude the better)
* Go to [`Tools > SSH Configurations`](https://www.jetbrains.com/help/pycharm/settings-tools-ssh-configurations.html)
  * Click Add
  * Change **Authentication type** to `OpenSSH config and authentication agent`
  * Set **Host** to `ims.okteto`, replace `ims` with the container name from okteto.yaml
    * You should see **Port** fill automatically. If not, something's wrong..
  * Set **Username** to your system user (`whoami` in terminal)
  * Test Connection
* Go to [`Project > Python Interpreter`](https://www.jetbrains.com/help/pycharm/configuring-remote-interpreters-via-ssh.html)
  * Click **Add Interpreter** and select `On SSH`
  * Choose `Existing` connection and select `ims.okteto`
  * Click **Next** until you can select Interpreter, then choose `System interpreter`

Enable the remote interpreter as project default and let PyCharm sync files to the okteto dev container. You may need to restart the IDE once.

**Option 2: pydevd**

Initial setup:
* Add a [`Python Debug Server`](https://www.jetbrains.com/help/pycharm/remote-debugging-with-product.html#create-remote-debug-config)
  * Set `IDE host name` to `localhost`
  * Set `Port` to `12345`
  * Path mapping: map local path `<repository>` to remote path `/usr/src/app`
    * Example: `/Users/mark/dev/surf/gitlab/ims` <-> `/usr/src/app`

Steps to take every time you want to debug:
* In your `.env` set `DEBUG_PYCHARM=true`
* Start the debug server in pycharm; it will say `Waiting for process connection...`
* Choose how you want to debug:
  * To run IMS in debugging mode: `okteto up`
  * To run unit tests in debugging mode: `okteto up ims --command=pytest  --command="tests/unit_tests" --command="-v"`
  * (note: you cannot debug acceptance tests this way, unless you run them against an IMS instance) 
* Wait until you see this log statement `[info     ] Connecting to pydevd server (choose 'Resume Program' in PyCharm)`
* Go back to PyCharm and click `Resume Program` in the Debug window

Now it will halt on breakpoints and you can debug as normal.

Notes:
* We need to use `uvicorn` as `hypercorn` inits the application twice for some reason (breaking the pydevd setup)
* Whenever you make changes to the code and it reloads, you'll need to click `Resume Program` again
