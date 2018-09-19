Sniffer Tab
===========

How to sniff?
-------------
It's simple. For every discoverd interface you can find a sniffer tab
here. If no tab for your desired interface is displayed, please
re-check all available interfaces using the button on the main tab.
Once you find your desired interface, just click on start.

Ignoring packets
----------------
You can add tab specific packets to the ignore list.
Hint: Use a blank data field if you want to exclude whole IDs.

Another Hint: You can use the fitering buttons to remove background noise. It's great.

I get errors/no data when I try to sniff!!1!
--------------------------------------------
 - Maybe your SocketCAN interface disappeared?
 - Maybe you have selected a wrong bitrate?
 - Have you tried turning it off and on again?

The sniffer tab doesn't list the packets I'm sending
-----------------------------------------------------
Thats normal. You will only see packets that you are receiving on a
specific interface. This prevents the packets that you generate via
fuzzing from being in your sniffed dump. If you really need all
packets in one dump, you can use ``candump``.
