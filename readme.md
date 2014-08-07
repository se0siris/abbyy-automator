# Abbyy Automator #

### About ###
This application will control Abbyy Finereader (currently only 10 due to dropped features in later versions) and allow a folder of input files to be processed to an output folder while retaining the directory structure.

### Why? ###
Abbyy doesn't provide a feature like this inside the main application. Well, it has the "Hot Folder" feature, but with a large volume of files this seems to cause a few problems.

### How? ###
Abbyy does not provide an API or command line tools to use its Finereader application. It does allow sending a processed file to Acrobat though after being started with the commandline with its `/send Acrobat` parameter.

This application will backup the main Acrobat.exe file and install its own proxy application. If the proxy application is asked to open a PDF file from outside of the Finereader temp folder it will pass the action to the original Acrobat.exe, otherwise it will send the path to a running instance of the Abbyy Automator application to be moved into the correct output folder.

The main Acrobat.exe file is restored on application exit. Yes, this is an extremely hacky way of doing things but it works and is better than older methods that we used.

### Features ###
  - **Folder monitoring**
    The application will build an initial queue once the process is started. It will then keep monitoring the input folder and add new files to the queue.
  - **Profiles**
    Profiles can be saved from Abbyy into the "Profiles" subfolder of the application and chosen from a dropdown list in the Abbyy Automator application.

### Changelog ###

##### 1.0 #####
  - First release