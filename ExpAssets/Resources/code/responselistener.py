import sdl2

from klibs.KLTime import precise_time
from klibs.KLEventQueue import pump, flush
from klibs.KLUserInterface import ui_request
from klibs.KLResponseCollectors import Response

# This is a draft of a new simple/flexible response collection module for KLibs.


class BaseResponseListener(object):
    """A base class for creating response listeners.
    
    The purpose of ResponseListeners is to make it easy to collect responses of a
    given type from participants (e.g. keypress responses, mouse cursor responses).
    There are a number of built-in ResponseListener classes for common use cases, but
    this base class is provided so that you can create your own.

    For accurate response timing, the stimuli that the participant responds to (e.g.
    a target in a cueing task) needs to be draw to the screen immediately before the
    collection loop starts. This is because it takes a few milliseconds (usually ~17)
    to refresh the screen, so you want to mark the start of the response period as
    immediately after the participant sees the stimuli.

    Args:
        timeout (float, optional): The maximum duration (in seconds) to wait for a
            valid response.

    """
    def __init__(self, timeout=None):
        self._loop_start = None
        self.timeout_ms = timeout * 1000 if timeout else None

    def _timestamp(self):
        # The timestamp (in milliseconds) to use as the start time for the loop.
        return precise_time() * 1000

    def collect(self):
        """Collects a single response from the participant.
        
        """
        resp = None
        self.init()
        while not resp:
            # Check if the collection loop has timed out
            if self.timeout_ms:
                if (self._timestamp() - self._loop_start) > self.timeout_ms:
                    break
            # Fetch event queue and check for valid responses
            events = pump(True)
            ui_request(queue=events)
            resp = self.listen(events)
        # If no response given, return default response
        if not resp:
            resp = Response(None, -1)
        return resp

    def init(self):
        """Initializes the listener for response collection.

        This method prepares the listener to enter its collection loop, initializing
        any necessary objects or hardware and setting the timestamp for when the
        collection loop started.
        
        This only needs to be called manually if using :meth:`listen` directly in a
        custom collection loop: otherwise, it is called internally by :meth:`collect`.

        """
        self._loop_start = self._timestamp()
        flush()

    def listen(self, q):
        """Checks a queue of input events for valid responses.

        This is the main method that needs to be defined when creating a custom
        ResponseListener: It checks a list of input events for valid responses, and
        returns the value and reaction time of the response if one has occured. It
        is used internally by :meth:`collect`, but can also be used directly to create
        custom response collection loops (along with :meth:`init` and :meth:`cleanup`)
        in cases where :meth:`collect` doesn't offer enough flexibility.

        Args:
            q (list): A list of input events to check for valid responses.

        Returns:
            :obj:`klibs.KLResponseCollector.Response` or None: A Response object containing the
            value and reaction time (in milliseconds) of the response, or None if no response
            has been made.
        
        """
        e = "ResponseListeners must have a defined 'listen' method"
        raise NotImplementedError(e)

    def cleanup(self):
        """Performs any necessary cleanup after response collection.

        This method is the inverse of the :meth:`init` method, resetting any
        initialized hardware or configured options to their original states. For
        example, if collecting an audio response from a microphone and `init` opens
        an audio stream for the device, this method would close it again after a
        response has been collected.

        This only needs to be called manually if using :meth:`listen` directly in a
        custom collection loop: otherwise, it is called internally by :meth:`collect`.

        """
        self._loop_start = None



class KeyPressListener(BaseResponseListener):
    """A helper class for listening for and collecting keypress responses.

    """
    def __init__(self, keymap, timeout=None):
        super(KeyPressListener, self).__init__(timeout)
        self._keymap = self._parse_keymap(keymap)

    def _timestamp(self):
        # Since keypress events have SDL timestamps, use SDL_GetTicks to mark the
        # start of the collection loop.
        return sdl2.SDL_GetTicks()

    def _parse_keymap(self, keymap):
        # Perform basic validation of the keymap
        if not isinstance(keymap, dict):
            raise TypeError("keymap must be a properly-formatted dict.")
        if len(keymap) == 0:
            raise ValueError("keymap must contain at least one key/label pair.")
        # Convert all key names in the map to SDL keycodes
        keycode_map = {}
        for key, label in keymap.items():
            if type(key) is str:
                keycode = sdl2.SDL_GetKeyFromName(key.encode('utf8'))
            else:
                keycode = key
            if keycode == 0:
                raise ValueError("'{0}' is not a recognized key name.".format(key))
            keycode_map[keycode] = label

        return keycode_map

    def listen(self, q):
        # Checks the input queue for any keypress events for keys in the keymap
        for event in q:
            if event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym # keyboard button event object
                if key.sym in self._keymap.keys():
                    value = self._keymap[key.sym]
                    rt = (event.key.timestamp - self._loop_start)
                    return Response(value, rt)
        return None
