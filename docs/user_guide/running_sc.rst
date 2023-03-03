
Running SiliconCompiler
------------------------------

You can either `run remotely`_ in the cloud, or `run locally`_ on your machine.

.. _run remotely:

Cloud Access (Public)
^^^^^^^^^^^^^^^^^^^^^

By default, SiliconCompiler will send remote jobs to our public beta servers, after printing a brief reminder that the job is being uploaded to a public server. You can run a quick self-test to verify that SiliconCompiler was installed successfully::

    sc -target asic_demo -remote

You do not need to configure anything to use the :keypath:`option, remote` flag with these public servers, but you can use the ``sc-configure`` command to specify where SiliconCompiler should send remote jobs::

    sc-configure https://server.siliconcompiler.com

Cloud Access (Private)
^^^^^^^^^^^^^^^^^^^^^^

SiliconCompiler also supports private servers which require authentication to access. If you have such a server to connect to, you will need a credentials text file located at ~/.sc/credentials on Linux or macOS, or at C:\\Users\\USERNAME\\.sc\\credentials on Windows. The credentials file is a JSON formatted file containing information about the remote server address, username, and password.

.. code-block:: json

   {
   "address": "your-server",
   "username": "your-username",
   "password": "your-key"
   }

Use a text editor to create the credentials file. Alternatively you can use :ref:`sc-configure` app to generate it from the command line.

.. code-block:: console

  (venv) sc-configure
  Remote server address: your-server
  Remote username: your-username
  Remote password: your-key
  Remote configuration saved to: /home/<USER>/.sc/credentials

To verify that your credentials file and server is configured correctly, run the :ref:`sc-ping` command.

.. code-block:: console

  (venv) sc-ping
  User myname validated successfully!
  Remaining compute time: 1440.00 minutes
  Remaining results bandwidth: 5242880 KiB

Once you have verified that your remote configuration works, try compiling a simple design:

.. code-block:: bash

   (venv) sc -target asic_demo -remote

For more information, see :ref:`Remote Processing`.

.. _run locally:

Run Locally
^^^^^^^^^^^

If you wish to run locally, you will need to install some external tool dependencies to start. Take a look at :ref:`External Tools` for a list of tools which you may want to have.

.. note::

   The minimum set of tools required for an ASIC flow are: Surelog, Yosys, OpenRoad and KLayout.

Once you have these tools installed, try compiling a simple design:

.. code-block:: bash

    (venv) cd $SCPATH/../examples/heartbeat
    (venv) sc heartbeat.v heartbeat.sdc

See the :ref:`Quickstart guide <quickstart guide>` section to get more details on what you're running.


View Design
^^^^^^^^^^^

To view IC layout files (DEF, GDSII) we recommend installing the open source multi-platform 'klayout' viewer (available for Windows, Linux, and macOS). Installation instructions for klayout can be found in the :ref:`tools directory <klayout>`.

To test the klayout installation, run the :ref:`sc-show` to display the 'heartbeat' layout:

.. code-block:: bash

   (venv) sc-show -design heartbeat
