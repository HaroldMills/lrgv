import unittest


SHOW_EXCEPTION_MESSAGES = False


class TestCase(unittest.TestCase):
    
    
    def assert_raises(self, exception_class, function, *args, **kwargs):
        
        try:
            function(*args, **kwargs)

        except exception_class as e:
            if SHOW_EXCEPTION_MESSAGES:
                print(str(e))
                
        else:
            raise AssertionError(
                f'{exception_class.__name__} not raised by '
                f'{function.__name__}')
