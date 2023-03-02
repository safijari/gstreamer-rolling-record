import numpy as np
import os, sys
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

frame_format = "RGBA"

Gst.init()
pipeline = Gst.parse_launch(
    f"""
    ximagesrc ! videoscale ! video/x-raw,framerate=60/1,width=1280,height=800 ! jpegenc ! fakesink name=s
"""
)
items = {"count": 0, "caps": None}

i = 0

def on_frame_probe(pad, info):
    if items["caps"] is None:
        items["caps"] = pad.get_current_caps()
    items["count"] += 1
    print(items["count"])
    buf = info.get_buffer()
    buffer_to_image_tensor(buf, pad.get_current_caps())
    timestamp = buf.pts / Gst.SECOND
    print(f"[{timestamp}]")
    return Gst.PadProbeReturn.OK


def buffer_to_image_tensor(buf, caps):
    pixel_bytes = 4
    caps_structure = caps.get_structure(0)
    height, width = caps_structure.get_value("height"), caps_structure.get_value(
        "width"
    )

    is_mapped, map_info = buf.map(Gst.MapFlags.READ)
    print(len(map_info.data))
    # image_array = np.ndarray(
    #     (height, width, pixel_bytes), dtype=np.uint8, buffer=map_info.data
    # ).copy()  # extend array lifetime beyond subsequent unmap
    # return image_array[:, :, :3]  # RGBA -> RGB


pipeline.get_by_name("s").get_static_pad("sink").add_probe(
    Gst.PadProbeType.BUFFER, on_frame_probe
)

pipeline.set_state(Gst.State.PLAYING)

try:
    while True:
        msg = pipeline.get_bus().timed_pop_filtered(
            Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR
        )
        if msg:
            text = msg.get_structure().to_string() if msg.get_structure() else ""
            msg_type = Gst.message_type_get_name(msg.type)
            print(f"{msg.src.name}: [{msg_type}] {text}")
            break
finally:
    open(f"logs/{os.path.splitext(sys.argv[0])[0]}.pipeline.dot", "w").write(
        Gst.debug_bin_to_dot_data(pipeline, Gst.DebugGraphDetails.ALL)
    )
    pipeline.set_state(Gst.State.NULL)
