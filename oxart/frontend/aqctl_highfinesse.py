#!/usr/bin/env python3
import argparse

import sipyco.common_args as sca
from sipyco.pc_rpc import simple_server_loop
from oxart.devices.highfinesse.driver import WavelengthMeter


def get_argparser():
    parser = argparse.ArgumentParser(
        description="ARTIQ controller for HighFinesse wavemeter (simplified)")
    sca.simple_network_args(parser, 4400)
    sca.verbosity_args(parser)

    return parser


def main():
    args = get_argparser().parse_args()
    sca.init_logger_from_args(args)
    dev = WavelengthMeter()

    try:
        simple_server_loop({"HighFinesse WLM": dev}, sca.bind_address_from_args(args), args.port)
    finally:
        dev.close()


if __name__ == "__main__":
    main()
