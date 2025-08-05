from argparse import ArgumentParser
from datetime import date as Date, timedelta as TimeDelta

from lrgv.util.test_case import TestCase
import lrgv.util.arg_utils as arg_utils


ONE_DAY = TimeDelta(days=1)


class ArgUtilsTests(TestCase):


    def test_no_date_args(self):

        self._test_parse_args((

            # no date arguments
            ((), (None, None, None), (None, None)),

        ))


    def _test_parse_args(self, cases):

        for args, expected_args, expected_dates in cases:

            args = parse_args(args)

            arg_tuple = (args.date, args.start_date, args.end_date)
            expected_args = tuple(create_date(d) for d in expected_args)
            self.assertEqual(arg_tuple, expected_args)

            dates = arg_utils.get_start_and_end_dates(args)
            expected_dates = tuple(create_date(d) for d in expected_dates)
            self.assertEqual(dates, expected_dates)


    def test_date_arg(self):

        self._test_parse_args((

            # date argument only
            (('--date', '2025-03-17'),
             ('2025-03-17', None, None),
             ('2025-03-17', '2025-03-17')),

        ))


    def test_date_names(self):
        
        today = Date.today()

        cases = (
            ('today', today),
            ('yesterday', today - ONE_DAY),
            ('tomorrow', today + ONE_DAY),
        )

        for date_name, expected_date in cases:

            expected_date = expected_date.isoformat()

            self._test_parse_args((
                (('--date', date_name),
                 (expected_date, None, None),
                 (expected_date, expected_date)),
            ))


    def test_start_and_end_dates(self):

        self._test_parse_args((

            # start date only
            (('--start-date', '2025-03-16'),
             (None, '2025-03-16', None),
             ('2025-03-16', None)),

            # end date only
            (('--end-date', '2025-03-18'),
             (None, None, '2025-03-18'),
             (None, '2025-03-18')),

            # start and end dates
            (('--start-date', '2025-03-16', '--end-date', '2025-03-18'),
             (None, '2025-03-16', '2025-03-18'),
             ('2025-03-16', '2025-03-18')),

        ))


    def test_date_mixture_errors(self):

        self._test_parse_args_errors((

            # date and start date arguments
            ('--date', '2025-03-17', '--start-date', '2025-03-16'),

            # date and end date arguments
            ('--date', '2025-03-17', '--end-date', '2025-03-18'),

            # all date arguments
            ('--date', '2025-03-17', '--start-date', '2025-03-16',
              '--end-date', '2025-03-18'),

        ))

    
    def _test_parse_args_errors(self, cases):
        for args in cases:
            args = parse_args(args)
            self.assert_raises(
                ValueError, arg_utils.get_start_and_end_dates, args)


def parse_args(args):
    parser = ArgumentParser(description='Test arg_utils.', exit_on_error=False)
    arg_utils.add_date_args(parser)
    return parser.parse_args(args)


def create_date(d):
    if d is None:
        return None
    else:
        return Date.fromisoformat(d)
