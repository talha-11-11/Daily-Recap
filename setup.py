from cx_Freeze import setup, Executable

# Include your application database and any other files you need.
include_files = [("database/apparel.db", "database/apparel.db")]

# Define build options
build_exe_options = {
    "packages": ["sys", "PyQt5", "sqlite3"],
    "include_files": include_files,
}

# Set the base for the application; necessary for Windows GUI applications
base = None
import sys
if sys.platform == "win32":
    base = "Win32GUI"

# Setup the application
setup(
    name="Clothing Manufacturing Manager",
    version="1.0",
    description="Clothing manufacturing management software!",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)]
)
