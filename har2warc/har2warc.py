import json
import sys
import base64

from warcio.warcwriter import BufferWARCWriter, WARCWriter
from warcio.statusandheaders import StatusAndHeaders
from warcio.timeutils import iso_date_to_timestamp

from six.moves.urllib.parse import urlsplit, urlencode
from io import BytesIO

from collections import OrderedDict

from argparse import ArgumentParser, RawTextHelpFormatter

from har2warc import __version__


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

    def parse(self, out_filename='har.warc.gz', rec_title='HAR Recording'):
        metadata = self.create_wr_metadata(self.har['log'], rec_title)
        self.write_warc_info(self.har['log'], out_filename, metadata)

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

    def create_wr_metadata(self, log, rec_title):
        pagelist = []

        for page in log['pages']:
            if not page['title'].startswith(('http:', 'https:')):
                continue

            pagelist.append(dict(title=page['title'],
                                 url=page['title'],
                                 timestamp=iso_date_to_timestamp(page['startedDateTime'])))

        metadata = {"title": rec_title,
                    #"created_at": timestamp_now(),
                    "type": "recording",
                    "pages": pagelist,
                   }

        return metadata

    def write_warc_info(self, log, filename, metadata):
        creator = '{0} {1}'.format(log['creator']['name'],
                                   log['creator']['version'])

        source = 'HAR Format {0}'.format(log['version'])

        software = 'har2warc ' + str(__version__)

        params = OrderedDict([('software', software),
                              ('creator', creator),
                              ('source', source),
                              ('format', 'WARC File Format 1.0'),
                              ('json-metadata', json.dumps(metadata))])

        record = self.writer.create_warcinfo_record(filename, params)
        self.writer.write_record(record)

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
    parser = ArgumentParser(description='HAR to WARC Converter',
                            formatter_class=RawTextHelpFormatter)

    parser.add_argument('input')
    parser.add_argument('output')

    parser.add_argument('--title')
    parser.add_argument('--no-z', action='store_true')

    r = parser.parse_args(args=args)

    rec_title = r.title or r.input.rsplit('/', 1)[-1]

    with open(r.output, 'wb') as fh:
        writer = WARCWriter(fh, gzip=not r.no_z)
        HarParser(r.input, writer).parse(r.output, rec_title)


main()
