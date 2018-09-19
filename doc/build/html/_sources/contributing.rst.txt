Contributing
============

Here's some useful info if you want to contribute.

Guidelines
----------

- Each tab has its own Class. If possible, inherit from :class:`~src.AbstractTab.AbstractTab`.

 - To provide comatibility:

  - The displayed data should also be in a raw data list called ``rawData`` which is *always* up to date
  - ``prepareUI`` initializes all GUI elements
  - ``active`` manages the status of a tab
  - Tab specific CANData instances are called ``CANData``
   
- Please log useful information using an own logger instance
- Use existing Toolbox methods if possible
- Use batch database operations using raw lists (not objects) for better performance
- Use docstrings
- Keep the ``.ui`` files clean: Always name new GUI elements properly according to existing ones
- Put new strings in the Strings file and reference it

I want to add a new tab, what do I have to do?
----------------------------------------------
- Create a new tab on the GUI and stick to the already existing naming conventions
- Add a QTableView to display your data and other GUI elements
- Update `mainWindow.py` using `pyside-uic mainWindow.ui > mainWindow.py`.
- Add a new File and a new class which inherits from :class:`~src.AbstractTab.AbstractTab`
- Call the parents constructor in your ``__init__``
- Add the GUI elements from the ``.ui`` file to your code. You can refer to the other tabs
  to see how it's done. Also, add the click handlers here.
- Call ``prepareUI`` as last action in ``__init___``
- If your tab needs an interface or displays interface values: Add your tab
  class or instance to :func:`~src.Toolbox.Toolbox.updateInterfaceLabels` and/or :func:`~src.Toolbox.Toolbox.updateCANDataInstances`.
- If your tab uses an instance: Add an instance to `Globals.py` and create one at startup (see `CANalyzat0r.py`).
- If your tab uses a static class: Call `prepareUI` at startup (see `CANalyzat0r.py`).
