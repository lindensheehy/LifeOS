#include <windows.h>

// Using WinMain instead of main() tells the Windows linker to use the GUI subsystem, 
// meaning this exe will NEVER spawn a command prompt window itself when you click it.
int APIENTRY WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    // The command we want to run. 
    // We use python.exe, but CREATE_NO_WINDOW ensures it stays completely invisible.
    char cmd[] = "venv\\Scripts\\python.exe controller.py";

    // Launch the process
    BOOL success = CreateProcessA(
        NULL,               // Application name
        cmd,                // Command line
        NULL,               // Process attributes
        NULL,               // Thread attributes
        FALSE,              // Inherit handles (FALSE prevents tethering to the parent)
        CREATE_NO_WINDOW,   // Flags to fully decouple the terminal
        NULL,               // Environment
        NULL,               // Current directory (NULL uses the exe's current dir)
        &si,                // Startup Info
        &pi                 // Process Info
    );

    if (success) {
        // We successfully launched the python script!
        // Now we immediately close our handles to the child process.
        // This cuts the umbilical cord, allowing the child to live on independently
        // even after this launcher exe terminates a millisecond later.
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        // If Python isn't in PATH or controller.py is missing, show a native Windows error popup
        MessageBoxA(NULL, "Failed to launch controller.py. Ensure python is in your PATH.", "LifeOS Launcher Error", MB_ICONERROR | MB_OK);
    }

    return 0;
}
