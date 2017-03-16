import json
import sys
import base64

from warcio.warcwriter import BufferWARCWriter, WARCWriter
from warcio.statusandheaders import StatusAndHeaders

from six.moves.urllib.parse import urlsplit, urlencode
from io import BytesIO

from argparse import ArgumentParser, RawTextHelpFormatter


# ============================================================================
class HarParser(object):
    def __init__(self, obj, writer):
        if isinstance(obj, str):
            with open(obj, 'rt') as fh:
                self.har = json.loads(fh.read())
        elif hasattr(obj, 'read'):
            self.har = json.loads(obj.read())
        elif isinstance(obj, dict):
            self.har = obj
        else:
            raise Exception('obj is an unknown format')

        self.writer = writer

    def parse(self):
        for entry in self.har['log']['entries']:

            url = entry['request']['url']

            response = self.handle_response(url, entry['response'])
            if not response:
                continue

            #TODO: support WARC/1.1 arbitrary precision dates!
            warc_date = entry['startedDateTime'][:19] + 'Z'

            response.rec_headers.replace_header('WARC-Date', warc_date)

            request = self.handle_request(entry['request'])

            self.writer.write_request_response_pair(request, response)

    def _get_http_version(self, entry, default='HTTP/1.0'):
        http_version = entry.get('httpVersion', default)
        if http_version == 'unknown':
            http_version = default

        return http_version

    def handle_response(self, url, response):
        #print(response['headers'])

        payload = BytesIO()
        content = response['content'].get('text')
        if not content:
            return

        if response['content'].get('encoding') == 'base64':
            payload.write(base64.b64decode(content))
            is_bin = True
        else:
            payload.write(content.encode('utf-8'))
            is_bin = False

        length = payload.tell()
        payload.seek(0)

        def skip(name):
            if name == 'transfer-encoding':
                return True

            if not is_bin and name == 'content-encoding':
                return True

            return False

        headers = [(header['name'], header['value'])
                   for header in response['headers']
                    if not skip(header['name'])]

        status_line = str(response.get('status', '404'))
        status_line += ' ' + response.get('statusText', 'unknown')

        proto = self._get_http_version(response)

        http_headers = StatusAndHeaders(status_line, headers, protocol=proto)

        record = self.writer.create_warc_record(url, 'response',
                                                http_headers=http_headers,
                                                payload=payload,
                                                length=length)

        return record

    def handle_request(self, request):
        parts = urlsplit(request['url'])

        path = parts.path
        query = request.get('queryString')
        if query:
            path += '?' + urlencode(dict((p['name'], p['value'])
                                    for p in query))

        headers = [(header['name'], header['value'])
                    for header in request['headers']]

        headers.append(('Host', parts.netloc))

        http_version = self._get_http_version(request)

        status_line = request['method'] + ' ' + path + ' ' + http_version
        http_headers = StatusAndHeaders(status_line, headers)

        record = self.writer.create_warc_record(request['url'], 'request',
                                                http_headers=http_headers,
                                                payload=None,
                                                length=0)

        return record




def main(args=None):
    parser = ArgumentParser(description='warcio utils',
                            formatter_class=RawTextHelpFormatter)

    parser.add_argument('input')
    parser.add_argument('output')

    cmd = parser.parse_args(args=args)

    with open(cmd.output, 'wb') as fh:
        writer = WARCWriter(fh)
        HarParser(cmd.input, writer).parse()


main()
