import dearpygui.dearpygui as dpg
from pytube import YouTube
from pytube.exceptions import *
from moviepy.editor import *


class Downloader:
    def __init__(self, yt_object):
        self._yt = yt_object
        self._streams_dict = {}
        self._streams = None

    def _kbps_string_to_int(self, kbps):
        kbps_digits = ""
        for c in kbps:
            if c.isdigit():
                kbps_digits += c

        return int(kbps_digits)

    # Convert the abr string to int to sort the streams by kbps later
    def _get_audio_streams(self):
        self._streams = self._yt.streams.filter(only_audio=True).filter(
            file_extension="mp4"
        )

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

    def download_temp(self, file_name="tmp_dl.mp4"):
        # Variable local to the entire class so that we can use it in `slice()` function.
        self._file_name = file_name
        itag_var = self._get_audio_streams()["itag"]
        print("Downloading to...")
        if self._streams is not None:
            # Moviepy download info/progress will be printed in the terminal
            print(self._streams.get_by_itag(itag_var).download(filename=f"{file_name}"))

    def slice(self, file_type, start=0, end=None, output_file_name="output_audio_file"):
        try:
            audio_clip = AudioFileClip(f"{self._file_name}").subclip(
                t_start=start, t_end=end
            )
            try:
                if file_type == "aac":
                    audio_clip.write_audiofile(
                        filename=f"{output_file_name}.aac", codec="aac"
                    )
                else:
                    audio_clip.write_audiofile(
                        filename=f"{output_file_name}.{file_type}" 
                    )
            except:
                print("Error downloading; invalid output file name.")
        except:
            print("Invalid start/end time.")

    def download(self, start, end, output_file_name, file_type):
        self.download_temp()
        self.slice(start, end, output_file_name, file_type)

# Class to handle the callbacks
class Callback:
    def __init__(self):
        self._start = 0
        self._end = None
        self._output_file_name = "output_audio_file"
        self._dl_object = None
        self._file_type = "aac"

    def test_callback(self):
        pass

    def valid_trim(self):
        pass

    def valid_file_name(self):
        pass

    @property
    def dl_object(self):
        return self._dl_object

    @dl_object.setter
    def dl_object(self, v):
        self._dl_object = v

    def start_cb(self, sender, app_data, user_data):
        self._start = 0 if app_data == "" else app_data

    def end_cb(self, sender, app_data, user_data):
        self._end = None if app_data == "" else app_data

    def file_name_cb(self, sender, app_data, user_data):
        self._output_file_name = app_data

    def file_type_cb(self, sender, app_data, user_data):
        self._file_type = app_data

    def dl_btn_cb(self, sender, app_data, user_data):
        print(f"{self._start} {self._end} {self._output_file_name}")
        if self.dl_object is not None:
            self.dl_object.download(self._start, self._end, self._output_file_name, self._file_type)


class App:
    def __init__(self):
        self._info_string = ""
        self._cb = Callback()

    # Get video info
    def link_info(self, yt_link):
        self._info_string += f"{yt_link.title}\n"
        self._info_string += (
            f"{yt_link.length//60} minutes {yt_link.length % 60} seconds\n"
        )
        self._info_string += (
            f"Uploaded: {yt_link.publish_date.date()} by {yt_link.author}\n"
        )

    def get_url(self, sender, app_data, user_data):
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
                with dpg.child_window(width=600, tag="yt_url", border=False):

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
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            tag="dl_btn", label="Download", callback=self._cb.dl_btn_cb
                        )
                        dpg.add_spacer()
                        dpg.add_text("feedback...")

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
