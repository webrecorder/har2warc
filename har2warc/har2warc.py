import json
import sys
import base64
import logging
import codecs

from warcio.warcwriter import BufferWARCWriter, WARCWriter
from warcio.statusandheaders import StatusAndHeaders
from warcio.timeutils import iso_date_to_timestamp

from six.moves.urllib.parse import urlsplit, urlencode
from io import BytesIO

from collections import OrderedDict

from argparse import ArgumentParser, RawTextHelpFormatter

from http_status import name as http_status_names

from . import __version__


# ============================================================================
class HarParser(object):
    logger = logging.getLogger(__name__)

    def __init__(self, obj, writer):
        if isinstance(obj, str):
            with codecs.open(obj, encoding='utf-8') as fh:
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
            self.parse_entry(entry)

    def parse_entry(self, entry):
        url = entry['request']['url']

        response = self.parse_response(url,
                                        entry['response'],
                                        entry.get('serverIPAddress'))

        #TODO: support WARC/1.1 arbitrary precision dates!
        warc_date = entry['startedDateTime'][:19] + 'Z'

        response.rec_headers.replace_header('WARC-Date', warc_date)

        request = self.parse_request(entry['request'])

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
                    "type": "recording",
                   }

        if pagelist:
            metadata["pages"] = pagelist

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

    def _get_http_version(self, entry):
        http_version = entry.get('httpVersion')
        if not http_version or http_version.upper() not in ('HTTP/1.1', 'HTTP/1.0'):
            http_version = 'HTTP/1.1'

        return http_version

    def parse_response(self, url, response, ip=None):
        headers = []
        payload = BytesIO()
        content = response['content'].get('text', '')

        if not content and not response.get('headers'):
            self.logger.info('No headers or payload for: {0}'.format(url))
            headers.append(('Content-Length', '0'))
        if response['content'].get('encoding') == 'base64':
            payload.write(base64.b64decode(content))
        else:
            payload.write(content.encode('utf-8'))

        length = payload.tell()
        payload.seek(0)

        SKIP_HEADERS = ('content-encoding', 'transfer-encoding')

        http2 = False

        for header in response['headers']:
            if header['name'].lower() not in SKIP_HEADERS:
                headers.append((header['name'], header['value']))

            #TODO: http2 detection -- write as same warc header?
            if (not http2 and
                header['name'] in (':method', ':scheme', ':path')):
                http2 = True

        status = response.get('status') or 204

        reason = response.get('statusText')
        if not reason:
            reason = http_status_names.get(status, 'No Reason')

        status_line = str(status) + ' ' + reason

        proto = self._get_http_version(response)

        http_headers = StatusAndHeaders(status_line, headers, protocol=proto)

        if not content:
            content_length = http_headers.get_header('Content-Length', '0')
            if content_length != '0':
                self.logger.info('No Content for length {0} {1}'.format(content_length, url))
                http_headers.replace_header('Content-Length', '0')
        else:
            http_headers.replace_header('Content-Length', str(length))

        warc_headers_dict = {}
        if ip:
            warc_headers_dict['WARC-IP-Address'] = ip

        record = self.writer.create_warc_record(url, 'response',
                                                http_headers=http_headers,
                                                payload=payload,
                                                length=length,
                                                warc_headers_dict=warc_headers_dict)

        return record

    def parse_request(self, request):
        parts = urlsplit(request['url'])

        path = parts.path
        query = request.get('queryString')
        if query:
            path += '?' + urlencode(dict((p['name'], p['value'])
                                    for p in query))

        headers = []
        http2 = False

        for header in request['headers']:
            headers.append((header['name'], header['value']))

            #TODO: http2 detection -- write as same warc header?
            if (not http2 and
                header['name'] in (':method', ':scheme', ':path')):
                http2 = True

        if http2:
            headers.append(('Host', parts.netloc))

        http_version = self._get_http_version(request)

        status_line = request['method'] + ' ' + path + ' ' + http_version
        http_headers = StatusAndHeaders(status_line, headers)

        payload = None
        length = 0

        if request['bodySize'] > 0:
            payload = BytesIO()
            payload.write(request['postData']['text'].encode('utf-8'))
            length = payload.tell()
            payload.seek(0)

        record = self.writer.create_warc_record(request['url'], 'request',
                                                http_headers=http_headers,
                                                payload=payload,
                                                length=length)

        return record


# ============================================================================
def main(args=None):
    parser = ArgumentParser(description='HAR to WARC Converter',
                            formatter_class=RawTextHelpFormatter)

    parser.add_argument('input')
    parser.add_argument('output')

    parser.add_argument('--title')
    parser.add_argument('--no-z', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')

    r = parser.parse_args(args=args)

    rec_title = r.title or r.input.rsplit('/', 1)[-1]

    logging.basicConfig(format='[%(levelname)s]: %(message)s')
    HarParser.logger.setLevel(logging.ERROR if not r.verbose else logging.INFO)

    with open(r.output, 'wb') as fh:
        writer = WARCWriter(fh, gzip=not r.no_z)
        HarParser(r.input, writer).parse(r.output, rec_title)


if __name__ == "__main__":  #pragma: no cover
    main()
