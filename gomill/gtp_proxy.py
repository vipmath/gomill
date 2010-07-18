"""Support for implementing proxy GTP engines.

That is, engines which implement some or all of their commands by sending them
on to another engine (the _back end_).

"""

from gomill import gtp_controller
from gomill import gtp_engine
from gomill.gtp_controller import (
    GtpProtocolError, GtpTransportError, GtpEngineError)
from gomill.gtp_engine import GtpError, GtpQuit, GtpFatalError


class BackEndError(StandardError):
    """Difficulty communicating with the back end."""

class Gtp_proxy(object):
    """Manager for a GTP proxy engine.

    Public attributes:
      engine     -- Gtp_engine_protocol
      controller -- Gtp_controller_protocol
      channel_id -- string

    The 'engine' attribute is the proxy engine. Initially it supports all the
    commands reported by the back end's 'list_commands'. You can add commands to
    it in the usual way; new commands will override any commands with the same
    names in the back end.

    The proxy engine also supports the following commands:
      gomill-passthrough <command> [args] ...
        Run a command on the back end (use this to get at overridden commands,
        or commands which don't appear in list_commands)

    If the proxy subprocess exits, this will be reported (as a transport error)
    when the next command is sent. If you're using handle_command, it will
    apropriately turn this into a fatal error.

    Sample use:
      proxy = gtp_proxy.Gtp_proxy()
      proxy.set_back_end_subprocess([<command>, <arg>, ...])
      proxy.engine.add_command(...)
      proxy.run()

    The default 'quit' handler passes 'quit' on the back end and raises
    GtpQuit.

    If you add handlers which are expected to cause the back end to exit
    (eg, by sending it 'quit'), you should have them raise GtpQuit.

    """
    def __init__(self):
        self.controller = None
        self.channel_id = None
        self.engine = None

    def _back_end_is_set(self):
        return self.controller is not None

    def _make_back_end_handlers(self):
        result = {}
        for command in self.back_end_commands:
            def handler(args, _command=command):
                return self.handle_command(_command, args)
            result[command] = handler
        return result

    def _make_engine(self):
        self.engine = gtp_engine.Gtp_engine_protocol()
        self.engine.add_commands(self._make_back_end_handlers())
        self.engine.add_protocol_commands()
        self.engine.add_commands({
            'quit'               : self.handle_quit,
            'gomill-passthrough' : self.handle_passthrough,
            })

    def set_back_end_controller(self, channel_id, controller):
        """Specify the back end using a Gtp_controller_protocol.

        channel_id -- string
        controller -- Gtp_controller_protocol

        Raises BackEndError if it can't communicate with the back end.

        """
        if self._back_end_is_set():
            raise StandardError("back end already set")
        try:
            response = controller.do_command(channel_id, 'list_commands')
        except GtpEngineError, e:
            raise BackEndError("list_commands failed on back end\n%s" % e)
        except GtpProtocolError, e:
            raise BackEndError("back end command isn't speaking GTP\n%s" % e)
        except GtpTransportError, e:
            raise BackEndError(
                "can't communicate with back end command:\n%s" % e)
        self.channel_id = channel_id
        self.controller = controller
        self.back_end_commands = [s for s in
                                  (t.strip() for t in response.split("\n"))
                                  if s]
        self._make_engine()

    def set_back_end_subprocess(self, command):
        """Specify the back end as a subprocess.

        command -- list of strings (as for subprocess.Popen)

        Raises BackEndError if it can't communicate with the back end.

        """
        try:
            channel = gtp_controller.Subprocess_gtp_channel(command)
        except GtpTransportError, e:
            # Probably means exec failure
            raise BackEndError("can't launch back end command\n%s" % e)
        controller = gtp_controller.Gtp_controller_protocol()
        controller.add_channel("back-end", channel)
        self.set_back_end_controller('back-end', controller)

    def close(self):
        """Close the channel to the back end.

        Transport errors are reported by raising BackEndError.

        There's no great need to call this if you're going to exit from the
        parent process anyway.

        """
        try:
            self.controller.close_channel(self.channel_id)
        except GtpTransportError:
            raise BackEndError("error closing channel to back end:\n%s" % e)

    def run(self):
        """Run a GTP session on stdin and stdout, using the proxy engine.

        This is provided for convenience; it's also ok to use the proxy engine
        directly.

        Returns either when EOF is seen on stdin, or when a handler (such as the
        default 'quit' handler) raises GtpQuit. It doesn't wait for the back end
        to exit.

        Closes the channel to the back end before it returns.

        """
        gtp_engine.run_interactive_gtp_session(self.engine)
        self.close()

    def pass_command(self, command, args):
        """Pass a command to the back end, and return its response.

        The response (or error response) is unchanged, except for whitespace
        normalisation.

        This passes the command to the back end even if it isn't included in the
        back end's list_commands output; the back end will presumably return an
        'unknown command' error.

        Error responses from the back end are reported by raising
        GtpEngineError.

        Transport or protocol errors are reported by raising BackEndError.

        """
        if not self._back_end_is_set():
            raise StandardError("back end isn't set")
        try:
            return self.controller.do_command(self.channel_id, command, *args)
        except GtpProtocolError, e:
            raise BackEndError(
                "protocol error communicating with back end:\n%s" % e)
        except GtpTransportError, e:
            raise BackEndError("error communicating with back end:\n%s" % e)

    def handle_command(self, command, args):
        """Run a command on the back end, from inside a GTP handler.

        This is a variant of pass_command, intended to be used directly in a
        command handler.

        Error responses from the back end are reported by raising GtpError.

        Transport or protocol errors are reported by raising GtpFatalError.

        """
        try:
            return self.pass_command(command, args)
        except GtpEngineError, e:
            raise GtpError(str(e))
        except BackEndError, e:
            raise GtpFatalError(str(e))

    def back_end_has_command(self, command):
        """Say whether the back end supports the specified command.

        This uses known_command, not list_commands. It caches the results.

        Transport or protocol errors are reported by raising BackEndError.

        """
        if not self._back_end_is_set():
            raise StandardError("back end isn't set")
        try:
            return self.controller.known_command(self.channel_id, command)
        except GtpProtocolError, e:
            raise BackEndError(
                "protocol error communicating with back end:\n%s" % e)
        except GtpTransportError, e:
            raise BackEndError("error communicating with back end:\n%s" % e)

    def handle_quit(self, args):
        result = self.handle_command("quit", [])
        raise GtpQuit(result)

    def handle_passthrough(self, args):
        try:
            command = args[0]
        except IndexError:
            gtp_engine.report_bad_arguments()
        return self.handle_command(command, args[1:])