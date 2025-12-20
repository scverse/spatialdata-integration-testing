import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--message", type=str)
parser.add_argument("--token", type=str)
parser.add_argument("--user", type=str)
args = parser.parse_args()

json_url = "https://api.pushover.net/1/messages.json"
my_data = {
    "token": args.token,
    "user": args.user,
    "message": args.message,
}
requests.post(json_url, data=my_data)
