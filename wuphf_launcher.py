"""Entry point for a future packaged WUPHF executable."""
import sys


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if args==['--background']:
        from wuphf.cli import main as run_cli
        run_cli(['run'])
    elif not args:
        from wuphf.web import main as run_web
        run_web()
    else:
        raise SystemExit('Usage: WUPHF [--background]')


if __name__=='__main__':
    main()
