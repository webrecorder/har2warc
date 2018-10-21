har2warc
========

Convert HTTP Archive (HAR) -> Web Archive (WARC) format

``pip install har2warc``


Command-Line Usage
~~~~~~~~~~~~~~~~~~

``har2warc <input.har> <output.warc.gz>``


Libary Usage
~~~~~~~~~~~~

har2warc can be used as a python library.

Simple usage similar to CLI interface:

.. code:: python

   from har2warc.har2warc import har2warc

   har2warc('input.har', 'output.warc.gz')


Also supports reading and writing from buffers:

.. code:: python

   from har2warc.har2warc import har2warc

   har = json.loads(...)

   with open('output.warc.gz', 'w+b') as warc:
        har2warc(har, warc)

        # READ WARC
        warc.seek(0)
        warc.read()


