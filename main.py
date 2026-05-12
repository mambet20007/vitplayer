#!/usr/bin/env python3
import curses
import sys
import os
import sounddevice as sd
import soundfile as sf
import numpy as np

os.environ.setdefault('ESCDELAY', '25')

def quite():
    sys.exit(0)

class App: 
    def __init__(self, stdscr):
        self.screen = stdscr
        self.running = True
        self.stream = None
        self.data = None
        self.fs = None
        self.current_frame = 0
        self.is_playing = False
        self.viz_data = np.zeros(1024)
        self.total_time = None
    
    def audio_callback(self, outdata, frames, time, status):
        if self.is_playing and self.current_frame < len(self.data):
            chunk = self.data[self.current_frame : self.current_frame + frames]
            # Заполняем outdata данными из файла
            if len(chunk) < frames:
                outdata[:len(chunk)] = chunk
                outdata[len(chunk):].fill(0)
                self.is_playing = False # Трек кончился
            else:
                outdata[:] = chunk
                self.current_frame += frames
            # Берем среднее по каналам для визуализации
            v_data = np.mean(chunk, axis=1) if chunk.ndim > 1 else chunk
            # Считаем амплитуды частот и сохраняем в переменную класса
            fft_complex = np.fft.rfft(v_data)
            self.viz_data = np.abs(fft_complex)[:int(curses.COLS / 2)]
        else:
            outdata.fill(0)
            self.viz_data = np.zeros(20)

    def play_song(self, path):
        if self.stream:
            self.stream.stop()
        self.data, self.fs = sf.read(path)
        self.current_frame = 0
        self.total_time = len(self.data) / self.fs # секунды
        self.is_playing = True
        self.stream = sd.OutputStream(samplerate=self.fs, channels=self.data.shape[1], callback=self.audio_callback)
        self.stream = sd.OutputStream(samplerate=self.fs,channels=self.data.shape[1] if self.data.ndim > 1 else 1,callback=self.audio_callback,blocksize=4096)
        self.stream.start()

    def arrow(self, x, y):
        self.screen.addstr(y, x, "<---")

    def screen_clear(self, xX, yY, indX, indY):
        for y in range(0, yY):
            for x in range(0, xX):
                self.screen.addstr(y + indY, x + indX, " ")

    def draw(self):
        self.screen.nodelay(True)
        self.screen.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.curs_set(False)
        curses.update_lines_cols()
        show_playlist = False
        ind = 11
        arrowX = int(curses.COLS / 2) - 8
        arrowY = 3
        arrow_pos = 0
        directory = "/home/mambet/Music"
        folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
        len_folders = len(folders)
        in_directory = True
        len_playlist = None
        current_playlist_path = None
        playlists_path = [os.path.abspath(os.path.join(directory, name)) for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
        song_is_playing = None
        parent_dir = None
        num_of_song = None
        num_of_current_song = None

        while self.running:
            if show_playlist and current_playlist_path:
                playlist = [f for f in os.listdir(current_playlist_path) if os.path.isfile(os.path.join(current_playlist_path, f))]
                len_playlist = len(playlist)
                songs_path = [os.path.abspath(os.path.join(current_playlist_path, name)) for name in os.listdir(current_playlist_path) if os.path.isfile(os.path.join(current_playlist_path, name))]
            

            if in_directory:
                scroll = 2 + len_folders
            else:
                scroll = 2 + len_playlist
            
            self.screen.erase() # обновление экрана

            self.screen.attron(curses.color_pair(1))
            # тут идет отрисовка всего
            self.screen.addstr(2, 10, "\\")
            # показывает директории
            if in_directory:
                self.screen.addstr(1, 1, "DIRECTORY")
                if scroll < curses.LINES - 3:
                    for index in range(0, len_folders):
                        self.screen.addnstr(3 + index, ind, folders[index], 21)
                else:
                    scroll_offset = max(0, arrow_pos - (curses.LINES - 6))
                    for index in range(0, curses.LINES - 5):
                        if index + scroll_offset < len_folders:
                            self.screen.addnstr(3 + index, ind, folders[index + scroll_offset], 21)
            # показывает плейлист выбраной директории
            if show_playlist:
                self.screen.addstr(1, 1, "PLAYLIST")
                self.screen.addstr(1, 10, parent_dir)
                if scroll < curses.LINES - 3:
                    for index in range(0, len_playlist):
                        self.screen.addnstr(3 + index, ind, playlist[index][:-4], int(curses.COLS / 2) - 19)
                else:
                    scroll_offset = max(0, arrow_pos - (curses.LINES - 6))
                    for index in range(0, curses.LINES - 5):
                        if index + scroll_offset < len_playlist:
                            self.screen.addnstr(3 + index, ind, playlist[index + scroll_offset][:-4], int(curses.COLS / 2) - 19)
            
            if song_is_playing != None:
                current_time = self.current_frame / self.fs # секунды
                mins_total = int(self.total_time // 60)
                secs_total = int(self.total_time % 60)
                mins_current = int(current_time // 60)
                secs_current = int(current_time % 60)
                time_total_str =f"{mins_total:02d}:{secs_total:02d}"
                time_current_str =f"{mins_current:02d}:{secs_current:02d}"
                self.screen.addstr(curses.LINES - 4, int(curses.COLS / 2) - 5, time_current_str)
                self.screen.addstr(curses.LINES - 4, curses.COLS - 6, time_total_str)
                bar_width = int(curses.COLS / 2) - 7
                progress = self.current_frame / len(self.data) if self.total_time > 0 else 0
                filled_width = int(bar_width * progress)
                bar_str = "#" * filled_width + "-" * (bar_width - filled_width)
                self.screen.addstr(curses.LINES - 4, int(curses.COLS / 2),f"[{bar_str}]" )
                if play:
                    self.screen.addstr(1, int(curses.COLS / 2) - 2, "NOW PLAYING ")
                    self.screen.addnstr(1, int(curses.COLS / 2) + 10, song_is_playing[:-4], int(curses.COLS / 2) - 11)
                else:
                    self.screen.addstr(1, int(curses.COLS / 2) - 2, "SYBAU ")
                    self.screen.addnstr(1, int(curses.COLS / 2) + 4, song_is_playing[:-4], int(curses.COLS / 2) - 5)
                if int(current_time) == int(self.total_time) - 1:
                    if num_of_song + 1 < len_playlist:
                        num_of_song += 1
                        current_song_path = songs_path[num_of_song]
                        song_is_playing = playlist[num_of_song]
                    else:
                        song_is_playing = None
            else:
                self.screen.addstr(1, int(curses.COLS / 2) - 2, "NOTHING IS PLAYING YET")
            if num_of_song != num_of_current_song:
                self.play_song(songs_path[num_of_song])
                num_of_current_song = num_of_song


            self.screen.border()
            self.screen.addstr(curses.LINES - 1, curses.COLS - 6, "VIT")
            self.arrow(int(arrowX), int(arrowY))
            if self.is_playing and hasattr(self, 'viz_data'):
                for i, val in enumerate(self.viz_data[:58]):
                    bar_height = int(np.clip(val * 0.7, 0, curses.LINES - 12))
                    if i % 2 == 0:
                        for h in range(bar_height):
                            try:
                                self.screen.addstr(curses.LINES - 5 - h, int(curses.COLS / 2) + (i * 2), "┃")
                            except:
                                pass
            # тут отрисовка заканчивается
            self.screen.attroff(curses.color_pair(1))
            self.screen.refresh() 

            # обработка нажатий
            try:
                key = self.screen.getch()
            except:
                key = -1

            if key == 27: #Esc
                quite()
            if key == curses.KEY_UP:
                if arrowY > 3 and arrowY >= arrow_pos + 3:
                    arrowY -= 1
                    arrow_pos = max(0, arrow_pos - 1)
                elif arrow_pos > 0:
                    arrow_pos -= 1

            if key == curses.KEY_DOWN:
                max_items = len_folders if in_directory else len_playlist
                max_pos = max_items - 1

                if scroll < curses.LINES - 3:
                    if arrowY != scroll:
                        arrowY += 1
                        arrow_pos = min(arrow_pos + 1, max_pos)
                    else:
                        arrowY = scroll
                else:
                    if arrowY < curses.LINES - 3:
                        arrowY += 1
                        arrow_pos = min(arrow_pos + 1, max_pos)
                    elif arrow_pos < max_pos:
                        arrow_pos += 1
 
            if key in (curses.KEY_ENTER, 10, 13):
                if in_directory:
                    current_playlist_path = playlists_path[arrow_pos]
                    show_playlist = True
                    arrowY = 3
                    parent_dir = folders[arrow_pos]
                    arrow_pos = 0
                    in_directory = False
                else:
                    play = True
                    current_song_path = songs_path[arrow_pos]
                    num_of_song = arrow_pos
                    num_of_current_song = num_of_song
                    song_is_playing = playlist[arrow_pos]
                    self.play_song(songs_path[num_of_song])

            if key == curses.KEY_LEFT:
                if show_playlist:
                    show_playlist = False
                    in_directory = True
                    current_playlist_path = None
                    arrow_pos = 0
                    arrowY = 3
            if key == 32: # пробел
                self.is_playing = not self.is_playing
                play = not play


curses.wrapper(lambda s: App(s).draw())
