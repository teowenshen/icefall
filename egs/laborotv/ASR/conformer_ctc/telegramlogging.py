import requests
import logging, logging.handlers

def escape_html(text : str):
    """
    Escapes all html characters in text
    :param str text:
    :rtype: str
    """
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

class TelegramStreamIO(logging.Handler):

    API_ENDPOINT = 'https://api.telegram.org'
    MAX_MESSAGE_LEN = 4096
    formatter = logging.Formatter('%(asctime)s - %(levelname)s at %(funcName)s (line %(lineno)s):\n\n%(message)s')

    def __init__(self):
        super(TelegramStreamIO, self).__init__()
        token = '2033198046:AAG-k77HX1XJzcm33DHWE8G6g4hdxvV6fCc'
        self.chat_id = '1976736656'
        self.url = f'{self.API_ENDPOINT}/bot{token}/sendMessage'

    
    def emit(self, record : logging.LogRecord):
        """
        Emit a record.

        Send the record to the Web server as a percent-encoded dictionary
        """
        data = {
            'chat_id': self.chat_id,
            'text': self.format(self.mapLogRecord(record)),
            'parse_mode': 'HTML'
        }
        try:
            requests.get(self.url, json=data)
            #return response.json()
        except:
            print("LOL TelegramStreamIO failed to send message")
            pass



    def mapLogRecord(self, record):
        """
        Default implementation of mapping the log record into a dict
        that is sent as the CGI data. Overwrite in your class.
        Contributed by Franz Glasner.
        """

        for k, v in record.__dict__.items():
            if isinstance(v, str):
                setattr(record, k, escape_html(v))
        return record

def setup_logger(minimum : int = logging.DEBUG, tg_level : int = logging.INFO):

    assert tg_level >= minimum
    logger = logging.getLogger()
    logger.setLevel(minimum)

    stdout = logging.StreamHandler()
    stdout.setLevel(minimum)
    formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
    stdout.setFormatter(formatter)
    logger.addHandler(stdout)

    tg = TelegramStreamIO()
    formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s:\n %(message)s')
    tg.setFormatter(formatter)
    tg.setLevel(tg_level)
    logger.addHandler(tg)


def main():
    logging.info('30% &')


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s at %(funcName)s (line %(lineno)s) - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    tg = TelegramStreamIO()
    tg.setLevel(logging.INFO)
    tg.setFormatter(formatter)
    logger.addHandler(tg)
    
    main()