import os
import sys
import subprocess
import signal
import time
from datetime import datetime
import time

DEPSPATH = "/home/deck/homebrew/plugins/decky-recorder/bin"
GSTPLUGINSPATH = DEPSPATH + "/gstreamer-1.0"
TMPLOCATION = "/tmp"

import logging

logging.basicConfig(
    filename="/tmp/decky-recorder.log",
    format="Decky Recorder: %(asctime)s %(levelname)s %(message)s",
    filemode="w+",
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
std_out_file = open("/tmp/decky-recorder-std-out.log", "w")
std_err_file = open("/tmp/decky-recorder-std-err.log", "w")
logging.getLogger().addHandler(logging.StreamHandler())

class Plugin:

    _recording_process = None

    _tmpFilepath: str = None
    _filepath: str = None

    _mode: str = "localFile"
    _audioBitrate: int = 128
    _localFilePath: str = "/home/jari/Videos"
    _fileformat: str = "mp4"

    # Starts the capturing process
    def start_capturing(self):
        logger.info("Starting recording")
        if Plugin.is_capturing(self) == True:
            logger.info("Error: Already recording")
            return

        os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
        # os.environ["XDG_SESSION_TYPE"] = "wayland"
        os.environ["HOME"] = "/home/jari"

        # Start command including plugin path and ld_lib path
        start_command = "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv".format(
            GSTPLUGINSPATH, DEPSPATH
        )

        # Video Pipeline
        # videoPipeline = "pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink !"
    
        videoPipeline = "ximagesrc ! video/x-raw,framerate=5/1 ! videoconvert ! theoraenc ! oggmux name=sink !"
        cmd = "{} {}".format(start_command, videoPipeline)

        # If mode is localFile
        if self._mode == "localFile":
            logger.info("Local File Recording")
            dateTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            self._tmpFilepath = "{}/Decky-Recorder_{}.mp4".format(TMPLOCATION, dateTime)
            self._filepath = "{}/Decky-Recorder_{}.{}".format(
                self._localFilePath, dateTime, self._fileformat
            )
            fileSinkPipeline = " filesink location={}".format(self._tmpFilepath)
            cmd = cmd + fileSinkPipeline
        else:
            logger.info("Mode {} does not exist".format(self._mode))
            return

        # Creates audio pipeline
        # monitor = subprocess.getoutput("pactl get-default-sink") + ".monitor"
        # cmd = (
        #     cmd
        #     + ' pulsesrc device="Recording_{}" ! audioconvert ! lamemp3enc target=bitrate bitrate={} cbr=true ! sink.audio_0'.format(
        #         monitor, self._audioBitrate
        #     )
        # )

        # Starts the capture process
        logger.info("Command: " + cmd)
        self._recording_process = subprocess.Popen(
            cmd, shell=True, stdout=std_out_file, stderr=std_err_file
        )
        logger.info("Recording started!")
        return

    # Stops the capturing process and cleans up if the mode requires
    def stop_capturing(self):
        logger.info("Stopping recording")
        if Plugin.is_capturing(self) == False:
            logger.info("Error: No recording process to stop")
            return
        logger.info("Sending sigin")
        self._recording_process.send_signal(signal.SIGINT)
        logger.info("Sigin sent. Waiting...")
        self._recording_process.wait()
        logger.info("Waiting finished")
        self._recording_process = None
        logger.info("Recording stopped!")

        # if recording was a local file
        if self._mode == "localFile":
            logger.info("Repairing file")
            ffmpegCmd = "ffmpeg -i {} -c copy {}".format(
                self._tmpFilepath, self._filepath
            )
            logger.info("Command: " + ffmpegCmd)
            self._tmpFilepath = None
            self._filepath = None
            ffmpeg = subprocess.Popen(
                ffmpegCmd, shell=True, stdout=std_out_file, stderr=std_err_file
            )
            ffmpeg.wait()
            logger.info("File copied with ffmpeg")
            os.remove(self._tmpFilepath)
            logger.info("Tmpfile deleted")
        return

    # Returns true if the plugin is currently capturing
    def is_capturing(self):
        logger.info("Is capturing? " + str(self._recording_process is not None))
        return self._recording_process is not None

    # Sets the current mode, supported modes are: localFile
    def set_current_mode(self, mode: str):
        logger.info("New mode: " + mode)
        self._mode = mode

    # Gets the current mode
    def get_current_mode(self):
        logger.info("Current mode: " + self._mode)
        return self._mode

    # Sets audio bitrate
    def set_audio_bitrate(self, aduioBitrate: int):
        logger.info("New audio bitrate: " + aduioBitrate)
        self._audioBitrate = aduioBitrate

    # Gets the audio bitrate
    def get_audio_bitrate(self):
        logger.info("Current audio bitrate: " + self._audioBitrate)
        return self._audioBitrate

    # Sets local FilePath
    def set_local_filepath(self, localFilePath: str):
        logger.info("New local filepath: " + localFilePath)
        self._localFilePath = localFilePath

    # Gets the local FilePath
    def get_local_filepath(self):
        logger.info("Current local filepath: " + self._localFilePath)
        return self._localFilePath

    # Sets local file format
    def set_local_fileformat(self, fileformat: str):
        logger.info("New local file format: " + fileformat)
        self._fileformat = fileformat

    # Gets the file format
    def get_local_fileformat(self):
        logger.info("Current local file format: " + self._fileformat)
        return self._fileformat

    def loadConfig(self):
        logger.info("Loading config")
        ### TODO: IMPLEMENT ###
        self._mode = "localFile"
        self._audioBitrate = 128
        self._localFilePath = "/home/deck/Videos"
        self._fileformat = "mp4"
        return

    def saveConfig(self):
        logger.info("Saving config")
        ### TODO: IMPLEMENT ###
        return

    def _main(self):
        Plugin.loadConfig(self)
        return

    def _unload(self):
        if Plugin.is_capturing(self) == True:
            Plugin.end_recording(self)
        Plugin.saveConfig(self)
        return


def main():
    p = Plugin()
    p.start_capturing()
    time.sleep(2)
    p.stop_capturing()


if __name__ == "__main__":
    main()