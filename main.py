import sys
import os
sys.dont_write_bytecode = True

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from data.migration import run_migration
run_migration()

try:
    import kivy
except ImportError:
    from main_tk import main as tk_main
    tk_main()
    sys.exit(0)

from kivy_app import TupcularKraliKivyApp
TupcularKraliKivyApp().run()
