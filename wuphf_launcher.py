"""Entry point for a future packaged WUPHF executable."""
import sys
from pathlib import Path

_dll_directory=None


def _prepare_windows_dlls():
    global _dll_directory
    if sys.platform!='win32' or not getattr(sys,'frozen',False) or _dll_directory is not None:return
    import ctypes
    import os
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.SetDllDirectoryW.argtypes=[ctypes.c_wchar_p]
    kernel.SetDllDirectoryW.restype=ctypes.c_int
    directory=os.add_dll_directory(sys._MEIPASS)
    # Keep Python's DLL dependencies available without passing the bundle search path to Codex.
    if not kernel.SetDllDirectoryW(None):
        directory.close()
        raise RuntimeError('Could not reset the Windows DLL search path.')
    _dll_directory=directory


def main(argv=None):
    _prepare_windows_dlls()
    if sys.platform=='darwin' and getattr(sys,'frozen',False):
        import os
        os.environ['PATH']=os.environ.get('PATH','/usr/bin:/bin')+':/opt/homebrew/bin:/usr/local/bin'
        if 'SSL_CERT_FILE' not in os.environ and 'SSL_CERT_DIR' not in os.environ and Path('/etc/ssl/cert.pem').is_file():
            os.environ['SSL_CERT_FILE']='/etc/ssl/cert.pem'
    args=sys.argv[1:] if argv is None else argv
    if args==['--version']:
        print('WUPHF '+(Path(__file__).resolve().parent/'VERSION').read_text(encoding='utf-8').strip())
    elif args==['--install']:
        from wuphf.install import main as run_install
        try:run_install()
        except (ValueError,OSError,RuntimeError) as error:raise SystemExit(str(error)) from None
    elif args==['--background']:
        from wuphf.cli import main as run_cli
        run_cli(['run'])
    elif args==['--check-codex']:
        from wuphf.core import read_snapshot
        snap=read_snapshot()
        print('Codex responded; reset details '+('complete.' if snap.get('complete') else 'unavailable or incomplete.'))
    elif args==['--check-assets']:
        from wuphf.google_auth import PUBLIC_CLIENT, parse_client
        from wuphf.i18n import languages
        from wuphf.storage import load
        from wuphf.web import PAGE, PIXEL_FONT
        if (b'WUPHF' not in PAGE.read_bytes() or PIXEL_FONT.read_bytes()[:4]!=b'wOF2'
                or len(languages())!=8 or not (PAGE.parent/'assets'/'geist-pixel-OFL.txt').is_file()
                or not all((PAGE.parent.parent/name).is_file() for name in ('LICENSE','VERSION','README.md','CHANGELOG.md'))):
            raise SystemExit('Packaged assets are incomplete.')
        parse_client(load(PUBLIC_CLIENT,{}))
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
        raise SystemExit('Usage: WUPHF [--version|--install|--background|--check-assets|--check-codex]')


if __name__=='__main__':
    main()
