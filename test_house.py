"""Disabled legacy writer.

Historical source is in offline_reference and is not a runtime entry.
This module performs no Tapir call.
"""


def main():
    raise SystemExit('test_house is disabled: direct Tapir writes are refused')


if __name__ == '__main__':
    main()
