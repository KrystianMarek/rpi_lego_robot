#!/usr/bin/env python

import curses

from system_temperature import SystemTemperature
from BrickPi import BrickPiUpdateValues, BrickPiSetup, BrickPi, PORT_A, PORT_B, BrickPiSetupSensors


def update_window(window, power, key, temp):
    window.refresh()
    window.clear()
    window.addstr(1, 1, "a,z - power, arrows - steering, q|esc - exit")
    window.addstr(3, 1, "current power: " + str(power))
    window.addstr(4, 1, "system temp: " + str(temp) + "c")


def increase_power(power, power_step):
    power = power + power_step
    if power > 250:
        power = 250

    return power


def decrease_power(power, power_step):
    power = power - power_step
    if power < 0:
        power = 0

    return power


def run_motors(brick, power_left, power_right):
    brick.MotorSpeed[PORT_A] = power_left
    brick.MotorSpeed[PORT_B] = power_right
    BrickPiUpdateValues()


def go_right(power, brick):
    run_motors(brick, power, power)


def go_left(power, brick):
    run_motors(brick, -power, -power)


def go_backward(power, brick):
    run_motors(brick, -power, power)


def go_forward(power, brick):
    run_motors(brick, power, -power)


def main(window, brick):
    run = True
    power = 0
    power_step = 50
    key = 0

    st = SystemTemperature()

    while run:
        temp = st.get_temp()
        update_window(window, power, key, temp)
        key = window.getch()

        if key == 113 or key == 27:
            run = False

        if key == 97:
            power = increase_power(power, power_step)

        if key == 122:
            power = decrease_power(power, power_step)

        if key == 259:
            go_forward(power, brick)

        if key == 258:
            go_backward(power, brick)

        if key == 260:
            go_left(power, brick)

        if key == 261:
            go_right(power, brick)


if __name__ == '__main__':
    window = curses.initscr()
    curses.noecho()
    curses.cbreak()
    window.keypad(1)
    window.border(1)

    BrickPiSetup()
    BrickPi.MotorEnable[PORT_A] = 1
    BrickPi.MotorEnable[PORT_B] = 1
    BrickPiSetupSensors()

    try:
        main(window, BrickPi)
    except Exception:
        raise
    finally:
        curses.endwin()

#esc 279
#q  113
#a 970
#z 122
# up 259
# left 260
#right 261
#down 258
