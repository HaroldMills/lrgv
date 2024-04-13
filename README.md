Note that in the following the term *user directory* refers to the
home directory of the user thaat runs the LRGV software, e.g.
`C:\Users\wreva`.

The `lrgv` Python package is software for the Old Bird Lower Rio Grande
Valley (LRGV) acoustic monitoring project. The software includes a
program called `run_nighthawk` that runs the Nighthawk nocturnal flight
call detector on audio recordings and a program called `archive_clips`
that adds detected clips to a Vesper archive. `run_nighthawk` is
also known as the *Nighthawk runner* and `archive_clips` is also known
as the *archiver*. As of this writing, the Nighthawk runner runs on
monitoring station laptops, while the archiver runs on a separate
computer in Lansing, NY dedicated to maintaining the station laptops
(to the extent possible via the SugarSync file synchronization utility)
and archiving their detections. In the future, the archiver may run
on the station laptops instead.

To install the `lrgv` package and related software onto a station laptop:

0. Make sure that the i-Sound Recorder is configured to record into the
   `Desktop\i-Sound Audio` subdirectory of the user directory. The `lrgv`
   package software assumes that the files will appear there.

1. Copy the contents of the SugarSync
   `My Sugarsync\LRGV Station Laptop Software\To Copy` directory (i.e.
   its `Apps` and `Clips` subdirectories) into `C:\Temp\calls`.

2. Install Miniconda into the `miniconda3` subdirectory of the user
   directory (e.g. `C:\Users\wreva`).

3. Create a Conda environment called `lrgv` by issuing the following
   commands at an Anaconda Prompt:

       conda create -n lrgv python=3.11
       conda activate lrgv
       cd C:\Documents\My SugarSync\LRGV Station Software\To Share\Python\lrgv-2024
       pip install -e .

   Note that the last command includes a "." at the end, separated
   from the "-e" that precedes it by a space. You can cut and paste
   the above command to help be sure to get it right.

4. Create a Conda environment called `nighthawk-0.3.0` by issuing the
   following commands at an Anaconda Prompt:

       conda create -n nighthawk-0.3.0 python=3.10
       conda activate nighthawk-0.3.0
       pip install nighthawk==0.3.0

5. Use the Windows Task Scheduler to create a task that runs
   the `C:\Temp\calls\Apps\Nighthawk Runner\Start Nighthawk Runner.bat`
   batch file every morning at 5:10 AM. The batch file runs a Python
   script in the `lrgv` Conda environment that runs Nighthawk on the
   previous night's recording and puts clips for the resulting detections
   in the `C:\Temp\calls\Clips\Nighthawk\Incoming` directory. You can
   use the `Create Basic Task` wizard in the task scheduler to create
   the task, as long as you subsequently perform the edits indicated
   below. When creating the task, you can leave the
   `Add arguments (optional)` and `Start in (optional)` items of the
   `Start a Program` configuration empty. After creating the task,
   edit it and select `Run whether user is logged on or not` and
   `Do not store password` in the `General` tab.

For a station that will also run the Vesper Recorder:

6. Create a `Desktop\Vesper Audio` subdirectory of the user
   directory. The Vesper Recorder will write audio files to
   this directory.

7. Edit the file
   `C:\Temp\calls\Apps\Vesper Recorder\Vesper Recorder Settings.yaml`.
   Change the station name `Ludlow` to the full name of your station
   (e.g. `Port Isabel`) in the two places in the file where it occurs.
   Note that there's no need to quote the station name in the file.

8. Create a Conda environment called `vesper-latest` by issuing the
   following commands at an Anaconda Prompt:

       conda create -n vesper-latest python=3.11
       conda activate vesper-latest
       conda install -c conda-forge python-sounddevice
       cd C:\Documents\My SugarSync\LRGV Station Software\To Share\Python\Vesper
       pip install -e .

   This installation make take several minutes, since the Vesper
   package has many dependencies.

9. Use the Windows Task Scheduler to create a daily task that runs
   the `C:\Temp\calls\Apps\Vesper Recorder\Start Vesper Recorder.bat`
   batch file every day at noon (i.e. 12 PM). The batch file runs
   the Vesper Recorder, configured to record to the
   `Desktop\Vesper Audio` subdirectory of the user directory. You can
   use the `Create Basic Task` wizard in the task scheduler to create
   the task, as long as you subsequently perform the edits indicated
   below. When creating the task, you can leave the
   `Add arguments (optional)` and `Start in (optional)` items of the
   `Start a Program` configuration empty. After creating the task,
   edit it and select `Run whether user is logged on or not` and
   `Do not store password` in the `General` tab.