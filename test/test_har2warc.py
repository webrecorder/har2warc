from har2warc.har2warc import main
from warcio.cli import main as indexer
from tempfile import NamedTemporaryFile
import os
import sys

from contextlib import contextmanager
from io import BytesIO


class TestHar2WARC(object):
    @classmethod
    def get_test_file(cls, filename):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)

    def test_example_har(self):
        filename = self.get_test_file('example.har')

        with NamedTemporaryFile('wb') as temp:
            main([filename, temp.name])


            with patch_stdout() as buff:
                indexer(['index', temp.name, '-f', 'warc-target-uri'])

                assert buff.getvalue().decode('utf-8') == EXPECTED


EXPECTED = """\
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


