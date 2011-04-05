"""
    Script for setting up google app accounts with webfaction.com
"""

__author__ = "Robert Parris"
__credits__ = ["seanf", "digitalxero", "http://forum.webfaction.com/viewtopic.php?pid=9647"]
__license__ = "MIT"
__version__ = "1.0.0"

import sys
import xmlrpclib
from optparse import OptionParser

# Hardcode webfaction credentials here, if wanted.
WEBFACTION_USERNAME = ''
WEBFACTION_PASSWORD = ''


def create_mx_records(server, session_id, domain, mx_info, quiet):
    for mx in mx_info:
        server_resp = server.create_dns_override(session_id, domain, '', '', mx[0], mx[1], '')
        if not quiet:
            print(server_resp)
            print('Created MX record: %s domain: %s priority: %s ' % (mx[0], domain, mx[1]))


def create_subdomain(server, session_id, domain, subdomain, quiet):
    server_resp = server.create_domain(session_id, domain, subdomain)
    if not quiet:
        print(server_resp)
        print('created subdomain %s on %s' % (subdomain, domain))


def create_cname_record(server, session_id, domain, subdomain, cname_target, quiet):
    server_resp = server.create_dns_override(session_id, subdomain + '.' + domain, '', cname_target, '', '', '')
    if not quiet:
        print(server_resp)
        print('created cname record %s.%s -> %s' % (subdomain, domain, cname_target))


def get_webfaction_credentials(opts_un='', opts_pw='', force_input=False):
    if force_input:
        return raw_input('Webfaction Username: '), raw_input('Webfaction Password: ')
    if opts_un:
        un = opts_un
    elif WEBFACTION_USERNAME is not '':
        un = WEBFACTION_USERNAME
    else:
        un = raw_input('Webfaction Username: ')
    if opts_pw:
        pw = opts_pw
    elif WEBFACTION_PASSWORD is not '':
        pw = WEBFACTION_PASSWORD
    else:
        pw = raw_input('Webfaction Password: ')
    return un, pw


def get_domain(opts_domain):
    return opts_domain if opts_domain else raw_input('Please enter your domain name (no www, etc): ')


def get_mail_subdomain(opts_mail):
    return opts_mail if opts_mail else raw_input('Please enter the mail subdomain (e.g. mail): ')


def get_cal_subdomain(opts_cal):
    return opts_cal if opts_cal else raw_input('Please enter the calendar subdomain (e.g. calendar): ')


def get_docs_subdomain(opts_docs):
    return opts_docs if opts_docs else raw_input('Please enter the documents subdomain (e.g. docs): ')


def login_webfaction(server, username, password, quiet, attempt=0):
    if not quiet:
        print('Logging into webfaction as user %s' % (username))
    try:
        return server.login(username, password)
    except xmlrpclib.Fault, err:
        if not quiet:
            print "Fault code: %d" % err.faultCode
        print "%s" % err.faultString
        if attempt < 3:
            username, password = get_webfaction_credentials(force_input=True)
            login_webfaction(server, username, password, quiet, attempt=attempt + 1)
        else:
            sys.exit('Too many failed attempts')


def main():
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option('-u', '--username', dest='username', help='webfaction username', default=WEBFACTION_USERNAME)
    parser.add_option('-p', '--password', dest='password', help='webfaction password', default=WEBFACTION_PASSWORD)
    parser.add_option('-D', '--domain', dest='domain', help='domain name attached to google apps (no www, etc)')
    parser.add_option('-m', '--mail', dest='mail', help='mail subdomain (e.g. webmail)')
    parser.add_option('-c', '--calendar', dest='cal', help='calendar subdomain (e.g. calendar)')
    parser.add_option('-d', '--documents', dest='docs', help='documents subdomain (e.g. docs)')
    parser.add_option('-q', '--quiet', dest='quiet', action='store_true')
    (opts, args) = parser.parse_args()

    server = xmlrpclib.Server('https://api.webfaction.com/')
    mx_info = (
                ('ASPMX.L.GOOGLE.COM', '10'),
                ('ALT1.ASPMX.L.GOOGLE.COM', '20'),
                ('ALT2.ASPMX.L.GOOGLE.COM', '20'),
                ('ASPMX2.GOOGLEMAIL.COM', '30'),
                ('ASPMX3.GOOGLEMAIL.COM', '30'),
                ('ASPMX4.GOOGLEMAIL.COM', '30'),
                ('ASPMX5.GOOGLEMAIL.COM', '30'),
              )

    username, password = get_webfaction_credentials(opts.username, opts.password)
    session_id, account = login_webfaction(server, username, password, opts.quiet)

    domain = get_domain(opts.domain)
    mail_subdomain = get_mail_subdomain(opts.mail)
    cal_subdomain = get_cal_subdomain(opts.cal)
    docs_subdomain = get_docs_subdomain(opts.docs)

    create_mx_records(server, session_id, domain, mx_info, opts.quiet)

    for subdomain in [mail_subdomain, cal_subdomain, docs_subdomain]:
        if subdomain:
            create_subdomain(server, session_id, domain, subdomain, opts.quiet)
            create_cname_record(server, session_id, domain, subdomain, 'ghs.google.com', opts.quiet)

if __name__ == '__main__':
    sys.exit(main())
