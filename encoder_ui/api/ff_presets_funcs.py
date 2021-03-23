from ff_presets.preset_stream import Stream
from ff_presets.config import Config
import logging
import traceback


Config(is_library_mode=True)


def compile_ff_preset(stream_preset) -> (Stream, list):
   # Returned stream and list of errors
   try:
      stream = Stream(preset=stream_preset)
      if stream.is_valid:
         return stream, None
      else:
         return stream, stream.validation_errors
   except Exception as e:
      logging.error(traceback.format_exc())
      return None, [str(e), ]
