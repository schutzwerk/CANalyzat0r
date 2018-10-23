![Alt text](/.repoResources/mainTab.png?raw=true "CANalyzat0r main tab")

*This software project is a result of a Bachelor's thesis created at [SCHUTZWERK](https://www.schutzwerk.com) in collaboration with [Aalen University](https://www.hs-aalen.de/) by Philipp Schmied.*

*Please refer to the corresponding [blog post](https://www.schutzwerk.com/en/43/posts/canalyzat0r/) for more information.*

# Why another CAN tool?
* Built from scratch with new ideas for analysis mechanisms
* Bundles features of many other tools in one place
* Modular and extensible: Read the docs and implement your own analysis mechanisms
* Comfortable analysis using a GUI
* Manage work in separate projects using a database
* Documentation: Read the docs if you need a manual or technical info.

# Installing and running:
* Run `sudo ./install_requirements.sh` along with `sudo -E ./CANalyzat0r.sh`. This will create a folder called `pipenv` with a `pipenv` environment in it.
* Or just use the docker version which is recommended at this time (Check the `README.md` file in the subdirectory)

For more information, read the HTML or PDF version of the documentation in the `./doc/build` folder.

# Features
* Manage interface configuration (automatic loading of kernel modules, manage physical and virtual SocketCAN devices)
* Multi interface support
* Manage your work in projects. You can also import and export them in the human readable/editable JSON format
* Logging of all actions
* Graphical sniffing
* Manage findings, dumps and known packets per project
![Alt text](/.repoResources/demo/knownPackets.gif?raw=true "Recognizing known packets")
* Easy copy and paste between tabs. Also, you can just paste your SocketCAN files into a table that allows pasting
![Alt text](/.repoResources/demo/import.gif?raw=true "Import SocketCAN files")
* Threaded Sending, Fuzzing and Sniffing
![Alt text](/.repoResources/demo/fuzzer-sniffer.gif?raw=true "Fuzzing and Sniffing at the same time")
* Add multiple analyzing threads on the GUI
* Ignore packets when sniffing - Automatically filter unique packets by ID or data and ID
* Compare dumps
* Allows setting up complex setups using only one window
* Clean organization in tabs for each analysis task
* Binary packet filtering with randomization
* Search for action specific packets using background noise filtering
![Alt text](/.repoResources/demo/filter.gif?raw=true "Filter Tab")
* SQLite support
* Fuzz and change the values on the fly

# Testing It

You can use the [Instrument Cluster Simulator](https://github.com/zombieCraig/ICSim) in order to tinker with a virtual CAN bus without having to attach real CAN devices to your machine.

# Fixing the GUI style

This application has to be run as superuser. Because of a missing configuration, the displayed style
can be set to an unwanted value when the effective UID is 0. To fix this behaviour, follow these steps:

* Quick way: Execute `echo "[QT]\nstyle=CleanLooks" >> ~/.config/Trolltech.conf`

* Alternative way:
  * Install qt4-qtconfig: `sudo apt-get install qt4-qtconfig`
  * Run qtconfig-qt4 as superuser and change the GUI style to CleanLooks or GTK+

* Or use the docker container

# License

This project is licensed under the [GPLv3](https://www.gnu.org/licenses/gpl.txt).
