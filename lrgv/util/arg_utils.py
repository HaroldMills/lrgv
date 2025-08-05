from datetime import date as Date, timedelta as TimeDelta


_ONE_DAY = TimeDelta(days=1)


def add_date_args(
        
    parser,
    date_arg_name='--date',
    date_arg_help='Date to process.',
    start_date_arg_name='--start-date',
    start_date_arg_help=(
        'Start date of range of dates to process. '
        'This argument is mutually exclusive with the --date argument.'),
    end_date_arg_name='--end-date',
    end_date_arg_help=(
        'End date of range of dates to process. '
        'This argument is mutually exclusive with the --date argument.')

):

    # We are careful to call `Date.today` exactly once in this function
    # to be certain that the same `today` date is used for all arguments.

    today = Date.today()

    def parse_date(date):
        return _parse_date(date, today)
    
    def add_arg(name, help):
        parser.add_argument(name, type=parse_date, help=help)
    
    add_arg(date_arg_name, date_arg_help)
    add_arg(start_date_arg_name, start_date_arg_help)
    add_arg(end_date_arg_name, end_date_arg_help)


def _parse_date(date, today):

    if date == 'today':
        return today
    
    elif date == 'yesterday':
        return today - _ONE_DAY

    elif date == 'tomorrow':
        return today + _ONE_DAY

    try:
        return Date.fromisoformat(date)
    except ValueError as e:
        raise ValueError(
            f'Invalid date "{date}". Expected YYYY-MM-DD.') from e


def get_start_and_end_dates(args, default_date='today'):

    date = args.date
    start_date = args.start_date
    end_date = args.end_date

    if date is not None:
        # single date argument specified

        # Check that start date was not also specified.
        if start_date is not None:
            _handle_date_arg_conflict('start')

        # Check that end date was not also specified.
        if end_date is not None:
            _handle_date_arg_conflict('end')

        return date, date

    else:
        # single date argument not specified

        return start_date, end_date


def _handle_date_arg_conflict(arg_name):
    raise ValueError(
        f'The --date and --{arg_name}-date arguments were both specified. '
        f'If the --date argument is specified, the --start-date and '
        f'--end-date arguments must not be specified.')