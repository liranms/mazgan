import json
import traceback
import subprocess
from flask import Flask, render_template, request, Response, jsonify
from functools import wraps
from options import *
from mazgan_secrets import *

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# From http://flask.pocoo.org/snippets/8/
def check_auth(username, password):
    if not username or not password:
        return False
    return username in VALID_AUTH and VALID_AUTH[username] == password

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def ir_send(button):
    try:
        # return button
        return subprocess.check_output(
            #  "-d" "/var/run/lirc/lircd-lirc0"
            ["/usr/bin/irsend", "--count=2", "send_once", REMOTE_NAME, button])
    except Exception as e:
        traceback.print_exc()
        return "Failure: %s" % (e,)


def make_state(temp=24, fan=Fan.auto, energy=Energy.auto, mode=Mode.cool, state=State.on):
    return {"temp": temp,
            Fan.__name__: str(fan.name),
            Energy.__name__: str(energy.name),
            Mode.__name__: str(mode.name),
            "state": str(state.name),
            }


def save_state(s):
    with open(STATE_FILENAME, "wt") as f:
        json.dump(s, f)


def load_state():
    try:
        with open(STATE_FILENAME, "rt") as f:
            return json.load(f)
    except:
        traceback.print_exc()
        return make_state()


@app.route('/')
@requires_auth
def home():
    opt = {Fan.__name__: [i.name for i in Fan],
           # Energy.__name__: [i.name for i in Energy],
           Mode.__name__: [i.name for i in Mode]
           }
    state = load_state()
    return render_template('main.html', opt=opt, state=state)


@app.route('/on', methods=['POST'])
@requires_auth
def set():
    temp = int(request.form.get('temperature', 25))
    fan = Fan[request.form.get(Fan.__name__, Fan.auto.name)]
    # energy = Energy[request.form.get(Energy.__name__, Energy.auto.name)]
    energy = Energy.auto
    mode = Mode[request.form.get(Mode.__name__, Mode.cool.name)]
    btn = make_name(State.on, temp, fan, energy, mode)
    state = make_state(temp, fan, energy, mode, State.on)
    output = ir_send(btn)
    save_state(state)
    return jsonify({"result": "turnned on (%s %sC@%s). %s" % (mode.name, temp, fan.name, str(output, "utf-8"),),
                    "button": btn})


@app.route('/off', methods=['POST', 'GET'])
@requires_auth
def turn_off():
    output = ir_send("OFF")
    state = make_state(state=State.off)
    save_state(state)
    return jsonify({"result": "turnned off. %s" % (str(output, "utf-8"),)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
