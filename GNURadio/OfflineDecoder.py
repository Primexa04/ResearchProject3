#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: satnogs_fsk_ax25
# Author: Manolis Surligas (surligas@gmail.com)
# Description: Generic FSK/MSK decoder supporting AX.25 framing schemes
# GNU Radio version: 3.10.5.1

from gnuradio import analog
import math
from gnuradio import blocks
import pmt
from gnuradio import digital
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import gnuradio.satnogs as satnogs
import satellites
import satellites.components.datasinks




class satnogs_fsk_ax25(gr.top_block):

    def __init__(self, antenna="", baudrate=9600, bw=0.0, gain=0.0, gain_mode="Overall", lo_offset=200e3, ppm=0, rx_freq=600632500, samp_rate_rx=0.0):
        gr.top_block.__init__(self, "satnogs_fsk_ax25", catch_exceptions=True)

        ##################################################
        # Parameters
        ##################################################
        self.antenna = antenna
        self.baudrate = baudrate
        self.bw = bw
        self.gain = gain
        self.gain_mode = gain_mode
        self.lo_offset = lo_offset
        self.ppm = ppm
        self.rx_freq = rx_freq
        self.samp_rate_rx = samp_rate_rx

        ##################################################
        # Variables
        ##################################################
        self.variable_ax25_decoder_0 = variable_ax25_decoder_0 = satnogs.ax25_decoder('HS0AK', 11, True, True, 1024, True)
        self.decimation = decimation = 8

        ##################################################
        # Blocks
        ##################################################

        self.satnogs_waterfall_sink_0 = satnogs.waterfall_sink((baudrate*decimation), 0.0, 10, 1024, '/tmp/freqCorrected.dat', 1)
        self.satnogs_frame_decoder_0_0 = satnogs.frame_decoder(variable_ax25_decoder_0, 1 * 1)
        self.satellites_kiss_server_sink_0 = satellites.components.datasinks.kiss_server_sink("0.0.0.0", 8102, options="")
        self.satellites_check_address_0 = satellites.check_address('HS0K', "from", '')
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=76800,
                decimation=78125,
                taps=[],
                fractional_bw=0)
        self.low_pass_filter_0_0 = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                (baudrate*decimation),
                (baudrate*1.25),
                (baudrate / 2.0),
                window.WIN_HAMMING,
                6.76))
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            (decimation // 2),
            firdes.low_pass(
                1,
                (baudrate*decimation),
                (0.625* baudrate),
                (baudrate / 8.0),
                window.WIN_HAMMING,
                6.76))
        self.digital_clock_recovery_mm_xx_0 = digital.clock_recovery_mm_ff(2, (2 * math.pi / 100), 0.5, (0.5/8.0), 0.01)
        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        self.dc_blocker_xx_0 = filter.dc_blocker_ff(1024, True)
        self.blocks_vco_c_0 = blocks.vco_c((baudrate*decimation), (-baudrate*decimation), 1.0)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(1024, (1.0/1024.0), 4096, 1)
        self.blocks_message_debug_0 = blocks.message_debug(True)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, '/tmp/KNACKSAT2_2026-02-27T05_17_00Doppler_FIRcf32.raw', False, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_gr_complex*1, (1024//2))
        self.analog_quadrature_demod_cf_0_0_0_0 = analog.quadrature_demod_cf(1.0)
        self.analog_quadrature_demod_cf_0_0 = analog.quadrature_demod_cf(1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.satellites_check_address_0, 'ok'), (self.blocks_message_debug_0, 'print'))
        self.msg_connect((self.satnogs_frame_decoder_0_0, 'out'), (self.satellites_check_address_0, 'in'))
        self.msg_connect((self.satnogs_frame_decoder_0_0, 'out'), (self.satellites_kiss_server_sink_0, 'in'))
        self.connect((self.analog_quadrature_demod_cf_0_0, 0), (self.dc_blocker_xx_0, 0))
        self.connect((self.analog_quadrature_demod_cf_0_0_0_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_delay_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_file_source_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_vco_c_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.satnogs_waterfall_sink_0, 0))
        self.connect((self.blocks_vco_c_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.dc_blocker_xx_0, 0), (self.digital_clock_recovery_mm_xx_0, 0))
        self.connect((self.digital_binary_slicer_fb_0, 0), (self.satnogs_frame_decoder_0_0, 0))
        self.connect((self.digital_clock_recovery_mm_xx_0, 0), (self.digital_binary_slicer_fb_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.analog_quadrature_demod_cf_0_0, 0))
        self.connect((self.low_pass_filter_0_0, 0), (self.analog_quadrature_demod_cf_0_0_0_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_delay_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.low_pass_filter_0_0, 0))


    def get_antenna(self):
        return self.antenna

    def set_antenna(self, antenna):
        self.antenna = antenna

    def get_baudrate(self):
        return self.baudrate

    def set_baudrate(self, baudrate):
        self.baudrate = baudrate
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, (self.baudrate*self.decimation), (0.625* self.baudrate), (self.baudrate / 8.0), window.WIN_HAMMING, 6.76))
        self.low_pass_filter_0_0.set_taps(firdes.low_pass(1, (self.baudrate*self.decimation), (self.baudrate*1.25), (self.baudrate / 2.0), window.WIN_HAMMING, 6.76))

    def get_bw(self):
        return self.bw

    def set_bw(self, bw):
        self.bw = bw

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain

    def get_gain_mode(self):
        return self.gain_mode

    def set_gain_mode(self, gain_mode):
        self.gain_mode = gain_mode

    def get_lo_offset(self):
        return self.lo_offset

    def set_lo_offset(self, lo_offset):
        self.lo_offset = lo_offset

    def get_ppm(self):
        return self.ppm

    def set_ppm(self, ppm):
        self.ppm = ppm

    def get_rx_freq(self):
        return self.rx_freq

    def set_rx_freq(self, rx_freq):
        self.rx_freq = rx_freq

    def get_samp_rate_rx(self):
        return self.samp_rate_rx

    def set_samp_rate_rx(self, samp_rate_rx):
        self.samp_rate_rx = samp_rate_rx

    def get_variable_ax25_decoder_0(self):
        return self.variable_ax25_decoder_0

    def set_variable_ax25_decoder_0(self, variable_ax25_decoder_0):
        self.variable_ax25_decoder_0 = variable_ax25_decoder_0

    def get_decimation(self):
        return self.decimation

    def set_decimation(self, decimation):
        self.decimation = decimation
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, (self.baudrate*self.decimation), (0.625* self.baudrate), (self.baudrate / 8.0), window.WIN_HAMMING, 6.76))
        self.low_pass_filter_0_0.set_taps(firdes.low_pass(1, (self.baudrate*self.decimation), (self.baudrate*1.25), (self.baudrate / 2.0), window.WIN_HAMMING, 6.76))



def argument_parser():
    description = 'Generic FSK/MSK decoder supporting AX.25 framing schemes'
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--antenna", dest="antenna", type=str, default="",
        help="Set antenna [default=%(default)r]")
    parser.add_argument(
        "--baudrate", dest="baudrate", type=eng_float, default=eng_notation.num_to_str(float(9600)),
        help="Set baudrate [default=%(default)r]")
    parser.add_argument(
        "--bw", dest="bw", type=eng_float, default=eng_notation.num_to_str(float(0.0)),
        help="Set Bandwidth [default=%(default)r]")
    parser.add_argument(
        "--gain", dest="gain", type=eng_float, default=eng_notation.num_to_str(float(0.0)),
        help="Set gain [default=%(default)r]")
    parser.add_argument(
        "--gain-mode", dest="gain_mode", type=str, default="Overall",
        help="Set gain_mode [default=%(default)r]")
    parser.add_argument(
        "--lo-offset", dest="lo_offset", type=eng_float, default=eng_notation.num_to_str(float(200e3)),
        help="Set lo_offset [default=%(default)r]")
    parser.add_argument(
        "--ppm", dest="ppm", type=eng_float, default=eng_notation.num_to_str(float(0)),
        help="Set ppm [default=%(default)r]")
    parser.add_argument(
        "--rx-freq", dest="rx_freq", type=eng_float, default=eng_notation.num_to_str(float(600632500)),
        help="Set rx_freq [default=%(default)r]")
    parser.add_argument(
        "--samp-rate-rx", dest="samp_rate_rx", type=eng_float, default=eng_notation.num_to_str(float(0.0)),
        help="Set Device Sampling rate [default=%(default)r]")
    return parser


def main(top_block_cls=satnogs_fsk_ax25, options=None):
    if options is None:
        options = argument_parser().parse_args()
    tb = top_block_cls(antenna=options.antenna, baudrate=options.baudrate, bw=options.bw, gain=options.gain, gain_mode=options.gain_mode, lo_offset=options.lo_offset, ppm=options.ppm, rx_freq=options.rx_freq, samp_rate_rx=options.samp_rate_rx)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
