from har2warc.har2warc import main
from warcio.cli import main as indexer
from warcio import ArchiveIterator
import tempfile
import os
import sys

from contextlib import contextmanager
from io import BytesIO


class TestHar2WARC(object):
    @classmethod
    def get_test_file(cls, filename):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)

    def load_har(self, filename):
        filename = self.get_test_file(filename)

        temp_filename = os.path.join(tempfile.gettempdir(), tempfile.gettempprefix() + '-' + os.path.basename(filename))

        try:
            main([filename, temp_filename])

            with patch_stdout() as buff:
                indexer(['index', temp_filename, '-f', 'warc-target-uri'])

                return buff.getvalue().decode('utf-8')
        finally:
            os.remove(temp_filename)

    def test_example_har(self):
        assert self.load_har('example.har') == EXAMPLE_INDEX

    def test_http2_har(self):
        assert self.load_har('http2.github.io.har').startswith(HTTP2_INDEX)

    def test_load_http2_warc_convert_protocol(self):
        filename = self.get_test_file('http2.github.io.har')

        temp_filename = os.path.join(tempfile.gettempdir(), tempfile.gettempprefix() + '-http2.warc')

        try:
            main([filename, temp_filename])

            with open(temp_filename, 'rb') as fh:
                ai = ArchiveIterator(fh, verify_http=True)

                record = next(ai)
                assert record.rec_type == 'warcinfo'

                record = next(ai)
                assert record.rec_type == 'response'

                # ensure protocol vonerted to HTTP/1.1
                assert record.http_headers.protocol == 'HTTP/1.1'

        finally:
            os.remove(temp_filename)



EXAMPLE_INDEX = """\
{}
{"warc-target-uri": "http://example.com/"}
{"warc-target-uri": "http://example.com/"}
{"warc-target-uri": "https://www.iana.org/domains/reserved"}
{"warc-target-uri": "https://www.iana.org/domains/reserved"}
{"warc-target-uri": "http://www.iana.org/domains/example"}
{"warc-target-uri": "http://www.iana.org/domains/example"}
{"warc-target-uri": "https://www.iana.org/domains/example"}
{"warc-target-uri": "https://www.iana.org/domains/example"}
{"warc-target-uri": "https://www.iana.org/_css/2015.1/screen.css"}
{"warc-target-uri": "https://www.iana.org/_css/2015.1/screen.css"}
{"warc-target-uri": "https://www.iana.org/_js/2013.1/jquery.js"}
{"warc-target-uri": "https://www.iana.org/_js/2013.1/jquery.js"}
{"warc-target-uri": "https://www.iana.org/_js/2013.1/iana.js"}
{"warc-target-uri": "https://www.iana.org/_js/2013.1/iana.js"}
{"warc-target-uri": "https://www.iana.org/_img/2013.1/iana-logo-header.svg"}
{"warc-target-uri": "https://www.iana.org/_img/2013.1/iana-logo-header.svg"}
{"warc-target-uri": "https://www.iana.org/_css/2015.1/print.css"}
{"warc-target-uri": "https://www.iana.org/_css/2015.1/print.css"}
{"warc-target-uri": "https://www.iana.org/_img/2015.1/fonts/NotoSans-Bold.woff"}
{"warc-target-uri": "https://www.iana.org/_img/2015.1/fonts/NotoSans-Bold.woff"}
{"warc-target-uri": "https://www.iana.org/_img/2015.1/fonts/NotoSans-Regular.woff"}
{"warc-target-uri": "https://www.iana.org/_img/2015.1/fonts/NotoSans-Regular.woff"}
{"warc-target-uri": "https://www.iana.org/_img/2015.1/fonts/SourceCodePro-Regular.woff"}
{"warc-target-uri": "https://www.iana.org/_img/2015.1/fonts/SourceCodePro-Regular.woff"}
{"warc-target-uri": "https://www.iana.org/_img/bookmark_icon.ico"}
{"warc-target-uri": "https://www.iana.org/_img/bookmark_icon.ico"}
"""

HTTP2_INDEX = """\
{}
{"warc-target-uri": "https://http2.github.io/"}
{"warc-target-uri": "https://http2.github.io/"}
{"warc-target-uri": "https://http2.github.io/components/bootstrap/dist/css/bootstrap.min.css"}
{"warc-target-uri": "https://http2.github.io/components/bootstrap/dist/css/bootstrap.min.css"}
{"warc-target-uri": "https://http2.github.io/asset/site.css"}
{"warc-target-uri": "https://http2.github.io/asset/site.css"}
"""


@contextmanager
def patch_stdout():
    buff = BytesIO()
    if hasattr(sys.stdout, 'buffer'):
        orig = sys.stdout.buffer
        sys.stdout.buffer = buff
        yield buff
        sys.stdout.buffer = orig
    else:
        orig = sys.stdout
        sys.stdout = buff
        yield buff
        sys.stdout = orig


