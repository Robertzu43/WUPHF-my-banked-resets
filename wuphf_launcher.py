"""Entry point for a future packaged WUPHF executable."""
import sys


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if args==['--background']:
        from wuphf.cli import main as run_cli
        run_cli(['run'])
    elif args==['--check-codex']:
        from wuphf.core import read_snapshot
        snap=read_snapshot()
        print('Codex responded; reset details '+('complete.' if snap.get('complete') else 'unavailable or incomplete.'))
    elif args==['--check-assets']:
        from wuphf.i18n import languages
        from wuphf.web import PAGE, PIXEL_FONT
        if (b'WUPHF' not in PAGE.read_bytes() or PIXEL_FONT.read_bytes()[:4]!=b'wOF2'
                or len(languages())!=8 or not (PAGE.parent/'assets'/'geist-pixel-OFL.txt').is_file()
                or not (PAGE.parent.parent/'LICENSE').is_file()):
            raise SystemExit('Packaged assets are incomplete.')
        if getattr(sys,'frozen',False) and sys.platform in ('win32','linux'):
            from importlib import import_module
            module='keyring.backends.Windows' if sys.platform=='win32' else 'keyring.backends.SecretService'
            backend='WinVaultKeyring' if sys.platform=='win32' else 'Keyring'
            getattr(import_module(module),backend)
        print('WUPHF assets OK')
    elif not args:
        from wuphf.web import main as run_web
        run_web()
    else:
        raise SystemExit('Usage: WUPHF [--background|--check-assets|--check-codex]')


if __name__=='__main__':
    main()
