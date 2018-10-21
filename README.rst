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

Use the CLI interface:

.. code:: python
   
   from har2warc.har2warc import main
   main(['input.har', 'output.warc.gz'])
   

Using the parser directly:

.. code:: python

   from har2warc import har2warc

   har2warc('input.har', 'output.warc.gz')

   
   
 


