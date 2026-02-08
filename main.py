import curses

def main(stdscr):
    # Clear screen
    stdscr.clear()

    # This is where your curses application logic goes
    stdscr.addstr(5, 10, "Hello, Curses on Linux!", curses.A_REVERSE)
    stdscr.addstr(7, 10, "Press any key to exit.")

    # Refresh the screen to show output
    stdscr.refresh()

    # Wait for a key press
    stdscr.getch()

# Start the curses application
curses.wrapper(main)
