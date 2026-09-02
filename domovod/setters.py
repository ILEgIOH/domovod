"""Фабрика простых сеттеров для полей состояния (автосеттеры в Reflex отключены)."""

import reflex as rx


def make_setter(attr: str):
    def _setter(self, value):
        setattr(self, attr, value)

    # Reflex derives the wire event name from the last segment of
    # __qualname__. Without a unique qualname, every dynamically created
    # setter collides on "make_setter.<locals>._setter", so only the last
    # one defined in a class actually gets called no matter which button
    # triggers it. Give each setter its own name AND qualname.
    _setter.__name__ = f"set_{attr}"
    _setter.__qualname__ = f"set_{attr}"
    return rx.event(_setter)
