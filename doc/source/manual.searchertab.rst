Searcher Tab
============

What can I search for?
----------------------
Using this tab you can perform a binary packet search for a
specific packet or a whole packet set that cause an effect.
Let's suppose you've fuzzed and got a large packet dump that, when
replayed, causes an effect on your CAN device / car. You now want to
extract the relevant packet(s) out of that dump. Searcher tab to the
rescue -- Load the whole packet dump and let the analyzer routine
guide you.
Note: This first tries to search for **1** packet that causes an action.
It this fails, the searcher tries to continously minimize the packet set.

It doesn't work!!1!
-------------------
Don't give up too fast, try the following things:
- Set the packet gap to a lower value, you can even try 0
- Just try again and hope for better shuffling
- Use another dump/fuzz again, ...
- Wait a few seconds after each chunk

It still doesn't work :(
------------------------
CAN devices can be extremely tricky, for example spedometers. Depending
on your dump, you may have to try it multiple times with the same dump
because of packet timings and/or bad luck. If you replay your whole
dump and see the desired action, you will be able to find it using
the searchter tab.


I want to do it manually, how can this tool help me?
----------------------------------------------------
Create a new sender, add the dump to it and send them in a loop.
Minimize the packet set from the bottom using your "CTRL+C" and "DEL" and try
again. If it didn't perform the desired action, paste the packets again
and delete other packets.
