from gomill import gtp_engine
from gomill import gtp_controller
from gomill import gtp_proxy

def handle_mygenmove(proxy, args):
    return proxy.pass_command('genmove', args)

def handle_mytest(args):
    return "mytest: %s" % ",".join(args)

def main():
    channel = gtp_controller.Subprocess_gtp_channel(
        "./player -m kiai.simple_montecarlo_player".split())
    controller = gtp_controller.Gtp_controller_protocol()
    controller.add_channel("sub", channel)

    proxy = gtp_proxy.Gtp_proxy('sub', controller)
    proxy.add_command('mygenmove', handle_mygenmove)
    proxy.engine.add_command("mytest", handle_mytest)

    is_error, response, end_session = proxy.engine.run_command("showboard", [])
    assert not is_error
    assert not end_session
    print response

    gtp_engine.run_interactive_gtp_session(proxy.engine)


if __name__ == "__main__":
    main()

