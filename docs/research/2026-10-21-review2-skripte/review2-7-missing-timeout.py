#!/usr/bin/env python3
"""Reproduction for Finding 7: Session._rpc has no timeout and hangs indefinitely."""
import inspect
from mechvane.solidcraft import Session

s = Session()
try:
    # Check signature of _rpc, cmd, tool, batch
    rpc_params = inspect.signature(s._rpc).parameters
    cmd_params = inspect.signature(s.cmd).parameters
    tool_params = inspect.signature(s.tool).parameters
    batch_params = inspect.signature(s.batch).parameters

    print(f"_rpc parameters: {list(rpc_params.keys())}")
    print(f"cmd parameters: {list(cmd_params.keys())}")
    print(f"tool parameters: {list(tool_params.keys())}")
    print(f"batch parameters: {list(batch_params.keys())}")

    assert "timeout" not in rpc_params
    assert "timeout" not in cmd_params
    assert "timeout" not in tool_params
    assert "timeout" not in batch_params

    # Verify implementation of _rpc:
    # while True:
    #     line = self._p.stdout.readline()
    src = inspect.getsource(s._rpc)
    assert "readline()" in src
    assert "timeout" not in src
    print("CONFIRMED: _rpc performs unconditional blocking readline() with no timeout mechanism!")
finally:
    s.close()
