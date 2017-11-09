import functools
from threading import Lock, RLock, Thread
import time
import random


def synchronized(wrapped):
    """ Synchronization decorator. """

    meta_lock = Lock()

    @functools.wraps(wrapped)
    def _wrapper(self, *args, **kwargs):
        with meta_lock:
            lock = vars(self).get("__lock_"+wrapped.__name__, None)
            if lock is None:
                lock = vars(self).setdefault("__lock_"+wrapped.__name__, RLock())
                lock.id = random.randint(1, 100)

        print self.id, lock.id, wrapped

        with lock:
            return wrapped(self, *args, **kwargs)

    return _wrapper


class Foo:
    @synchronized
    def sleep(self, x, text):
        time.sleep(x)
        print self.id, "Slept %d" % x, text

    @synchronized
    def wait(self, x, text):
        time.sleep(x)
        print self.id, "Waited %d" % x, text

    def passed(self, x, text):
        time.sleep(x)
        print text
        print vars(self).get('__lock_wait')

    def __init__(self, id):
        self.id = id

foo = Foo('foo')
bar = Foo('bar')


def t(i, m, s, c):
    foo_t = Thread(target=getattr(i, m), args=[s, c])
    foo_t.daemon = True
    foo_t.start()

t(foo, "sleep", 1, "A")
t(foo, "wait", 1, "A")
t(bar, "sleep", 1, "A")
t(bar, "wait", 1, "A")

t(foo, "sleep", 1, "B")
t(foo, "wait", 1, "B")
t(bar, "sleep", 1, "B")
t(bar, "wait", 1, "B")

t(foo, "passed", 1.5, "Four A events should have run, But B events should have not.")

time.sleep(3)

print "Four B events should have run"
