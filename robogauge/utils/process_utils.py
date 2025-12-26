# -*- coding: utf-8 -*-
'''
@File    : process_utils.py
@Time    : 2025/12/26 21:59:53
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : No Daemon Pool for Multiprocessing
'''
import multiprocessing
import multiprocessing.pool

class NoDaemonProcess(multiprocessing.Process):
    @property
    def daemon(self):
        return False
    @daemon.setter
    def daemon(self, value):
        pass

class NoDaemonPool(multiprocessing.pool.Pool):
    def __init__(self, *args, **kwargs):
        """ context=ctx in kwargs is required """
        super(NoDaemonPool, self).__init__(*args, **kwargs)

    def Process(self, *args, **kwds):
        proc = super(NoDaemonPool, self).Process(*args, **kwds)
        proc.__class__ = NoDaemonProcess
        return proc
