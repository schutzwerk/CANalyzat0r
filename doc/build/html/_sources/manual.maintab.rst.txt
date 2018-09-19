Main Tab
==========

Welcome to CANalyzat0rs main tab!
Here you can change interface settings and creat/remove virtual CAN
interfaces. Don't worry, the kernel modules should aready be loaded for you.

Where's my interface?!?!1!
--------------------------
If you can't find your attached CAN interface in the ComboBox, please
check the output of ``ifconfig -a``. In order to use your interface
with CANAlyzat0r, a SocketCAN device must be present. Maybe you have to
load another kernel module/driver?

Creating and selecting projects
-------------------------------

On a fresh startup, you should encounter a message saying that a new
project should be created. You can still use this application without a
selected project. However, one can't save dumps or known packets.
To create a project, please refer to the manager tab. After you
have created a project there, you can set it as active project in the
main tab.

Log levels
----------
You can set the minimum log level for which messages will be printed
to the log box in this tab.

Where's my data being saved to?!!?
----------------------------------
By default, CANalyzat0r creates a SQLite database called "database.db"
in the data folder. Please take care of this file as everything you
discover is saved here.

But what if i want to export my data?
-------------------------------------
Please check the manager tab and learn on how to export projects and
dumps.
