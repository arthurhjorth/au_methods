# au_methods

This code is released under CC Attribution-NonCommercial-ShareAlike 4.0 International.

If you use it in your own teaching, I would love to know about it. So please write me at arthur@mgmt.au.dk.

If you are interested in using it in your own teaching, but you have questions, please feel free to get in touch, arthur@mgmt.au.dk.

# Installation:

Install a virtual environment, and use pip to install requirements.txt. 

The virtual environment inludes gunicorn, and if you want to run it in the background I recommend using Supervisord to spawn daemons with an appropriate number of workers (2-4ish), and with a port that you have permission to open on the firewall.

If you want to just run a local server, either set up a $FLASK_APP environment variable and run flask run, configure through wsgi, or use python to run the app.py file.
