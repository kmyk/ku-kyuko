#!/usr/bin/python2
# -*- coding: utf-8 -*-

import logging
import mechanize # fails on python3
import re
import datetime
import smtplib
import email
import email.mime.text
import os
import sys

debug_not_use_mobile = False

def load_kyuko(user, password):
    logging.debug('begin scraping')
    br = mechanize.Browser()
    br.set_handle_robots(False)

    if debug_not_use_mobile:
        br.open('https://kym.kobe-u.ac.jp/kobe-u/campus')
    else:
        br.open('https://mob-kym.kobe-u.ac.jp/kobe-m/campus')
    br.select_form(name='form')
    br['usernm'] = user
    br['passwd'] = password
    br.submit()

    if debug_not_use_mobile:
        br.open('https://kym.kobe-u.ac.jp/kobe-u/campus?view=view.menu&func=function.kyukohoko.kyukohoko.refer')
    else:
        br.follow_link(url_regex='func=function\.keitai\.kyukohoko\.refer')

    return br.response().get_data().decode('shift_jis')

def parse_kyuko(html):
    logging.debug('begin parsing')
    data = html.split('<hr>')[1]
    data = re.compile('</?a[^>]*>').sub(' ', data)
    data = re.compile('&nbsp;').sub(' ', data)
    data = re.compile('\s+').sub(' ', data)
    data = data.split('<br>')
    result = []
    state = None
    for elem in data:
        elem = elem.strip()
        if elem.startswith('[') and elem.endswith(']'):
            state = elem
        elif state is None or elem == '':
            pass
        elif elem.endswith(u'はありません'):
            pass
        else:
            result.append({ 'type' : state.encode('utf-8'), 'info' : elem.encode('utf-8') })
    logging.info('{} event found'.format(len(result)))
    return result

def format_and_cache_kyuko(data, cache):
    logging.debug('begin formating')
    if os.path.exists(cache):
        cached = list(open(cache).readlines())
        cached = map(lambda x : x.strip(), cached)
    else:
        cached = []
    draft = []
    for event in data:
        event = '{type} {info}'.format(**event)
        if cached.count(event) == 0:
            draft.append(event)
    with open(cache, 'a') as fh:
        fh.write('\n'.join(draft))
        fh.write('\n')
    logging.info('{} new event found'.format(len(draft)))
    return draft

def email_addr_of(user):
    return '{}@stu.kobe-u.ac.jp'.format(user)

def send_kyuko(data, user, dests, password):
    if len(data) == 0:
        logging.info('nothing to email')
        return
    logging.debug('begin sending')
    addr = email_addr_of(user)
    msg = email.mime.text.MIMEText('\n'.join(data), 'plain', 'utf-8')
    msg['Subject'] = '休補講情報 at {}'.format(datetime.datetime.today().strftime('%m/%d %H:%M'))
    msg['From'] = addr
    msg['Date'] = email.Utils.formatdate()
    smtp = smtplib.SMTP_SSL('smtp.kobe-u.ac.jp', 465)
    smtp.ehlo()
    smtp.login(addr, password)
    for dest in dests:
        msg['To'] = dest
        smtp.sendmail(addr, [dest], msg.as_string())
    smtp.quit()
    logging.info('email sent to {}'.format(addr))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user')
    parser.add_argument('-p', '--password')
    parser.add_argument('--cache', default=os.path.expanduser('~/.ku-kyuko/cache'))
    parser.add_argument('--log', default=os.path.expanduser('~/.ku-kyuko/log'))
    parser.add_argument('--dests', default=os.path.expanduser('~/.ku-kyuko/dests'))
    parser.add_argument('--debug-not-use-mobile', action='store_true')
    parser.add_argument('--debug-only-print', action='store_true')
    args = parser.parse_args()
    if args.user is None:
        if not sys.stdin.isatty():
            parser.error('USER is not given')
        args.user = input('user: ')
    if args.password is None:
        if not sys.stdin.isatty():
            parser.error('PASSWORD is not given')
        import getpass
        args.password = getpass.getpass('password: ')
    for f in [args.cache, args.log]:
        dirname = os.path.dirname(os.path.abspath(f))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    if os.path.exists(args.dests):
        args.dests = list(filter(lambda x: x, map(lambda x: x.strip(), open(args.dests).readlines())))
    else:
        args.dests = [email_addr_of(args.user)]

    logging.basicConfig(filename=args.log, level=logging.DEBUG)

    logging.debug('begin program')
    try:
        debug_not_use_mobile = args.debug_not_use_mobile
        kyuko = load_kyuko(args.user, args.password)
        if args.debug_only_print:
            print kyuko
        else:
            kyuko = parse_kyuko(kyuko)
            kyuko = format_and_cache_kyuko(kyuko, cache=args.cache)
            send_kyuko(kyuko, user=args.user, dests=args.dests, password=args.password)
    except:
        logging.exception('')
        sys.exit(1)
    logging.debug('end program')
