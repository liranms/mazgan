# mazgan
IR blaster decoder and website for air conditioner tadiran wind 50

mazgan.py includes decoding mode2 output and reverse engineering of the coding created by the original remote
it also includes a class that allows generating valid IR codes for any state (at least for the options I was able to reverse)
running the file will generate all possible states into a lirc file

app.py is a simple flask web interface that calls ir_send with the valid selected option
