import json
import sys


def average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)


def greet(name: str) -> int:
    return "Hello " + name


def broken():
    return undefined_var