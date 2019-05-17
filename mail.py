from mailer import Mailer, Message
from log import log
from settings import EMAIL

def send_email(name, email, mess):
    """ Send new password to user
    """

    mail = Mailer(host=EMAIL['host'],
                  port=EMAIL['port'],
                  use_tls=EMAIL['use_tls'],
                  usr=EMAIL['user'],
                  pwd=EMAIL['password']
                  )

    message = Message(From='help@rxmedaccess.com',
                      To=['oyefesobi.paul@gmail.com'],
                      Subject="message from {}".format(email)
                      )

    message.Body = """{} sent you the following message:
                      {}
                   """.format(name, email, mess)
    try:
        mail.send(message)
    except Exception as e:
        log.error('Send mail error: {}'.format(str(e)))
