"""The sketch environment of the workspace (ADR 0005, addendum 2026-11-02): create a sketch on a plane or
face (or open one again), draw in it with SolidCraft's sketch commands one request at a time, and finish
or cancel. The whole session is one hand step in the shared undo list; the agent is locked out meanwhile.
Inside the sketch, undo goes back one command (a checkpoint per command)."""

# Commands the sketcher may send while a sketch is open. Opening, closing and leaving go through
# begin/finish/cancel, so they are not allowed here.
NOT_IN_SESSION = {"sketch.create", "sketch.edit", "sketch.finish", "sketch.finish_auto_constrain"}
# Besides sketch.*: changing a dimension's value (its parameter), as double-clicking a dimension does
ALSO_IN_SESSION = {"parameters.change"}


class SketchError(Exception):
    """A request that does not fit the state of the sketch environment (HTTP 409)."""


def _inspect(doc) -> dict:
    """What the sketcher draws: points, curves, dimensions, constraints, degrees of freedom, profiles, plane."""
    return doc.session.cmd("sketch.inspect", {})


def _restore(doc, cp):
    """Back to the checkpoint, then drop it (forget alone drops it without going back)."""
    doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp})
    _forget(doc, cp)


def _forget(doc, cp):
    try:
        doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": True})
    except Exception:
        pass


class SketchSession:
    def __init__(self, doc, agent, snap, start_cp, name: str, editing: bool):
        self.doc, self.agent, self.snap = doc, agent, snap
        self.start_cp = start_cp      # the part before the session: cancel goes back here
        self.name, self.editing = name, editing
        self.undo: list = []          # one checkpoint per command, newest last

    @classmethod
    def begin(cls, doc, agent, plane=None, edit: str | None = None) -> "SketchSession":
        """Open the environment: a new sketch on plane (XY, XZ, YZ or {face: [x, y, z]}), or the sketch
        named edit. Raises if the agent works (Busy) or SolidCraft refuses the plane."""
        if (plane is None) == (edit is None):
            raise ValueError("give either plane or edit")
        if plane is not None:
            plane = {"face": plane["face"]} if isinstance(plane, dict) and "face" in plane else plane
            if plane not in ("XY", "XZ", "YZ") and not isinstance(plane, dict):
                raise ValueError("plane: XY, XZ, YZ or {face: [x, y, z]}")
        snap = agent.begin_hand()
        s = doc.session
        try:
            cp = s.cmd("edit.checkpoint").get("checkpoint")
            try:
                if edit is not None:
                    s.cmd("sketch.edit", {"sketch": edit})
                    name = edit
                else:
                    made = s.cmd("sketch.create", {"plane": plane})
                    name = made.get("name") or _inspect(doc).get("name")
            except BaseException:
                _restore(doc, cp)
                raise
        except BaseException:
            agent.end_hand(snap, None)
            raise
        return cls(doc, agent, snap, cp, name, edit is not None)

    def state(self) -> dict:
        st = _inspect(self.doc)
        return {"sketch": self.name, "editing": self.editing, "can_undo": bool(self.undo), "state": st}

    def command(self, command: str, params: dict) -> dict:
        """One sketch command (sketch.line, sketch.circle.center, sketch.dimension, sketch.constraint.*, ...).
        A refused command leaves the sketch as it was."""
        if not isinstance(command, str) or command in NOT_IN_SESSION or not (
                command.startswith("sketch.") or command in ALSO_IN_SESSION):
            raise PermissionError(f"not a drawing command in the sketch environment: {command}")
        s = self.doc.session
        cp = s.cmd("edit.checkpoint").get("checkpoint")
        try:
            result = s.cmd(command, params or {})
        except BaseException:
            _restore(self.doc, cp)
            raise
        self.undo.append(cp)
        return {"result": result, **self.state()}

    def undo_last(self) -> dict:
        if not self.undo:
            raise SketchError("nothing to undo in this sketch")
        _restore(self.doc, self.undo.pop())
        return self.state()

    def finish(self) -> dict:
        """Close the sketch, save the part, record the session as one undo step."""
        s = self.doc.session
        try:
            s.cmd("sketch.finish", {})
            self.doc.save()
        except BaseException:
            self.cancel()
            raise
        for cp in self.undo + [self.start_cp]:
            _forget(self.doc, cp)
        label = f"{'Edit sketch' if self.editing else 'Sketch'} {self.name} in {self.doc.name}"
        self.agent.end_hand(self.snap, label)
        return {"done": label, "sketch": self.name}

    def cancel(self) -> dict:
        """Leave without keeping anything: the part goes back to how it was before begin."""
        _restore(self.doc, self.start_cp)
        self.agent.end_hand(self.snap, None)
        return {"cancelled": self.name}
