import json
import os
import pickle
import re
import tempfile
import time
import uuid

import markdown
import requests
from bs4 import BeautifulSoup
from norn import util
from norn import flags


class EventList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

        for i in range(len(self)):
            setattr(self, f"_{i + 1}", self[i])


class CloudWatchEvents:
    def __init__(self, **kwargs):
        self.account = kwargs.get("account")
        self.event_region = kwargs.get("region")
        flags.debug = kwargs.get("debug")

        self.events = self.get_events()
        self.services = []

        self._create_events()

    def get_events(self):
        event_fpath = f"{tempfile.gettempdir()}/cwet.{uuid.getnode()}"

        try:
            file_state = os.stat(event_fpath)
        except FileNotFoundError:
            file_state = None
            event_file = open(event_fpath, "wb")

        if (
            file_state
            and (int(round(time.time() * 1000)) - int(file_state.st_mtime * 1000))
            > 604800000
        ):
            fetch_events = True
            event_file = open(event_fpath, "wb")
        elif not file_state:
            fetch_events = True
        elif self.account or self.event_region:
            fetch_events = True
            event_file = open(event_fpath, "wb")
        else:
            event_file = open(event_fpath, "rb")
            cloudwatch_events = pickle.load(event_file)
            event_file.close()
            fetch_events = False

        if flags.debug: 
            fetch_events = True
            event_file = open(event_fpath, "wb")

        if fetch_events:
            cloudwatch_events = {"events": {}}
            cw_events_urls = [
                "https://raw.githubusercontent.com/awsdocs/amazon-cloudwatch-events-user-guide/master/doc_source/EventTypes.md",
                "https://raw.githubusercontent.com/awsdocs/aws-batch-user-guide/master/doc_source/batch_cwe_events.md",
                "https://raw.githubusercontent.com/awsdocs/aws-codebuild-user-guide/master/doc_source/sample-build-notifications.md",
                "https://raw.githubusercontent.com/awsdocs/aws-config-developer-guide/master/doc_source/monitor-config-with-cloudwatchevents.md",
                "https://raw.githubusercontent.com/awsdocs/amazon-ec2-user-guide/master/doc_source/ebs-cloud-watch-events.md",
                "https://raw.githubusercontent.com/awsdocs/amazon-ec2-auto-scaling-user-guide/master/doc_source/cloud-watch-events.md",
                "https://raw.githubusercontent.com/awsdocs/amazon-ec2-user-guide/master/doc_source/spot-interruptions.md",
                "https://raw.githubusercontent.com/awsdocs/amazon-ecs-developer-guide/master/doc_source/ecs_cwe_events.md",
                "https://raw.githubusercontent.com/awsdocs/amazon-ecr-user-guide/master/doc_source/ecr-eventbridge.md",
                "https://raw.githubusercontent.com/awsdocs/aws-elemental-mediastore-user-guide/master/doc_source/monitoring-cloudwatch-events-object-state-change.md",
                "https://raw.githubusercontent.com/awsdocs/aws-elemental-mediastore-user-guide/master/doc_source/monitoring-cloudwatch-events-container-state-change.md",
                "https://raw.githubusercontent.com/awsdocs/aws-elemental-mediapackage-user-guide/master/doc_source/cloudwatch-events-example.md",
                "https://raw.githubusercontent.com/awsdocs/amazon-guardduty-user-guide/master/doc_source/guardduty_findings_cloudwatch.md",
                "https://raw.githubusercontent.com/awsdocs/aws-security-hub-user-guide/master/doc_source/securityhub-cloudwatch-events.md",
                "https://raw.githubusercontent.com/awsdocs/aws-step-functions-developer-guide/master/doc_source/cw-events.md",
                "https://raw.githubusercontent.com/awsdocs/aws-step-functions-developer-guide/master/doc_source/cw-events.md",
            ]

            patterns = []
            if self.account:
                patterns.append((re.compile(r'(?<=:|")[0-9]{12}(?=:|")'), self.account))

            if self.event_region:
                patterns.append(
                    (
                        re.compile(
                            r"(us(-gov)?|ap|ca|cn|eu|sa)-(central|(north|south)?(east|west)?)-\d"
                        ),
                        self.event_region,
                    )
                )

            sess = requests.Session()
            for url in cw_events_urls:
                raw_data = sess.get(url).text

                md = markdown.Markdown()
                html_data = md.convert(raw_data)

                soup = BeautifulSoup(html_data, features="html.parser")

                for code_block in soup.findAll("code"):
                    parsed_data = code_block.text.replace("”", '"')
                    parsed_data = code_block.text.replace("...", "")
                    for p in patterns:
                        parsed_data = p[0].sub(p[1], parsed_data)

                    try:
                        event_data = json.loads(parsed_data)
                    except ValueError as e:
                        event_data = util.fix_json(e, parsed_data, url)
                    try:
                        if (
                            "source" in event_data.keys()
                            and type(event_data["source"]) is not list
                        ):
                            if (
                                event_data["source"]
                                not in cloudwatch_events["events"].keys()
                            ):
                                cloudwatch_events["events"][
                                    event_data["source"]
                                ] = []
                            cloudwatch_events["events"][
                                event_data["source"]
                            ].append(event_data)
                    except AttributeError as e:
                        continue

            pickle.dump(cloudwatch_events, event_file)
            event_file.close()

        return cloudwatch_events

    def _create_events(self):
        events = self.events
        ebs_events = EventList()

        self.services.append("ebs")
        for svc in events["events"].keys():
            svc_name = svc.replace("aws.", "")
            self.services.append(svc_name)

            for evn in events["events"][svc]:
                if "EBS" in evn["detail-type"]:
                    ebs_events.append(evn)

            event_conv = EventList(events["events"][svc])
            setattr(self, "ebs", ebs_events)
            setattr(self, svc_name, event_conv)

        self.ec2[:] = [
            ebs_event for ebs_event in self.ec2 if "EBS" not in ebs_event["detail-type"]
        ]

        self.services.sort()
