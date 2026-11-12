import os
import subprocess


def ping_host(host):
    os.system("ping -c 1 " + host)


def run_cmd(cmd):
    return subprocess.run(cmd, shell=True)


def calculate(expr):
    return eval(expr)