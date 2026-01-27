# spatialdata-data-converter

**This repo has been migrated from an old private one and the migration is not complete yet**. I.e. things will not work as they are now.

Automated pipeline for the end-to-end testing of the SpatialData framework, the conversion of sample datasets and the upload of the converted datasets to S3.

## How to use this repository
This repository contains a series of scripts that can be ran manually (either sequentially, either with parallelization) or in a Airflow pipeline. We need all these approaches, since they cover different use cases.

- Airflow. A machine connected to the internet to which the team can have secure access will run
 Airflow 24/7 and will provide a continuously up-to-date status on the health of the SpatialData framework. The Airflow pipeline could be configured to use a parallel executor, but we will keep it simple and run the jobs sequentially. This is fine because the machine is more of a "run and forget" type, so it doesn't really matter if the jobs take a bit longer to run.

The Airflow pipeline has some disadvantages:
- It's not straightforward to debug/rerun failing jobs.

The machine is not powerful. A laptop is more powerful, and the local workstations we have in the lab are much more powerful. This is why we have these two approaches:
- Manual execution, sequentially. We run jobs in a series of bash script. Simple to understand, to run, to debug and fast.
- Manual execution, parallelized. We run jobs in parallel using a simple bash function to spin multiple processes. Simple and very fast. More fragile than a sequential run, and not as stable or powerful than Airflow or other executors like Nextflow etc, but much simpler than those.

Probably there are better techs, like Flyte or Prefect, which combine easy local execution with a pipeline system. But they are expensive. Airflow is powerful but not good for local execution, bash is simple and good for local execution but not a good way to build pipelines. That's why we use both.
 

## Installation on local/private machines (to run the scripts manually)
The installation instructions are not heavily tested so be ready to adjust them to your environment (and please contribute back your changes), or consider opening a GitHub issue.

1. Clone the repository, including the submodules:
    ```bash
    git clone --recurse-submodules https://github.com/scverse/spatialdata-integration-testing.git 
    ```

2. Go to the cloned directory:
    ```bash
    cd spatialdata-data-converter
    ```
3. Install the `pixi` environment
   You need to have `pixi` available in your system.
   ```bash
   pixi install
   pixi update
   ```
4. Copy `template_envvars.sh` into `envvars.sh` and edit the 2 paths according to your system.
5. Run `workflow_first_run.sh` with
    ```bash
    bash src/spatialdata_data_converter/workflow_first_run.sh
    ````
   This will run a small set of commands sequentially.
6. If your script fails (it shoult not, but there is some chance it will):
    - Comment out what worked to avoid re-running everything.
    - Fix what didn't work.
    - Run the script again from where it failed.
    - Continue like this until the script finishes successfully.
    - Please commit and push the fixes, or at minimum report them.
7. Now there is a good chance that things work, you are ready to run the real thing!
   This is the script that you should run before making a release. The jobs will be run in parallel. On a multi-core ubuntu machine the parallel version takes 15 mins, the non parallel would take (I think) more than 1 hour.
    ```bash
   bash src/spatialdata_data_converter/workflow_before_release.sh
   ```
   If it passes, you are ready to make a release! If it doesn't pass, debug things like before. 
   You can either comment out lines from the script above, or if you want to run things sequentially you can 
   manually comment/uncomment out lines in the script `invoke_cli.sh` (which contains all the commands, even the one you don't need) and run it with:
    ```bash
    bash src/spatialdata_data_converter/invoke_cli.sh
    ```
8. After making a release, please upload the new datasets to S3 by running:
    ```bash
    bash src/spatialdata_data_converter/workflow_upload_data_for_release.sh
    ```

## Installation on the Airflow machine
1. Configure the Airflow home directory.
In your `~/.zshrc` file (or depending on your system `~/.bashrc`, `~/.bash_profile`, ...), add the following lines (remember to change the path):
```bash
export AIRFLOW_HOME=/absolute/path/to/spatialdata-integration-testing/airflow
```
2. Run Airflow
```bash
pixi run airflow standalone
```
When running the command above for the first time, it creates a configuration file in `$AIRFLOW_HOME/airflow.cfg`. After creating the configuration, the command starts the webserver and the scheduler.

3. Manually change the configuration
Set
```python
load_examples = False 
page_size = 100
```

3. Open the dashboard.

   In your browser and go to `http://localhost:8080` to access the Airflow webserver.
   If it doesn't work, check the terminal output for the correct port.
4. Login.
    
    For username and password follow the instructions printed in the terminal: search for "standalone | Password for the admin user has been previously generated in".

# Known issues
- The previous version of the repo used a serial executor for Airflow (i.e. no two tasks could be run in parallel). The current default configuration allows parallel execution. I may have spotted some problems during IO operations due to this but I am still investigating. Worst case we can sacrifice some performance and go back to serial execution.
