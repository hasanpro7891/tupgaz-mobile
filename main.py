import sys
import os
import traceback

sys.dont_write_bytecode = True

try:
    from data.migration import run_migration
    run_migration()
except Exception:
    pass

try:
    import kivy
except ImportError:
    try:
        from main_tk import main as tk_main
        tk_main()
    except Exception:
        pass
    sys.exit(0)

try:
    from kivy_app import TupcularKraliKivyApp
    TupcularKraliKivyApp().run()
except Exception:
    try:
        log_path = os.path.join(os.environ.get('EXTERNAL_STORAGE', '/storage/emulated/0'), 'tupgaz_hata.txt')
        with open(log_path, 'w') as f:
            traceback.print_exc(file=f)
    except Exception:
        pass
