import sys
import queue
import threading
import time
import logging

from . import wlmConst
from . import wlmData

logger = logging.getLogger(__name__)


CALLBACK_THREAD_PRIORITY = 2
queue = queue.Queue()
semaphore = threading.Semaphore(value=0)


# what are modes 267-273? frequency? these are undocumented
@wlmData.CALLBACK_EX_TYPE
def cb(ver, mode, intval, dblval, res1):
    # print("callback: ", mode, intval, dblval, res1, flush=True)
    logger.debug("callback: %d %d %f %d", mode, intval, dblval, res1)
    queue.put((ver, mode, intval, dblval, res1))
    semaphore.release()


class WavelengthMeter:
    """Read-only interface to HighFinesse Wavelength Meter"""
    def __init__(self, loop=None):
        self.id = None
        self.active_channel = None
        self.data = {}

        try:
            self.dll = wlmData.LoadDLL()
            #dll = wlmData.LoadDLL('/path/to/your/libwlmData.so')
        except OSError as err:
            sys.exit(f'{err}\nPlease check if the wlmData DLL is installed correctly!')

        # Check the number of WLM server instances
        if self.dll.GetWLMCount(0) == 0:
            sys.exit('There is no running WLM server instance.')

        # Install callback function
        self.dll.Instantiate(wlmConst.cInstNotification, wlmConst.cNotifyInstallCallbackEx, cb,
            CALLBACK_THREAD_PRIORITY)

        self._consumer_thread = threading.Thread(target=self._consumer)
        self._consumer_thread.start()

    def close(self):
        """Close wavelength meter server"""
        # Remove callback function
        self.dll.Instantiate(wlmConst.cInstNotification, wlmConst.cNotifyRemoveCallback, None, 0)

        semaphore.release()
        queue.join()
        self._consumer_thread.join()

    def ping(self):
        # HACK
        return True

    def _consumer(self):
        # while True:
        while semaphore.acquire():
            if queue.empty():
                break
            self.id, mode, intval, dblval, res1 = queue.get()

            # print("consumer: ", mode, intval, dblval, res1, flush=True)
            logger.debug("consumer: %d %d %f %d", mode, intval, dblval, res1)

            if mode == wlmConst.cmiSwitcherChannel:
                self.data[mode] = (res1, intval)
            else:
                self.data[mode] = (intval, dblval)
            queue.task_done()

    def get_all(self):
        """Get all latest updates.

        Returns a dictionary of tuples indexed by mode constant.
        """
        return self.data

    def get_by_mode(self, mode):
        """Get latest update by mode constant.

        Mode constants are defined in HighFinesse documentation.
        Return value is a tuple of (integer, float), as described
        in the documentation for CallbackProcEx, except for the
        special case of cmiSwitcherChannel; see
        `get_switcher_channel`.
        """
        return self.data.get(mode, (0, 0.0))

    def get_pressure(self):
        """Get air pressure.

        Returns tuple of (timestamp, pressure).
        """
        return self.get_by_mode(wlmConst.cmiPressure)

    def get_temperature(self):
        """Get temperature.

        Returns tuple of (timestamp, temperature).
        """
        return self.get_by_mode(wlmConst.cmiTemperature)

    def get_switcher_channel(self):
        """Get active switcher channel.

        Returns tuple of (timestamp, channel).
        """
        return self.get_by_mode(wlmConst.cmiSwitcherChannel)

    def get_wavelength(self, channel):
        """Get wavelength in nm.

        Returns tuple of (timestamp, wavelength).
        """
        modes = {
            1: wlmConst.cmiWavelength1,
            2: wlmConst.cmiWavelength2,
            3: wlmConst.cmiWavelength3,
            4: wlmConst.cmiWavelength4,
            5: wlmConst.cmiWavelength5,
            6: wlmConst.cmiWavelength6,
            7: wlmConst.cmiWavelength7,
            8: wlmConst.cmiWavelength8,
        }
        return self.get_by_mode(modes[channel])

    def get_frequency(self, channel):
        """Get frequency in Hz.

        Returns tuple of (timestamp, frequency).
        """
        c = 299792458.0
        ts, wl = self.get_wavelength(channel)
        if wl > 0:
            return (ts, c / (1e-9 * wl))
        else:
            return (ts, wl)
