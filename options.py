from enum import Enum

REMOTE_NAME = "wind50_auto"
STATE_FILENAME = "/var/www/mazgan.state"

class Mode(Enum):
    cool = 1
    heat = 2
    fan = 3    
    defrost = 4
    auto = 5


class Fan(Enum):
    low = 1
    med = 2
    high = 3
    auto = 4


class Energy(Enum):
    auto = 0
    night = 1
    none = 2


class State(Enum):
    on = 0b0011
    off = 0b1100

class Temperature(Enum):
    minimal = 16
    maximal = 30


def make_name(state, temp, fan, energy, mode):
    assert isinstance(state, State)
    assert isinstance(temp, int)
    assert isinstance(fan, Fan)
    assert isinstance(energy, Energy)
    assert isinstance(mode, Mode)
    if state == State.off:
        return "off"
    name = [str(temp),
            str(fan),
            str(energy),
            str(mode)]
    return "_".join(name)