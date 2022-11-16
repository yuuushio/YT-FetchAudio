import dearpygui.dearpygui as dpg
from pytube import YouTube
from pytube.exceptions import *
from moviepy.editor import *
import yaml
import os
import subprocess


class Config:
    """
    Class to read config file.
    """

    # This will make it so that the user doesn't have to input the
    # output directory each time the app is run; the app will fetch 
    # it from the config file instead.

    def __init__(self):
        self._data = ""
        self._read_config_file()

    @property
    def directory(self):
        return self._data

    @directory.setter
    def directory(self, v):
        self._data = v

    def _read_config_file(self):
        with open("config.yml", "r") as f:
            yml_data = yaml.safe_load(f)

        # `expanduser` used to expand paths containing tilde
        if os.path.exists(os.path.expanduser(yml_data["directory"])):
            self.directory = os.path.expanduser(yml_data["directory"])
        else:
            self.directory = ""

class Downloader:
    """
    Class used to handle downloading, converting and trimming the YouTube video.
    """
    def __init__(self, yt_object):
        self._yt = yt_object
        self._streams_dict = {}
        self._streams = None
        self._file_directory = ""

    # Convert the abr string to int to sort the streams by kbps later
    def _kbps_string_to_int(self, kbps):
        kbps_digits = ""
        for c in kbps:
            if c.isdigit():
                kbps_digits += c

        return int(kbps_digits)

    def _get_audio_streams(self):
        self._streams = self._yt.streams.filter(only_audio=True).filter(
            file_extension="mp4"
        )

        # Dict containing the necessary info for each stream
        for i in range(len(self._streams)):
            self._streams_dict[i + 1] = {
                "itag": self._streams[i].itag,
                "type": self._streams[i].mime_type,
                "abr": self._kbps_string_to_int(self._streams[i].abr),
            }

        # Sort streams dictionary by each stream's abr (kbps) - to get the highest quality audio stream
        highest_kbps_stream = sorted(
            self._streams_dict, key=lambda x: -self._streams_dict[x]["abr"]
        )

        # `[0]` is the index to the key with the highest kbps
        return self._streams_dict[highest_kbps_stream[0]]

    def set_path(self, v: str)->str:
        if v == "" or v is None:
            return ""
        else:
            if v[-1] != "/":
                return v
            else:
                # Because we're going to put a `/` from our side
                return v[:-1]

    def download_temp(self, user_data, file_name="tmp_dl.mp4"):
        # Variable local to the entire class so that we can use it in `slice()` function.
        self._file_name = file_name
        itag_var = self._get_audio_streams()["itag"]
        dpg.set_value(user_data, "Downloading...")
        if self._streams is not None:
            #print(self._streams.get_by_itag(itag_var).download(filename=f"{file_name}"))
            self._streams.get_by_itag(itag_var).download(filename=f"{file_name}")

    def slice(self, user_data, file_type, start=0, end=None, output_file_name="output_audio_file"):

        try:
            # Format:
            # - `<sec>`
            # - `<min, sec>`
            # - `<hr, min, sec>`
            audio_clip = AudioFileClip(f"{self._file_name}").subclip(
                t_start=start, t_end=end
            )
            try:
                cfg = Config()
                self._file_directory = self.set_path(cfg.directory)

                if file_type == "aac":
                    if self._file_directory is not None and self._file_directory != "":
                        # `write_audiofile` returns None when it's done converting/subcliping;
                        #   this can be used to provide feedback.
                        fb_str = audio_clip.write_audiofile(
                            filename=f"{self._file_directory}/{output_file_name}.aac", codec="aac"
                        )
                        if fb_str is None: dpg.set_value(user_data, "Download complete!")
                    else:
                        # Else download in the directory this program resides
                        fb_str = audio_clip.write_audiofile(
                            filename=f"{output_file_name}.aac", codec="aac"
                        )
                        if fb_str is None: dpg.set_value(user_data, "Download complete!")
                else:
                    if self._file_directory is not None and self._file_directory != "":
                        fb_str = audio_clip.write_audiofile(
                            filename=f"{self._file_directory}/{output_file_name}.{file_type}"
                        )
                        if fb_str is None: dpg.set_value(user_data, "Download complete!")
                    else:
                        fb_str = audio_clip.write_audiofile(
                            filename=f"{output_file_name}.{file_type}" 
                        )
                        if fb_str is None: dpg.set_value(user_data, "Download complete!")

                # remove the youtube mp4 video we downloaded
                subprocess.call(["rm", f"{self._file_name}"])
            except:
                    dpg.set_value(user_data, "Error downloading; invalid output file name.")
        except:
            dpg.set_value(user_data, "Invalid start/end time.")

    def download(self,user_data,start, end, output_file_name, file_type):
        # Download raw youtube vid (audio stream) in mp4 format
        self.download_temp(user_data)

        # Convert downloaded youtube vid to mp3,aac...; subclip if parameters are specified
        self.slice(user_data, file_type, start, end, output_file_name)

class Callback:
    """
    Class used to handle dpg callbacks.
    """

    def __init__(self):
        self._start = 0
        self._end = None
        self._output_file_name = "output_audio_file"
        self._dl_object = None
        self._file_type = "aac"

    def valid_file_name(self):
        pass

    @property
    def dl_object(self):
        return self._dl_object

    @dl_object.setter
    def dl_object(self, v):
        self._dl_object = v

    def start_cb(self, sender, app_data, user_data):
        self._start = 0 if app_data == "" else eval(app_data)

    def end_cb(self, sender, app_data, user_data):
        self._end = None if app_data == "" else eval(app_data)

    def file_name_cb(self, sender, app_data, user_data):
        self._output_file_name = app_data

    def file_type_cb(self, sender, app_data, user_data):
        self._file_type = app_data

    def dl_btn_cb(self, sender, app_data, user_data):
        # print(f"{self._start} {self._end} {self._output_file_name}")
        if self.dl_object is not None:
            self.dl_object.download(user_data, self._start, self._end, self._output_file_name, self._file_type)



class App:
    """
    Class used to handle the main GUI.
    """
    def __init__(self):
        self._info_string = ""
        self._cb = Callback()
        self._current_url = ""

    # Get video info
    def link_info(self, yt_link):
        self._info_string += f"{yt_link.title}\n"
        self._info_string += (
            f"{yt_link.length//60} minutes {yt_link.length % 60} seconds\n"
        )
        self._info_string += (
            f"Uploaded: {yt_link.publish_date.date()} by {yt_link.author}\n"
        )

    def _reset_info_string(self):
        self._info_string = ""

    def get_url(self, sender, app_data, user_data):
        # Clear the current link information (if any) when a new link is entered
        self._reset_info_string()
        dpg.set_value(user_data, self._info_string)

        # Validating url using pytube's exception
        try:
            yt_link = YouTube(str(app_data))

            # generate info of the link
            self.link_info(yt_link)
            self._cb.dl_object = Downloader(yt_link)

            # user_data used to output video's info upon entering url
            dpg.set_value(user_data, self._info_string)

        except PytubeError:
            print("Enter a valid YouTube link.")

    def main_dpg_ops(self):
        with dpg.window(
            pos=[0, 0],
            autosize=True,
            no_resize=True,
            no_title_bar=True,
            tag="Primary Window",
        ):

            with dpg.group(horizontal=True):
                with dpg.child_window(width=450, tag="yt_url", border=False):

                    # Text input group to enter the video url
                    dpg.add_text("URL:")
                    with dpg.group():
                        text_control = dpg.add_text(tag="output_txt", default_value="")
                        dpg.add_spacer()
                        with dpg.group():
                            dpg.add_input_text(
                                before=text_control,
                                tag="input_yt_url",
                                callback=self.get_url,
                                width=550,
                                user_data=text_control,
                            )
                            dpg.add_spacer()

                    # Start/end time group
                    with dpg.group(horizontal=True):
                        dpg.add_text("Start:")
                        dpg.add_input_text(
                            tag="start_time", width=100, callback=self._cb.start_cb
                        )
                        dpg.add_spacer()
                        dpg.add_text("End:")
                        dpg.add_input_text(
                            tag="end_time", width=100, callback=self._cb.end_cb
                        )

                    with dpg.group():
                        dpg.add_spacer()

                    # Get file name of the output
                    with dpg.group(horizontal=True):
                        dpg.add_text("Output File Name:")
                        dpg.add_input_text(
                            tag="output_file_name",
                            width=200,
                            callback=self._cb.file_name_cb,
                        )
                        dpg.add_combo(("aac", "mp3"), default_value="aac", callback=self._cb.file_type_cb, tag="audio_type", width=90)

                    with dpg.group():
                        dpg.add_spacer()

                    # Download button group
                    with dpg.group():
                        feedback_text = dpg.add_text(tag="feedback", default_value="")
                        dpg.add_button(
                            tag="dl_btn", label="Download", callback=self._cb.dl_btn_cb,
                            user_data = feedback_text, width=100, height=30
                        )
                        dpg.add_spacer()

    def start_gui(self):
        dpg.create_context()
        self.main_dpg_ops()
        dpg.create_viewport(title="YT-2-mp3", width=400, height=400)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()


def main():
    gui = App()
    gui.start_gui()


if __name__ == "__main__":
    main()
