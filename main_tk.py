import sys
import os
sys.dont_write_bytecode = True

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        from data.migration import run_migration
        run_migration()

        import tkinter as tk
        from app import TupcularKraliApp

        root = tk.Tk()
        app = TupcularKraliApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import traceback
        from tkinter import messagebox
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Kritik Hata",
                f"Program başlatılamadı:\n\n{e}\n\n{traceback.format_exc()}")
        except Exception:
            print(f"Kritik Hata: {e}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    main()
