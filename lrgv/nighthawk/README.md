This directory contains the script `run_nighthawk.py` for running the
Nighthawk detector on LRGV recordings. To use this script on an LRGV
station laptop:

1. Install Miniconda on the laptop.

2. Copy the entire `lrgv-2024` directory, including the
   `run_nighthawk.py` script and this file, into the
   `C:\Temp\calls\Apps\Code` directory of the laptop.

3. Create a Conda environment called `lrgv` by issuing the following
   commands at an Anaconda Prompt:

       conda create -n lrgv python=3.11
       conda activate lrgv
       cd C:\Temp\calls\Apps\Code\lrgv-2024
       pip install -e .

   Note that the last command includes a "." at the end, separated
   from the "-e" that precedes it by a space. You can cut and paste
   the above command to help be sure to get it right.

4. Create a Conda environment called `nighthawk-0.3.0` by issuing the
   following commands at an Anaconda Prompt:

       conda create -n nighthawk-0.3.0 python=3.10
       conda activate nighthawk-0.3.0
       pip install nighthawk==0.3.0

5. Use the Windows Task Scheduler to create a daily task that runs
   the `run_nighthawk.py` script in the `lrgv` Conda environment
   every morning to run Nighthawk on the previous night's recording.
   When configuring the task in the Task Scheduler, use the
   "Start a program" action with the "program/script" configuration
   item set to:

       C:\Users\wreva\miniconda3\envs\lrgv\python.exe

   i.e. the path of the Python interpreter of the `lrgv` Conda
   environment.
   
   Set the "Add arguments (optional)" configuration item to a string
   of the form:

       <script path> <recording directory path> <clip directory path>

   for example:

       "C:\Temp\calls\Apps\Code\lrgv-2024\lrgv\nighthawk\run_nighthawk.py" "C:\Users\wreva\Desktop\Vesper Recorder Audio" "C:\Temp\calls\Clips\Nighthawk\Incoming"

   Be sure to double-quote the paths you specify.

   Leave the "Start in (optional)" configuration item empty.
