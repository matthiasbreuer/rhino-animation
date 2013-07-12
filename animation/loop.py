import time

import rhinoscript as rs
import scriptcontext as sc

import Rhino as r


class Loop(object):
    def __init__(self, fps=25):
        self.callbacks = []
        self.delta = 1.0 / fps
        self.running = False

    def update(self):
        td = time.time() - self.time
        if td > self.delta:
            self.time = time.time()
            [callback(td) for callback in self.callbacks]
            self.redraw()

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        try:
            self.callbacks.remove(callback)
        except ValueError:
            return False

        return True

    def start(self):
        self.running = True
        self.time = time.time()
        while True:
            if not self.running:
                return

            self.update()

    def stop(self):
        self.running = False
        self.redraw()

    def redraw(self):
        rs.document.EnableRedraw()
        sc.doc.Views.Redraw()
        r.RhinoApp.Wait()
        rs.document.EnableRedraw(False)