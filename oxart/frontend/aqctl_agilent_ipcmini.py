#!/usr/bin/env python3

import argparse
import logging

import sipyco.common_args as sca
from sipyco.pc_rpc import simple_server_loop
from oxart.devices.ipcmini.driver import IPCMini


def get_argparser():
    parser = argparse.ArgumentParser(
        description="ARTIQ controller for Agilent IPCMini")
    parser.add_argument("-d", "--device", help="IP address of device")
    sca.simple_network_args(parser, 4311)
    sca.verbosity_args(parser)

    return parser


def main():
    args = get_argparser().parse_args()
    sca.init_logger_from_args(args)
    dev = IPCMini(args.device)

    try:
        simple_server_loop({f"IPCMini {dev.get_label()}": dev}, sca.bind_address_from_args(args), args.port)
    finally:
        dev.close()


if __name__ == "__main__":
    main()
