Filter Tab
==========

What can I filter?
------------------
Let's suppose you want to find (a) specific packet(s) that get
generated when you (for example) press a button, accelerate or lock
the cars doors. The captured CAN traffic contains so much data that
you can't seem to find the packets easily. Let's use the filter tab:

 - You can collect background noise containing CAN packets that
   are sent on the bus without any user interaction
 - After that, a variable amount of samples get captured. You have to
   perform the desired action **in every sample** - e.g. lock the
   doors in every sample.
 - As soon as all data has been captured, the filter tab begins to
   analyze it. It filters background noise out of each sample and tries
   to find packets that occur in every sample. These are most likely
   the packets your are looking for.

How can I try this without a car or CAN device?
-----------------------------------------------
Use ICSim!
