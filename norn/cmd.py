import argparse
import sys
from pprint import pprint
import json
import os
from urllib.parse import urlparse

from norn import events
from norn import test


def main():
    argv = sys.argv[1:]

    parser = argparse.ArgumentParser(usage=("%(prog)s"))

    subparsers = parser.add_subparsers()

    # list services
    service_parser = subparsers.add_parser(
        "services", description="Supported services."
    )
    service_parser.set_defaults(func=services)

    # events
    events_parser = subparsers.add_parser("events", description="Events for a service")
    events_parser.add_argument(
        "--service",
        "-s",
        dest="service_name",
        type=str,
        default=None,
        required=True,
        help="Select a service",
    )

    events_parser.add_argument(
        "--account",
        "-a",
        dest="account",
        type=str,
        default=None,
        help="AWS account ID to pre-populate event samples.",
    )

    events_parser.add_argument(
        "--region",
        "-r",
        dest="event_region",
        type=str,
        default=None,
        help="AWS region to pre-populate event samples.",
    )

    events_parser.set_defaults(func=get_events)

    # test
    test_parser = subparsers.add_parser("test", description="Test with CloudWatch events")
    test_parser.add_argument(
        "--event",
        "-e",
        dest="event",
        type=str,
        default=None,
        required=True,
        help="Event to test against",
    )

    test_parser.add_argument(
        "--pattern",
        "-p",
        dest="pattern",
        type=str,
        default=None,
        help="AWS region to pre-populate event samples.",
    )

    test_parser.set_defaults(func=test_pattern)

    # trigger
    trigger_parser = subparsers.add_parser("trigger", description="Trigger lambda functions with test events")
    trigger_parser.add_argument(
        "--event",
        "-e",
        dest="event",
        type=str,
        default=None,
        required=True,
        help="Event to test against",
    )

    trigger_parser.add_argument(
        "--function_name",
        "-n",
        dest="function_name",
        type=str,
        default=None,
        help="Name of the lambda function to trigger.",
    )

    trigger_parser.set_defaults(func=trigger_f)

    args = parser.parse_args(argv)
    args.func(**vars(args))


def services(**kwargs):
    svc = events.CloudWatchEvents()

    for i, service in enumerate(svc.services, 1):
        print(f"\t{i:>3}   {service}")


def get_events(**kwargs):
    service_name = kwargs.get("service_name")
    account = kwargs.get("account")
    event_region = kwargs.get("event_region")
    cwe = events.CloudWatchEvents(account=account, region=event_region)

    try:
        idx = int(service_name.split('.')[1]) - 1
    except IndexError:
        idx = None

    ret_func = getattr(cwe, service_name.split('.')[0])
    if idx or idx == 0:
        pprint(ret_func[idx])
    else:
        pprint(ret_func)

def test_pattern(**kwargs):
    tester = test.CWEventTest()

    test_events = events.CloudWatchEvents()

    sample_event = kwargs.get("event")

    pattern = kwargs.get("pattern")
    parsed_pattern = None
    final_path = None

    if pattern:
        try:
            parsed_pattern = json.loads(pattern)
        except json.decoder.JSONDecodeError:
            p = urlparse(pattern)
            final_path = os.path.abspath(os.path.join(p.netloc, p.path))

    if parsed_pattern:
        tester.load_pattern(s_pattern=parsed_pattern)
    elif final_path:
        tester.load_pattern(file=final_path)

    try:
        idx = int(sample_event.split('.')[1]) - 1
    except IndexError:
        idx = 0

    ret_func = getattr(test_events, sample_event.split('.')[0])

    pattern_result = tester.test_pattern(ret_func[idx])

    print(pattern_result)

def trigger_f(**kwargs):
    test_events = events.CloudWatchEvents()

    sample_event = kwargs.get("event")
    function_name = kwargs.get("function_name")

    try:
        idx = int(sample_event.split('.')[1]) - 1
    except IndexError:
        idx = 0

    ret_func = getattr(test_events, sample_event.split('.')[0])

    resp = test.CWEventTest.trigger_lambda(function_name, ret_func[idx])

    pprint(resp)


if __name__ == "__main__":
    main()
