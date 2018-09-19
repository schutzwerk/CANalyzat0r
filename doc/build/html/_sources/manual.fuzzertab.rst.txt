Fuzzer Tab
==========

What does this thing to?
------------------------
Using this tab you can send random packets into the CAN bus to discover
things. You can tune settings that control random packet generation
using the GUI elements.

What are masks?
---------------
You can write static values into the masks or put an X if that character
should be randomized. Using this, you can freely control the payload
of generated packets.
Hint: You can change masks and lengths **while fuzzing**.

Other fuzzers are much faster!!1!
---------------------------------
This is a python based fuzzer which also displays the packets on the GUI.
This convenience costs performance. If you want the best performance
you can use ``cangen`` of the ``can-utils`` package and import the
created packets later.

What are the modes?
-------------------
 - User specified: You can freely specify ID and data masks
 - 11 bit IDs / 29 bit IDs: Only short/extended IDs will be used
