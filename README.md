# Istos-Capstone
Code that I used for my capstone project at the University of Nevada, Reno

The team that worked on this consisted of myself, Joel Kaderka, Mitchell Lane, Benjamin Streeter, and Bruno Reyes.

The design intent for this was that the data acquisition device (DAQ) would send data to a server written in Python3 hosted on a spare machine we had on hand.
This server would then be queried by our client which ran on yet another device. 
This was to show that the TCP connection between the DAQ, server, and client were all possible.

The included JavaScript file was supposed to take the place of istos-client.py, but due to the limiations of JavaScript running as a client on a webpage, the webpage actually scrubbed out the TCP connection. The Python client was the solution and an XServer was used to render graphics straight from matplotlib.

<img src="https://i.imgur.com/0qO4a4Q.gif" height="200" width="200" align="middle">
