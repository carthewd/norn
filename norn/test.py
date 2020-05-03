import sys
import json
import boto3


class CWEventTest():
    def __init__(self):
        self.pattern = None

    def load_pattern(self, file=None, s_pattern=None):
        if file:
            with open(file) as fh:
                self.pattern = json.load(fh)
        elif s_pattern:
            self.pattern = s_pattern
        else:
            buf = ''
            print('Enter event pattern --> ')
            while True:
                pattern = sys.stdin.readline().rstrip('\n')

                if pattern == '.':
                    break
                else:
                    buf += pattern

            self.pattern = json.loads(buf)

    def test_pattern(self, test_event):
        aws_client = boto3.client('events')

        response = aws_client.test_event_pattern(
            EventPattern=json.dumps(self.pattern),
            Event=json.dumps(test_event)
        )

        return response['Result']

    @staticmethod
    def trigger_lambda(function_name, test_event, invoke_type='RequestResponse', alias=None):
        aws_client = boto3.client('lambda')

        response = aws_client.invoke(
            FunctionName=function_name,
            InvocationType=invoke_type,
            LogType='Tail',
            Payload=json.dumps(test_event).encode()
            # Qualifier=alias
        )

        return response
