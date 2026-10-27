import sys

if len(sys.argv) > 1:
    # python -m mechvane setup|ui|mcp, for when the mechvane script is not on PATH (Windows user installs)
    from .cli import main as cli_main

    sys.exit(cli_main())
else:
    # Without arguments: the MCP server, as in existing .mcp.json files
    from .server import main

    main()
