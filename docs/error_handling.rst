Error Handling
=========================

Error Handling During Startup
---------------------------------

If any child fixtures raise an error during startup, the following occurs:

#. All fixtures that have not yet been started (due to :ref:`abstract:Internal Child Dependencies`) are cancelled.
#. All fixtures whose startup has already started are allowed to continue their startup, if their startup raises an
   error, that error is added to the list of errors raised.
#. All fixtures whose startup has completed without errors are then torn down. If a tear down raises an error, that
   error is added to the list of errors raised.
#. An error is raised with the list of errors raised, failing whatever test called the parent fixture.

Error Handling During Teardown
---------------------------------

If any child fixtures raise an error during teardown, all the other teardowns are still run, and the error or errors are
re-raised, failing the teardown of whatever test called the parent fixture.