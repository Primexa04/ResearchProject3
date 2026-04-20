from gnuradio import blocks, gr
import signal
import sys
import gnuradio.satnogs as satnogs


class tb(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, 'ax25_direct_bits_test', catch_exceptions=True)

        self.src = blocks.file_source(
            gr.sizeof_char,
            '/tmp/Knacksat2_13753740_tx_bits_u8.bin',
            False
        )

        self.throttle = blocks.throttle(gr.sizeof_char, 5000, True)

        self.dec = satnogs.frame_decoder(
            satnogs.ax25_decoder('HS0AK', 11, True, True, 1024, True),
            1 * 1
        )

        self.dbg = blocks.message_debug(True)

        self.msg_connect((self.dec, 'out'), (self.dbg, 'print'))
        self.connect((self.src, 0), (self.throttle, 0))
        self.connect((self.throttle, 0), (self.dec, 0))


def main():
    t = tb()

    def sig_handler(sig=None, frame=None):
        t.stop()
        t.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    t.start(128)
    t.wait()


if __name__ == '__main__':
    main()
