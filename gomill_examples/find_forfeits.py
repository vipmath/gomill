"""Find forfeited games in tournament results.

This demonstrates retrieving and processing results from a playoff or
all-play-all tournament.

"""

import sys
from optparse import OptionParser

from gomill.gomill_common import opponent_of
from gomill.ringmasters import Ringmaster, RingmasterError

def show_result(matchup, result, filename):
    print "%s: %s forfeited game %s" % (
        matchup.name, result.losing_player, filename)

def find_forfeits(ringmaster):
    if ringmaster.competition_type not in ('playoff', 'allplayall'):
        raise RingmasterError("not a tournament")
    if not ringmaster.status_file_exists():
        raise RingmasterError("no status file")
    ringmaster.load_status()
    playoff = ringmaster.competition
    matchup_ids = playoff.get_matchup_ids()
    for matchup_id in matchup_ids:
        matchup = playoff.get_matchup(matchup_id)
        results = playoff.get_matchup_results(matchup_id)
        for result in results:
            if result.is_forfeit:
                filename = ringmaster.get_sgf_filename(result.game_id)
                show_result(matchup, result, filename)


_description = """\
Read results of a tournament and show all forfeited games.
"""

def main(argv):
    parser = OptionParser(usage="%prog <filename.ctl>",
                          description=_description)
    opts, args = parser.parse_args(argv)
    if not args:
        parser.error("not enough arguments")
    if len(args) > 1:
        parser.error("too many arguments")
    ctl_pathname = args[0]
    try:
        ringmaster = Ringmaster(ctl_pathname)
        find_forfeits(ringmaster)
    except RingmasterError, e:
        print >>sys.stderr, "ringmaster:"
        print >>sys.stderr, e
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])

