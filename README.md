# Istos-Capstone
Code that I used for my capstone project at the University of Nevada, Reno

The team that worked on this consisted of myself, Joel Kaderka, Mitchell Lane, Benjamin Streeter, and Bruno Reyes.

The design intent for this was that the data acquisition device (DAQ) would send data to a server written in Python3 hosted on a spare machine we had on hand.
This server would then be queried by our client which ran on yet another device. 
This was to show that the TCP connection between the DAQ, server, and client were all possible.

The included JavaScript file was supposed to take the place of istos-client, but due to the limiations of JavaScript injected into a webpage, the TCP connection was not allowed this way.
